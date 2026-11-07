from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c7d2a91e4b10'
down_revision: Union[str, None] = 'fb2aefdda6c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


tip_sala_enum = postgresql.ENUM(
    'LABORATOR', 'SALA_CERCETARE', 'ATELIER', 'SALA_SERVERE', 'DEPOZIT',
    name='tip_sala_enum',
    create_type=False,
)


def upgrade() -> None:
    tip_sala_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'institutii',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nume', sa.String(length=255), nullable=False),
        sa.Column('cod', sa.String(length=30), nullable=False),
        sa.Column('oras', sa.String(length=100), nullable=False),
        sa.Column('adresa', sa.String(length=255), nullable=False),
        sa.Column('email_contact', sa.String(length=255), nullable=True),
        sa.Column('telefon', sa.String(length=20), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_institutii_nume'), 'institutii', ['nume'], unique=True)
    op.create_index(op.f('ix_institutii_cod'), 'institutii', ['cod'], unique=True)

    op.create_table(
        'facultati',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('institutie_id', sa.Integer(), nullable=False),
        sa.Column('nume', sa.String(length=255), nullable=False),
        sa.Column('cod', sa.String(length=30), nullable=False),
        sa.Column('descriere', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['institutie_id'], ['institutii.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('institutie_id', 'nume', name='uq_facultati_institutie_nume'),
        sa.UniqueConstraint('institutie_id', 'cod', name='uq_facultati_institutie_cod'),
    )
    op.create_index(op.f('ix_facultati_institutie_id'), 'facultati', ['institutie_id'], unique=False)

    op.create_table(
        'departamente',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('facultate_id', sa.Integer(), nullable=False),
        sa.Column('nume', sa.String(length=255), nullable=False),
        sa.Column('cod', sa.String(length=30), nullable=False),
        sa.Column('descriere', sa.String(length=500), nullable=True),
        sa.Column('sef_departament_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['facultate_id'], ['facultati.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['sef_departament_id'], ['utilizatori.id_utilizator'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('facultate_id', 'nume', name='uq_departamente_facultate_nume'),
        sa.UniqueConstraint('facultate_id', 'cod', name='uq_departamente_facultate_cod'),
    )
    op.create_index(op.f('ix_departamente_facultate_id'), 'departamente', ['facultate_id'], unique=False)
    op.create_index(op.f('ix_departamente_sef_departament_id'), 'departamente', ['sef_departament_id'], unique=False)

    op.create_table(
        'sali',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('departament_id', sa.Integer(), nullable=False),
        sa.Column('cod', sa.String(length=30), nullable=False),
        sa.Column('nume', sa.String(length=255), nullable=False),
        sa.Column('tip_sala', tip_sala_enum, nullable=False),
        sa.Column('etaj', sa.Integer(), nullable=False),
        sa.Column('capacitate', sa.Integer(), nullable=False),
        sa.Column('descriere', sa.String(length=500), nullable=True),
        sa.Column('responsabil_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('capacitate > 0', name='ck_sali_capacitate_pozitiva'),
        sa.CheckConstraint('etaj >= -3 AND etaj <= 30', name='ck_sali_etaj_valid'),
        sa.ForeignKeyConstraint(['departament_id'], ['departamente.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['responsabil_id'], ['utilizatori.id_utilizator'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('departament_id', 'nume', name='uq_sali_departament_nume'),
    )
    op.create_index(op.f('ix_sali_cod'), 'sali', ['cod'], unique=True)
    op.create_index(op.f('ix_sali_departament_id'), 'sali', ['departament_id'], unique=False)
    op.create_index(op.f('ix_sali_responsabil_id'), 'sali', ['responsabil_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sali_responsabil_id'), table_name='sali')
    op.drop_index(op.f('ix_sali_departament_id'), table_name='sali')
    op.drop_index(op.f('ix_sali_cod'), table_name='sali')
    op.drop_table('sali')
    op.drop_index(op.f('ix_departamente_sef_departament_id'), table_name='departamente')
    op.drop_index(op.f('ix_departamente_facultate_id'), table_name='departamente')
    op.drop_table('departamente')
    op.drop_index(op.f('ix_facultati_institutie_id'), table_name='facultati')
    op.drop_table('facultati')
    op.drop_index(op.f('ix_institutii_cod'), table_name='institutii')
    op.drop_index(op.f('ix_institutii_nume'), table_name='institutii')
    op.drop_table('institutii')
    tip_sala_enum.drop(op.get_bind(), checkfirst=True)
