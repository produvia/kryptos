"""empty message

Revision ID: 9d05939446cd
Revises: 1d39fb6ab24a
Create Date: 2018-07-24 20:12:53.214761

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d05939446cd'
down_revision = '1d39fb6ab24a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('telegram_auth_date', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'telegram_auth_date')
    # ### end Alembic commands ###
