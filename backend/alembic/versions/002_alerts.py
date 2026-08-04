"""Fase 2: incidentes, notificações e SMTP.

Revision ID: 002_alerts
Revises: 001_initial
Create Date: 2026-08-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_alerts"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "emails",
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.add_column(
        "monitors",
        sa.Column("notification_group_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_monitors_notification_group_id",
        "monitors",
        "notification_groups",
        ["notification_group_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("monitor_id", sa.Integer(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incidents_monitor_id", "incidents", ["monitor_id"], unique=False)
    op.create_index(
        "ix_incidents_monitor_id_status",
        "incidents",
        ["monitor_id", "status"],
        unique=False,
    )

    op.create_table(
        "notification_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("monitor_id", sa.Integer(), nullable=True),
        sa.Column("on_down", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("on_recovery", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("on_degraded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("min_interval_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("reminder_minutes", sa.Integer(), nullable=True),
        sa.Column("quiet_hours_start", sa.Time(), nullable=True),
        sa.Column("quiet_hours_end", sa.Time(), nullable=True),
        sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("monitor_id"),
    )

    op.create_table(
        "smtp_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("password_encrypted", sa.Text(), nullable=True),
        sa.Column("from_email", sa.String(length=255), nullable=False, server_default=""),
        sa.Column(
            "from_name",
            sa.String(length=255),
            nullable=False,
            server_default="AmbushSystem",
        ),
        sa.Column("use_tls", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Regra global padrão + linha SMTP vazia
    op.execute(
        """
        INSERT INTO notification_rules (
            monitor_id, on_down, on_recovery, on_degraded,
            min_interval_minutes, reminder_minutes
        ) VALUES (NULL, true, true, false, 30, NULL)
        """
    )
    op.execute(
        """
        INSERT INTO smtp_settings (host, port, from_email, from_name, use_tls)
        VALUES ('', 587, '', 'AmbushSystem', true)
        """
    )


def downgrade() -> None:
    op.drop_table("smtp_settings")
    op.drop_table("notification_rules")
    op.drop_index("ix_incidents_monitor_id_status", table_name="incidents")
    op.drop_index("ix_incidents_monitor_id", table_name="incidents")
    op.drop_table("incidents")
    op.drop_constraint("fk_monitors_notification_group_id", "monitors", type_="foreignkey")
    op.drop_column("monitors", "notification_group_id")
    op.drop_table("notification_groups")
