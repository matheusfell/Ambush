"""Adiciona suporte a Microsoft Graph para envio de e-mails.

Revision ID: 005_o365_graph_email
Revises: 004_email_configs
Create Date: 2026-08-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_o365_graph_email"
down_revision: str | None = "004_email_configs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "smtp_settings",
        sa.Column(
            "delivery_method",
            sa.String(length=20),
            nullable=False,
            server_default="graph",
        ),
    )
    op.add_column(
        "smtp_settings",
        sa.Column("graph_tenant_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "smtp_settings",
        sa.Column("graph_client_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "smtp_settings",
        sa.Column("graph_client_secret_encrypted", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("smtp_settings", "graph_client_secret_encrypted")
    op.drop_column("smtp_settings", "graph_client_id")
    op.drop_column("smtp_settings", "graph_tenant_id")
    op.drop_column("smtp_settings", "delivery_method")
