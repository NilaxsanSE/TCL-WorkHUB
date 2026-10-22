import uuid

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.auth import get_current_user, require_admin, require_employee
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.time_tracking import admin_router as admin_time_router
from app.time_tracking import employee_router as employee_time_router

app = FastAPI(title=settings.project_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(employee_time_router)
app.include_router(admin_time_router)


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str
    role: UserRole
    active: bool


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "backend",
        "environment": settings.environment,
    }


@app.get("/health/database")
def database_health_check(database: Session = Depends(get_db)) -> dict[str, str]:
    try:
        database.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable",
        ) from error

    return {"status": "ok", "service": "database"}


@app.get("/api/me", response_model=CurrentUserResponse)
def read_current_user(user: User = Depends(get_current_user)) -> User:
    return user


@app.get("/api/employee")
def employee_access(user: User = Depends(require_employee)) -> dict[str, str]:
    return {"message": "Employee access confirmed", "user_id": str(user.id)}


@app.get("/api/admin")
def admin_access(user: User = Depends(require_admin)) -> dict[str, str]:
    return {"message": "Administrator access confirmed", "user_id": str(user.id)}
