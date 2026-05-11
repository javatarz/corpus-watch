"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "households",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("base_currency", sa.String(), nullable=False, server_default="INR"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "individuals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "household_id",
            sa.String(),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("dob", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "asset_classes",
        sa.Column("code", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
    )

    op.create_table(
        "accounts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "individual_id",
            sa.String(),
            sa.ForeignKey("individuals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asset_class_code",
            sa.String(),
            sa.ForeignKey("asset_classes.code"),
            nullable=False,
        ),
        sa.Column("broker", sa.String(), nullable=False),
        sa.Column("account_number_hash", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "assets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "account_id",
            sa.String(),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scheme_code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("last_value", sa.String(), nullable=True),
        sa.Column("last_value_as_of", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "asset_id",
            sa.String(),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ts", sa.Date(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("units", sa.String(), nullable=True),
        sa.Column("amount", sa.String(), nullable=True),
        sa.Column("identity_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("asset_id", "identity_key"),
    )

    op.bulk_insert(
        sa.table("asset_classes", sa.column("code"), sa.column("name"), sa.column("kind")),
        [{"code": "MF", "name": "Mutual Funds", "kind": "fund"}],
    )


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("assets")
    op.drop_table("accounts")
    op.drop_table("asset_classes")
    op.drop_table("individuals")
    op.drop_table("households")
