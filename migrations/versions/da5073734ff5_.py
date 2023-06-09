"""empty message

Revision ID: da5073734ff5
Revises: 5281daa906ae
Create Date: 2023-03-31 09:00:10.820302

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da5073734ff5'
down_revision = '5281daa906ae'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('cells',
    sa.Column('cell', sa.Integer(), nullable=False),
    sa.Column('cause', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('cell')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('cells')
    # ### end Alembic commands ###
