"""Initial schema (mirrors app.db.models). For prod use; dev boots via create_all."""

from __future__ import annotations

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass  # schema is created by Base.metadata.create_all on first boot


def downgrade() -> None:
    pass
