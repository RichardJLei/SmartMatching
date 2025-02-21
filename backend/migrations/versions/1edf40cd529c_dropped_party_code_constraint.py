"""dropped party code constraint

Revision ID: 1edf40cd529c
Revises: <your_previous_revision>
Create Date: 2024-03-xx

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1edf40cd529c'
down_revision: Union[str, None] = '<your_previous_revision>'  # Replace with your last revision ID
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the unique_party_code constraint
    op.execute('ALTER TABLE party_codes DROP CONSTRAINT IF EXISTS unique_party_code')


def downgrade() -> None:
    # Add back the constraint if needed
    op.create_unique_constraint('unique_party_code', 'party_codes', ['party_code'])
