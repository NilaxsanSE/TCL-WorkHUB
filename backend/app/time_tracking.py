import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth import require_admin, require_employee
from app.db.session import get_db
from app.models.enums import BreakType, WorkSessionStatus
from app.models.time_tracking import WorkBreak, WorkSession
from app.models.user import User

employee_router = APIRouter(prefix="/api/time", tags=["time tracking"])
admin_router = APIRouter(prefix="/api/admin/time", tags=["admin time tracking"])


class CheckInRequest(BaseModel):
    source_timezone: str = Field(default="Asia/Colombo", min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=2000)


class BreakStartRequest(BaseModel):
    break_type: BreakType = BreakType.REST
    notes: str | None = Field(default=None, max_length=2000)


class CheckOutRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class BreakResponse(BaseModel):
    id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None
    break_type: BreakType
    notes: str | None
    duration_seconds: int


class WorkSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_display_name: str
    started_at: datetime
    ended_at: datetime | None
    status: WorkSessionStatus
    source_timezone: str
    notes: str | None
    gross_seconds: int
    break_seconds: int
    worked_seconds: int
    active_break: BreakResponse | None
    breaks: list[BreakResponse]


class TimeStatusResponse(BaseModel):
    state: str
    current_session: WorkSessionResponse | None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def seconds_between(start: datetime, end: datetime) -> int:
    return max(0, int((aware(end) - aware(start)).total_seconds()))


def session_response(session: WorkSession, now: datetime | None = None) -> WorkSessionResponse:
    current_time = now or utc_now()
    session_end = session.ended_at or current_time
    break_responses: list[BreakResponse] = []
    break_seconds = 0
    active_break = None

    for work_break in sorted(session.breaks, key=lambda item: item.started_at):
        break_end = work_break.ended_at or current_time
        duration = seconds_between(work_break.started_at, break_end)
        response = BreakResponse(
            id=work_break.id,
            started_at=work_break.started_at,
            ended_at=work_break.ended_at,
            break_type=work_break.break_type,
            notes=work_break.notes,
            duration_seconds=duration,
        )
        break_responses.append(response)
        break_seconds += duration
        if work_break.ended_at is None:
            active_break = response

    gross_seconds = seconds_between(session.started_at, session_end)
    return WorkSessionResponse(
        id=session.id,
        user_id=session.user_id,
        user_display_name=session.user.display_name,
        started_at=session.started_at,
        ended_at=session.ended_at,
        status=session.status,
        source_timezone=session.source_timezone,
        notes=session.notes,
        gross_seconds=gross_seconds,
        break_seconds=break_seconds,
        worked_seconds=max(0, gross_seconds - break_seconds),
        active_break=active_break,
        breaks=break_responses,
    )


def open_session_query(user_id: uuid.UUID):
    return (
        select(WorkSession)
        .where(
            WorkSession.user_id == user_id,
            WorkSession.status == WorkSessionStatus.OPEN,
        )
        .options(selectinload(WorkSession.breaks), selectinload(WorkSession.user))
    )


def get_open_session(database: Session, user_id: uuid.UUID, *, lock: bool = False):
    statement = open_session_query(user_id).execution_options(populate_existing=True)
    if lock:
        statement = statement.with_for_update()
    return database.scalar(statement)


def require_open_session(database: Session, user_id: uuid.UUID, *, lock: bool = True):
    session = get_open_session(database, user_id, lock=lock)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Check in before performing this action",
        )
    return session


def active_break_for(session: WorkSession) -> WorkBreak | None:
    return next((work_break for work_break in session.breaks if work_break.ended_at is None), None)


def commit_or_conflict(database: Session, detail: str) -> None:
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from error


@employee_router.get("/status", response_model=TimeStatusResponse)
def read_time_status(
    database: Session = Depends(get_db),
    user: User = Depends(require_employee),
) -> TimeStatusResponse:
    session = get_open_session(database, user.id)
    if session is None:
        return TimeStatusResponse(state="checked_out", current_session=None)
    state = "on_break" if active_break_for(session) else "working"
    return TimeStatusResponse(state=state, current_session=session_response(session))


