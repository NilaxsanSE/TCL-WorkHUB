import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import InvoiceStatus, PaymentStatus, enum_values

if TYPE_CHECKING:
    from app.models.timesheet import TimesheetPeriod
    from app.models.user import User


class HourlyRate(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "hourly_rates"
    __table_args__ = (
        CheckConstraint("rate_amount >= 0", name="ck_hourly_rate_non_negative"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_hourly_rate_dates",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    rate_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    effective_from: Mapped[date] = mapped_column(Date, index=True)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="hourly_rates", foreign_keys=[user_id])


class PaymentRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payment_records"
    __table_args__ = (
        CheckConstraint("approved_minutes >= 0", name="ck_payment_minutes_non_negative"),
        CheckConstraint("rate_amount >= 0", name="ck_payment_rate_non_negative"),
        CheckConstraint("payable_amount >= 0", name="ck_payment_amount_non_negative"),
    )

    timesheet_period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("timesheet_periods.id", ondelete="RESTRICT"), unique=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    approved_minutes: Mapped[int] = mapped_column(Integer)
    rate_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    payable_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            name="payment_status",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=PaymentStatus.PENDING,
        index=True,
    )
    marked_paid_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    marked_paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    timesheet_period: Mapped["TimesheetPeriod"] = relationship(back_populates="payment_record")
    invoice: Mapped["Invoice | None"] = relationship(
        back_populates="payment_record", uselist=False
    )


class Invoice(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "invoices"

    payment_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_records.id", ondelete="RESTRICT"), unique=True, index=True
    )
    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(
            InvoiceStatus,
            name="invoice_status",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=enum_values,
        ),
        default=InvoiceStatus.GENERATED,
    )
    invoice_format: Mapped[str] = mapped_column(String(50))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    generated_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
    file_path: Mapped[str] = mapped_column(String(2048))

    payment_record: Mapped[PaymentRecord] = relationship(back_populates="invoice")
