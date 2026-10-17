import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ApprovalDecision, TimesheetStatus, enum_values

if TYPE_CHECKING:
    from app.models.finance import PaymentRecord
    from app.models.time_tracking import ZammadReference
    from app.models.user import User


class TimesheetPeriod(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "timesheet_periods"
    __table_args__ = (
        CheckConstraint("period_end >= period_start", name="ck_timesheet_period_dates"),
        UniqueConstraint("user_id", "period_start", "period_end", name="uq_user_timesheet_period"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    status: Mapped[TimesheetStatus] = mapped_column(
        Enum(
            TimesheetStatus,
            name="timesheet_status",
            native_enum=False,
            length=30,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=TimesheetStatus.DRAFT,
        index=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(
        back_populates="timesheet_periods", foreign_keys=[user_id]
    )
    approval_records: Mapped[list["ApprovalRecord"]] = relationship(
        back_populates="timesheet_period", cascade="all, delete-orphan"
    )
    zammad_references: Mapped[list["ZammadReference"]] = relationship(
        back_populates="timesheet_period"
    )
    payment_record: Mapped["PaymentRecord | None"] = relationship(
        back_populates="timesheet_period", uselist=False
    )


class ApprovalRecord(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "approval_records"

    timesheet_period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("timesheet_periods.id", ondelete="CASCADE"), index=True
    )
    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    decision: Mapped[ApprovalDecision] = mapped_column(
        Enum(
            ApprovalDecision,
            name="approval_decision",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=enum_values,
        )
    )
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    timesheet_period: Mapped[TimesheetPeriod] = relationship(back_populates="approval_records")
