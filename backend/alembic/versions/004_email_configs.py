"""Fase: configuração de e-mail por monitor.

Revision ID: 004_email_configs
Revises: 003_auth
Create Date: 2026-08-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_email_configs"
down_revision: str | None = "003_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "email_notification_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("monitor_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("emails", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("failure_threshold", sa.Integer(), nullable=False, server_default="3"),
        sa.Column(
            "down_subject",
            sa.String(length=255),
            nullable=False,
            server_default="[FORA DO AR] {monitor_name}",
        ),
        sa.Column(
            "down_body",
            sa.Text(),
            nullable=False,
            server_default=(
                "O monitor {monitor_name} está fora do ar.\n\n"
                "URL: {url}\nErro: {error}\nFalhas consecutivas: {failure_count}\n"
                "Dashboard: {dashboard_url}"
            ),
        ),
        sa.Column(
            "recovery_subject",
            sa.String(length=255),
            nullable=False,
            server_default="[RESTABELECIDO] {monitor_name}",
        ),
        sa.Column(
            "recovery_body",
            sa.Text(),
            nullable=False,
            server_default=(
                "O monitor {monitor_name} voltou ao ar.\n\n"
                "URL: {url}\nDuração: {duration}\nDashboard: {dashboard_url}"
            ),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("monitor_id"),
    )


def downgrade() -> None:
    op.drop_table("email_notification_configs")
