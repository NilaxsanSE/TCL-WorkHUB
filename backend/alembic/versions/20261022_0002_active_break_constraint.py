"""Allow only one active break per work session.

Revision ID: 20261022_0002
Revises: 20261017_0001
Create Date: 2026-10-22
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20261022_0002"
down_revision: str | None = "20261017_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_active_break_per_session",
        "work_breaks",
        ["work_session_id"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_active_break_per_session", table_name="work_breaks")
