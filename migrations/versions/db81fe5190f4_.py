"""empty message

Revision ID: db81fe5190f4
Revises: 26871be19c20
Create Date: 2023-07-22 12:10:13.906725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'db81fe5190f4'
down_revision = '26871be19c20'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('satellite',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('Name', sa.String(length=50), nullable=True),
    sa.Column('Norad_id', sa.Integer(), nullable=False),
    sa.Column('OperatingFreq', sa.Numeric(precision=7, scale=4), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('Name')
    )
    op.create_table('pass_data',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('AOS', sa.DateTime(), nullable=True),
    sa.Column('LOS', sa.DateTime(), nullable=True),
    sa.Column('maxElevation', sa.Integer(), nullable=True),
    sa.Column('ScheduledToReceive', sa.Boolean(), nullable=True),
    sa.Column('SatetlliteName', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['SatetlliteName'], ['satellite.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('pass_data', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pass_data_AOS'), ['AOS'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # ### end Alembic commands ###