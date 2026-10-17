"""Create the initial WorkHub schema.

Revision ID: 20261017_0001
Revises:
Create Date: 2026-10-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20261017_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("keycloak_subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=20), server_default="employee", nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint("role IN ('employee', 'admin')", name="user_role"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index(
        "ix_users_keycloak_subject", "users", ["keycloak_subject"], unique=True
    )

    op.create_table(
        "work_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="open", nullable=False),
        sa.Column("source_timezone", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at", name="ck_session_end_after_start"
        ),
        sa.CheckConstraint(
            "status IN ('open', 'completed', 'locked')", name="work_session_status"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_sessions_started_at", "work_sessions", ["started_at"])
    op.create_index("ix_work_sessions_status", "work_sessions", ["status"])
    op.create_index("ix_work_sessions_user_id", "work_sessions", ["user_id"])
    op.create_index(
        "uq_open_session_per_user",
        "work_sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )

    op.create_table(
        "work_breaks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("work_session_id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("break_type", sa.String(length=20), server_default="rest", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at", name="ck_break_end_after_start"
        ),
        sa.CheckConstraint("break_type IN ('meal', 'rest', 'other')", name="break_type"),
        sa.ForeignKeyConstraint(
            ["work_session_id"], ["work_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_breaks_work_session_id", "work_breaks", ["work_session_id"])

    op.create_table(
        "off_days",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("off_day_type", sa.String(length=20), nullable=False),
        sa.Column("approval_status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("approved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint(
            "off_day_type IN ('personal', 'company', 'holiday', 'sick', 'other')",
            name="off_day_type",
        ),
        sa.CheckConstraint(
            "approval_status IN ('pending', 'approved', 'rejected')",
            name="off_day_approval_status",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_off_days_date", "off_days", ["date"])
    op.create_index("ix_off_days_user_date", "off_days", ["user_id", "date"])
    op.create_index("ix_off_days_user_id", "off_days", ["user_id"])

    op.create_table(
        "timesheet_periods",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="draft", nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint("period_end >= period_start", name="ck_timesheet_period_dates"),
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'under_review', 'returned', 'approved', "
            "'rejected', 'payable', 'paid')",
            name="timesheet_status",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "period_start", "period_end", name="uq_user_timesheet_period"
        ),
    )
    op.create_index("ix_timesheet_periods_status", "timesheet_periods", ["status"])
    op.create_index("ix_timesheet_periods_user_id", "timesheet_periods", ["user_id"])

    op.create_table(
        "zammad_references",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("work_session_id", sa.Uuid(), nullable=True),
        sa.Column("timesheet_period_id", sa.Uuid(), nullable=True),
        sa.Column("ticket_number", sa.String(length=100), nullable=False),
        sa.Column("ticket_title", sa.String(length=500), nullable=False),
        sa.Column("ticket_url", sa.String(length=2048), nullable=False),
        sa.Column("work_summary", sa.Text(), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "work_session_id IS NOT NULL OR timesheet_period_id IS NOT NULL",
            name="ck_zammad_reference_has_parent",
        ),
        sa.ForeignKeyConstraint(
            ["timesheet_period_id"], ["timesheet_periods.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["work_session_id"], ["work_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_zammad_references_ticket_number", "zammad_references", ["ticket_number"])
    op.create_index(
        "ix_zammad_references_timesheet_period_id", "zammad_references", ["timesheet_period_id"]
    )
    op.create_index("ix_zammad_references_user_id", "zammad_references", ["user_id"])
    op.create_index(
        "ix_zammad_references_work_session_id", "zammad_references", ["work_session_id"]
    )

    op.create_table(
        "approval_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("timesheet_period_id", sa.Uuid(), nullable=False),
        sa.Column("admin_user_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "decision IN ('approved', 'rejected', 'returned')", name="approval_decision"
        ),
        sa.ForeignKeyConstraint(["admin_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["timesheet_period_id"], ["timesheet_periods.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_records_admin_user_id", "approval_records", ["admin_user_id"])
    op.create_index(
        "ix_approval_records_timesheet_period_id", "approval_records", ["timesheet_period_id"]
    )

    op.create_table(
        "hourly_rates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("rate_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("rate_amount >= 0", name="ck_hourly_rate_non_negative"),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_hourly_rate_dates",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hourly_rates_effective_from", "hourly_rates", ["effective_from"])
    op.create_index("ix_hourly_rates_user_id", "hourly_rates", ["user_id"])

    op.create_table(
        "payment_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("timesheet_period_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("approved_minutes", sa.Integer(), nullable=False),
        sa.Column("rate_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payable_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("marked_paid_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("marked_paid_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint("approved_minutes >= 0", name="ck_payment_minutes_non_negative"),
        sa.CheckConstraint("payable_amount >= 0", name="ck_payment_amount_non_negative"),
        sa.CheckConstraint("rate_amount >= 0", name="ck_payment_rate_non_negative"),
        sa.CheckConstraint(
            "status IN ('pending', 'payable', 'paid', 'cancelled')", name="payment_status"
        ),
        sa.ForeignKeyConstraint(
            ["marked_paid_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["timesheet_period_id"], ["timesheet_periods.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_records_status", "payment_records", ["status"])
    op.create_index(
        "ix_payment_records_timesheet_period_id",
        "payment_records",
        ["timesheet_period_id"],
        unique=True,
    )
    op.create_index("ix_payment_records_user_id", "payment_records", ["user_id"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("payment_record_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_number", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="generated", nullable=False),
        sa.Column("invoice_format", sa.String(length=50), nullable=False),
        sa.Column(
            "generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("generated_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("file_path", sa.String(length=2048), nullable=False),
        sa.CheckConstraint(
            "status IN ('generated', 'issued', 'cancelled')", name="invoice_status"
        ),
        sa.ForeignKeyConstraint(
            ["generated_by_user_id"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["payment_record_id"], ["payment_records.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"], unique=True)
    op.create_index("ix_invoices_payment_record_id", "invoices", ["payment_record_id"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("before_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("invoices")
    op.drop_table("payment_records")
    op.drop_table("hourly_rates")
    op.drop_table("approval_records")
    op.drop_table("zammad_references")
    op.drop_table("timesheet_periods")
    op.drop_table("off_days")
    op.drop_table("work_breaks")
    op.drop_table("work_sessions")
    op.drop_table("users")
