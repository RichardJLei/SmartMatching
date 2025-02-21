"""dropped party code constrains2

Revision ID: ba3c95a30c14
Revises: 1edf40cd529c
Create Date: 2025-02-21 18:31:49.249352

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba3c95a30c14'
down_revision: Union[str, None] = '1edf40cd529c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