@employee_router.post(
    "/check-in", response_model=WorkSessionResponse, status_code=status.HTTP_201_CREATED
)
def check_in(
    payload: CheckInRequest,
    database: Session = Depends(get_db),
    user: User = Depends(require_employee),
) -> WorkSessionResponse:
    try:
        ZoneInfo(payload.source_timezone)
    except ZoneInfoNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Source timezone is not recognized",
        ) from error

    if get_open_session(database, user.id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An open work session already exists",
        )

    session = WorkSession(
        user_id=user.id,
        started_at=utc_now(),
        status=WorkSessionStatus.OPEN,
        source_timezone=payload.source_timezone,
        notes=payload.notes,
    )
    database.add(session)
    commit_or_conflict(database, "An open work session already exists")
    database.refresh(session)
    session.user = user
    session.breaks = []
    return session_response(session)


@employee_router.post(
    "/breaks/start", response_model=WorkSessionResponse, status_code=status.HTTP_201_CREATED
)
def start_break(
    payload: BreakStartRequest,
    database: Session = Depends(get_db),
    user: User = Depends(require_employee),
) -> WorkSessionResponse:
    session = require_open_session(database, user.id)
    if active_break_for(session) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active break already exists",
        )

    database.add(
        WorkBreak(
            work_session_id=session.id,
            started_at=utc_now(),
            break_type=payload.break_type,
            notes=payload.notes,
        )
    )
    commit_or_conflict(database, "An active break already exists")
    session = require_open_session(database, user.id, lock=False)
    return session_response(session)


@employee_router.post("/breaks/end", response_model=WorkSessionResponse)
def end_break(
    database: Session = Depends(get_db),
    user: User = Depends(require_employee),
) -> WorkSessionResponse:
    session = require_open_session(database, user.id)
    work_break = active_break_for(session)
    if work_break is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There is no active break to end",
        )
    work_break.ended_at = utc_now()
    database.commit()
    session = require_open_session(database, user.id, lock=False)
    return session_response(session)


@employee_router.post("/check-out", response_model=WorkSessionResponse)
def check_out(
    payload: CheckOutRequest,
    database: Session = Depends(get_db),
    user: User = Depends(require_employee),
) -> WorkSessionResponse:
    session = require_open_session(database, user.id)
    if active_break_for(session) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="End the active break before checking out",
        )

    session.ended_at = utc_now()
    session.status = WorkSessionStatus.COMPLETED
    if payload.notes is not None:
        session.notes = payload.notes
    database.commit()
    database.refresh(session)
    session.user = user
    return session_response(session)


@employee_router.get("/sessions", response_model=list[WorkSessionResponse])
def read_own_sessions(
    limit: int = Query(default=30, ge=1, le=100),
    database: Session = Depends(get_db),
    user: User = Depends(require_employee),
) -> list[WorkSessionResponse]:
    sessions = database.scalars(
        select(WorkSession)
        .where(WorkSession.user_id == user.id)
        .options(selectinload(WorkSession.breaks), selectinload(WorkSession.user))
        .order_by(WorkSession.started_at.desc())
        .limit(limit)
    ).all()
    now = utc_now()
    return [session_response(session, now) for session in sessions]


@admin_router.get("/sessions", response_model=list[WorkSessionResponse])
def read_all_sessions(
    user_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    database: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[WorkSessionResponse]:
    statement = select(WorkSession).options(
        selectinload(WorkSession.breaks), selectinload(WorkSession.user)
    )
    if user_id is not None:
        statement = statement.where(WorkSession.user_id == user_id)
    sessions = database.scalars(
        statement.order_by(WorkSession.started_at.desc()).limit(limit)
    ).all()
    now = utc_now()
    return [session_response(session, now) for session in sessions]
