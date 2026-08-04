"""Armazena trecho do body da resposta nas checagens.

Revision ID: 006_check_response_body
Revises: 005_o365_graph_email
Create Date: 2026-08-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_check_response_body"
down_revision: str | None = "005_o365_graph_email"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("checks", sa.Column("response_body_excerpt", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("checks", "response_body_excerpt")
