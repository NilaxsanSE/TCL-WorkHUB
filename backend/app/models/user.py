import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UserRole, enum_values

if TYPE_CHECKING:
    from app.models.finance import HourlyRate
    from app.models.time_tracking import WorkSession
    from app.models.timesheet import TimesheetPeriod


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    keycloak_subject: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=UserRole.EMPLOYEE,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    work_sessions: Mapped[list["WorkSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    timesheet_periods: Mapped[list["TimesheetPeriod"]] = relationship(
        back_populates="user", foreign_keys="TimesheetPeriod.user_id"
    )
    hourly_rates: Mapped[list["HourlyRate"]] = relationship(
        back_populates="user", foreign_keys="HourlyRate.user_id"
    )
