from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd8a1f4b2e912'
down_revision: Union[str, None] = '060d3eca3b16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


stare_tehnica_enum = postgresql.ENUM(
    'DISPONIBILA', 'DEFECTA', 'IN_MENTENANTA',
    name='stare_tehnica_enum',
    create_type=False,
)

stare_rezervare_enum = postgresql.ENUM(
    'IN_ASTEPTARE', 'APROBATA', 'ANULATA', 'RESPINSA', 'FINALIZATA',
    name='stare_rezervare_enum',
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        stare_tehnica_enum.create(bind, checkfirst=True)
        stare_rezervare_enum.create(bind, checkfirst=True)

    op.create_table(
        'categorii_resurse',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nume', sa.String(length=100), nullable=False),
        sa.Column('descriere', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_categorii_resurse_nume'), 'categorii_resurse', ['nume'], unique=True)

    op.create_table(
        'resurse',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nume', sa.String(length=255), nullable=False),
        sa.Column('cod_inventar', sa.String(length=50), nullable=False),
        sa.Column('descriere', sa.String(length=500), nullable=True),
        sa.Column('categorie_id', sa.Integer(), sa.ForeignKey('categorii_resurse.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('sala_id', sa.Integer(), sa.ForeignKey('sali.id', ondelete='RESTRICT'), nullable=False),
        sa.Column(
            'stare_tehnica',
            sa.Enum('DISPONIBILA', 'DEFECTA', 'IN_MENTENANTA', name='stare_tehnica_enum'),
            nullable=False,
            server_default='DISPONIBILA',
        ),
        sa.Column('specificatii', sa.String(length=1000), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_resurse_cod_inventar'), 'resurse', ['cod_inventar'], unique=True)
    op.create_index(op.f('ix_resurse_nume'), 'resurse', ['nume'], unique=False)
    op.create_index(op.f('ix_resurse_categorie_id'), 'resurse', ['categorie_id'], unique=False)
    op.create_index(op.f('ix_resurse_sala_id'), 'resurse', ['sala_id'], unique=False)

    op.create_table(
        'rezervari',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('resursa_id', sa.Integer(), sa.ForeignKey('resurse.id', ondelete='CASCADE'), nullable=False),
        sa.Column('utilizator_id', sa.Integer(), sa.ForeignKey('utilizatori.id_utilizator', ondelete='CASCADE'), nullable=False),
        sa.Column('data_inceput', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data_sfarsit', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'stare',
            sa.Enum('IN_ASTEPTARE', 'APROBATA', 'ANULATA', 'RESPINSA', 'FINALIZATA', name='stare_rezervare_enum'),
            nullable=False,
            server_default='IN_ASTEPTARE',
        ),
        sa.Column('scop', sa.String(length=500), nullable=False),
        sa.Column('motiv_respingere', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rezervari_resursa_id'), 'rezervari', ['resursa_id'], unique=False)
    op.create_index(op.f('ix_rezervari_utilizator_id'), 'rezervari', ['utilizator_id'], unique=False)
    op.create_index(op.f('ix_rezervari_data_inceput'), 'rezervari', ['data_inceput'], unique=False)
    op.create_index(op.f('ix_rezervari_data_sfarsit'), 'rezervari', ['data_sfarsit'], unique=False)
    op.create_index(op.f('ix_rezervari_stare'), 'rezervari', ['stare'], unique=False)

    op.create_table(
        'jurnal_tehnic',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('resursa_id', sa.Integer(), sa.ForeignKey('resurse.id', ondelete='CASCADE'), nullable=False),
        sa.Column('utilizator_id', sa.Integer(), sa.ForeignKey('utilizatori.id_utilizator', ondelete='RESTRICT'), nullable=False),
        sa.Column('tip_interventie', sa.String(length=100), nullable=False),
        sa.Column('descriere', sa.String(length=1000), nullable=False),
        sa.Column('stare_anterioara', sa.Enum('DISPONIBILA', 'DEFECTA', 'IN_MENTENANTA', name='stare_tehnica_enum'), nullable=False),
        sa.Column('stare_noua', sa.Enum('DISPONIBILA', 'DEFECTA', 'IN_MENTENANTA', name='stare_tehnica_enum'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_jurnal_tehnic_resursa_id'), 'jurnal_tehnic', ['resursa_id'], unique=False)
    op.create_index(op.f('ix_jurnal_tehnic_utilizator_id'), 'jurnal_tehnic', ['utilizator_id'], unique=False)


def downgrade() -> None:
    op.drop_table('jurnal_tehnic')
    op.drop_table('rezervari')
    op.drop_table('resurse')
    op.drop_table('categorii_resurse')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        stare_rezervare_enum.drop(bind, checkfirst=True)
        stare_tehnica_enum.drop(bind, checkfirst=True)
