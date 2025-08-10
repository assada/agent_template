"""create threads table

Revision ID: 4c750f1a48e6
Revises:
Create Date: 2025-08-10 00:28:27.618485

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4c750f1a48e6"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "thread",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), onupdate=sa.text("now()"), nullable=True
        ),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("meta", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("idle", "busy", "interrupted", "error", name="threadstatus"),
            server_default="idle",
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("threads")
