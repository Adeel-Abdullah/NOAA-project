"""added TLEupdate Timestamp

Revision ID: 61088733377d
Revises: 0911fa97bf5d
Create Date: 2023-12-24 15:16:30.445701

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '61088733377d'
down_revision = '0911fa97bf5d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('satellite', schema=None) as batch_op:
        batch_op.add_column(sa.Column('TLEUpdateTime', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('satellite', schema=None) as batch_op:
        batch_op.drop_column('TLEUpdateTime')

    # ### end Alembic commands ###
