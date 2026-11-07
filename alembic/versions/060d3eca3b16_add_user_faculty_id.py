from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '060d3eca3b16'
down_revision: Union[str, None] = 'c7d2a91e4b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'utilizatori',
        sa.Column('facultate_id', sa.Integer(), sa.ForeignKey('facultati.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index(op.f('ix_utilizatori_facultate_id'), 'utilizatori', ['facultate_id'], unique=False)
    op.execute(
        "UPDATE utilizatori SET facultate_id = (SELECT id FROM facultati ORDER BY id ASC LIMIT 1) "
        "WHERE role_id IN (SELECT id FROM roles WHERE name = 'STUDENT') AND facultate_id IS NULL"
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_utilizatori_facultate_id'), table_name='utilizatori')
    op.drop_column('utilizatori', 'facultate_id')
