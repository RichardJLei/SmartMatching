"""add matching_units mapping to parsing_results

Revision ID: d9e65d65faef
Revises: 3dce2ced9612
Create Date: 2025-02-18 19:57:40.075988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd9e65d65faef'
down_revision: Union[str, None] = '3dce2ced9612'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('parsing_results', sa.Column('matching_unit_ids', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('parsing_results', 'matching_unit_ids')
    # ### end Alembic commands ###
