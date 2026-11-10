"""remove only the unchanged default seeded admin

Revision ID: 4b9d2a7c1e60
Revises: 8a4f2c1d9e03
Create Date: 2026-11-10
"""

from typing import Sequence, Union

from alembic import op

revision: str = "4b9d2a7c1e60"
down_revision: Union[str, Sequence[str], None] = "8a4f2c1d9e03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "DELETE FROM public.user "
        "WHERE email = 'test@admin.com' "
        "AND password = '$5$rounds=535000$8ws.bvUTex83mhMg$ujSsZgI7F7OrtqVVYynHGH3d23SMuncuUIa4.aJ6kQD'"
    )


def downgrade() -> None:
    # Password credentials are intentionally not recreated by a downgrade.
    pass
