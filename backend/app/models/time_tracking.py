import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ApprovalStatus, BreakType, OffDayType, WorkSessionStatus, enum_values

if TYPE_CHECKING:
    from app.models.timesheet import TimesheetPeriod
    from app.models.user import User


class WorkSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "work_sessions"
    __table_args__ = (
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ck_session_end_after_start"),
        Index(
            "uq_open_session_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
            sqlite_where=text("status = 'open'"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[WorkSessionStatus] = mapped_column(
        Enum(
            WorkSessionStatus,
            name="work_session_status",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=WorkSessionStatus.OPEN,
        index=True,
    )
    source_timezone: Mapped[str] = mapped_column(String(64), default="Asia/Colombo")
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="work_sessions")
    breaks: Mapped[list["WorkBreak"]] = relationship(
        back_populates="work_session", cascade="all, delete-orphan"
    )
    zammad_references: Mapped[list["ZammadReference"]] = relationship(
        back_populates="work_session"
    )


class WorkBreak(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "work_breaks"
    __table_args__ = (
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ck_break_end_after_start"),
        Index(
            "uq_active_break_per_session",
            "work_session_id",
            unique=True,
            postgresql_where=text("ended_at IS NULL"),
            sqlite_where=text("ended_at IS NULL"),
        ),
    )

    work_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("work_sessions.id", ondelete="CASCADE"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    break_type: Mapped[BreakType] = mapped_column(
        Enum(
            BreakType,
            name="break_type",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=BreakType.REST,
    )
    notes: Mapped[str | None] = mapped_column(Text)

    work_session: Mapped[WorkSession] = relationship(back_populates="breaks")


class OffDay(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "off_days"
    __table_args__ = (Index("ix_off_days_user_date", "user_id", "date"),)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)
    off_day_type: Mapped[OffDayType] = mapped_column(
        Enum(
            OffDayType,
            name="off_day_type",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=enum_values,
        )
    )
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(
            ApprovalStatus,
            name="off_day_approval_status",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=ApprovalStatus.PENDING,
    )
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)


class ZammadReference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "zammad_references"
    __table_args__ = (
        CheckConstraint(
            "work_session_id IS NOT NULL OR timesheet_period_id IS NOT NULL",
            name="ck_zammad_reference_has_parent",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    work_session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("work_sessions.id", ondelete="CASCADE"), index=True
    )
    timesheet_period_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("timesheet_periods.id", ondelete="CASCADE"), index=True
    )
    ticket_number: Mapped[str] = mapped_column(String(100), index=True)
    ticket_title: Mapped[str] = mapped_column(String(500))
    ticket_url: Mapped[str] = mapped_column(String(2048))
    work_summary: Mapped[str] = mapped_column(Text)

    work_session: Mapped[WorkSession | None] = relationship(back_populates="zammad_references")
    timesheet_period: Mapped["TimesheetPeriod | None"] = relationship(
        back_populates="zammad_references"
    )
