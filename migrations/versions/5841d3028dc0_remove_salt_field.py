"""remove salt field

Revision ID: 5841d3028dc0
Revises: a4fd6c867423
Create Date: 2024-12-12 15:45:05.222044

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '5841d3028dc0'
down_revision = 'a4fd6c867423'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('utenza', schema=None) as batch_op:
        batch_op.drop_column('salt')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('utenza', schema=None) as batch_op:
        batch_op.add_column(sa.Column('salt', mysql.VARCHAR(length=255), nullable=False))

    # ### end Alembic commands ###
