"""empty message

Revision ID: b56cba7a808f
Revises: 
Create Date: 2019-10-25 21:24:14.092521

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b56cba7a808f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('score',
    sa.Column('score_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('score', sa.String(length=1024), nullable=False),
    sa.PrimaryKeyConstraint('score_id')
    )
    op.create_table('user',
    sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('username', sa.String(length=1024), nullable=False),
    sa.Column('pwd_hash', sa.String(length=1024), nullable=False),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.drop_table('users')
    op.drop_table('scores')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('scores',
    sa.Column('id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('score', sa.TEXT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='idx_11906297_scores_pkey')
    )
    op.create_table('users',
    sa.Column('user_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('username', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('hash', sa.TEXT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('user_id', name='idx_11906289_users_pkey')
    )
    op.drop_table('user')
    op.drop_table('score')
    # ### end Alembic commands ###