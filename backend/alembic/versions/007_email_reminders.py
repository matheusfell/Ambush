"""Adiciona lembrete por monitor para e-mail.

Revision ID: 007_email_reminders
Revises: 006_check_response_body
Create Date: 2026-08-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007_email_reminders"
down_revision: str | None = "006_check_response_body"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "email_notification_configs",
        sa.Column("reminder_minutes", sa.Integer(), nullable=False, server_default="30"),
    )


def downgrade() -> None:
    op.drop_column("email_notification_configs", "reminder_minutes")
