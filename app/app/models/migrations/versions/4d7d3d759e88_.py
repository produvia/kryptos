"""empty message

Revision ID: 29498b27f9c4
Revises: b060ded0ae81
Create Date: 2018-07-29 01:43:41.940509

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '29498b27f9c4'
down_revision = 'b060ded0ae81'
branch_labels = None
depends_on = None


def upgrade():
    # Drop primary key constraint. Note the CASCASE clause - this deletes the foreign key constraint.
    op.drop_table('strategies')
    # Re-create the foreign key constraint
    # op.create_foreign_key('fk_roles_user_user_id_user', 'roles_users', 'user', ['user_id'], ['id'], ondelete='CASCADE')

def downgrade():
    op.create_table('strategies',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('trading_config', sa.JSON(), nullable=False),
    sa.Column('dataset_config', sa.JSON(), nullable=False),
    sa.Column('indicators_config', sa.JSON(), nullable=False),
    sa.Column('signals_config', sa.JSON(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
