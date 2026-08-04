"""Criação inicial das tabelas monitors e checks.

Revision ID: 001_initial
Revises:
Create Date: 2026-08-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "monitors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False, server_default="GET"),
        sa.Column("interval_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="10"),
        sa.Column(
            "expected_status",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default="{200}",
        ),
        sa.Column("expected_body_contains", sa.Text(), nullable=True),
        sa.Column("headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("basic_auth_user", sa.String(length=255), nullable=True),
        sa.Column("basic_auth_pass_encrypted", sa.Text(), nullable=True),
        sa.Column("skip_tls_verify", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("follow_redirects", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("slow_threshold_ms", sa.Integer(), nullable=False, server_default="3000"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "checks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("monitor_id", sa.Integer(), nullable=False),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("result", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checks_monitor_id", "checks", ["monitor_id"], unique=False)
    op.execute(
        "CREATE INDEX ix_checks_monitor_id_checked_at_desc "
        "ON checks (monitor_id, checked_at DESC)"
    )


def downgrade() -> None:
    op.drop_index("ix_checks_monitor_id_checked_at_desc", table_name="checks")
    op.drop_index("ix_checks_monitor_id", table_name="checks")
    op.drop_table("checks")
    op.drop_table("monitors")
