"""Add PriceQuote, RefreshLog, Asset.close_units

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "price_quotes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("ts", sa.Date(), nullable=False),
        sa.Column("price", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.UniqueConstraint("kind", "key", "ts", "source"),
    )

    op.create_table(
        "refresh_log",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("scheme_code", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
    )
    op.create_index("ix_refresh_log_scheme_finished", "refresh_log", ["scheme_code", "finished_at"])

    with op.batch_alter_table("assets") as batch_op:
        batch_op.add_column(sa.Column("close_units", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("assets") as batch_op:
        batch_op.drop_column("close_units")
    op.drop_index("ix_refresh_log_scheme_finished", table_name="refresh_log")
    op.drop_table("refresh_log")
    op.drop_table("price_quotes")
