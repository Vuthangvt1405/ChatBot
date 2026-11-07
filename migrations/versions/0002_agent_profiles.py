"""Agent Studio: saved agent profiles (STORY-01).

Revision ID: 0002_agent_profiles
Revises: 0001_initial
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_agent_profiles"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("name_key", sa.String(length=60), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("model_id", sa.String(length=200), nullable=False),
        sa.Column("enabled_tools", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("thinking_level", sa.String(length=16), nullable=False, server_default="MEDIUM"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # AC7: one name per workspace, ignoring case (name_key is the casefolded name).
    op.create_index(
        "ux_agent_profiles_workspace_name_key",
        "agent_profiles",
        ["workspace_id", "name_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_agent_profiles_workspace_name_key", table_name="agent_profiles")
    op.drop_table("agent_profiles")
