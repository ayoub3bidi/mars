"""seed_admin_user

Revision ID: 8a4f2c1d9e03
Revises: 2d1dbfecac61
Create Date: 2026-05-30 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8a4f2c1d9e03"
down_revision: Union[str, Sequence[str], None] = "2d1dbfecac61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO public.user (id, username, email, password, is_admin, disabled, oidc_configs)
        SELECT uuid_generate_v4(), 'admin', 'test@admin.com',
            '$5$rounds=535000$8ws.bvUTex83mhMg$ujSsZgI7F7OrtqVVYynHGH3d23SMuncuUIa4.aJ6kQD',
            true, false, '[]'::jsonb
        WHERE NOT EXISTS (SELECT 1 FROM public.user WHERE email = 'test@admin.com')
    """)


def downgrade() -> None:
    op.execute("DELETE FROM public.user WHERE email = 'test@admin.com'")
