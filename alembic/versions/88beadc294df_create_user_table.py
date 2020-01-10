"""create user table

Revision ID: 88beadc294df
Revises: 
Create Date: 2020-01-10 16:02:20.735468

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88beadc294df'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', String, primary_key=True),
        sa.Column('email', String, nullable=False, unique=True),
        sa.Column('password', String),
        sa.Column('name', String, nullable=False),
        sa.Column('creator', Integer),
        sa.Column('modifier', Integer),
        sa.Column('created_at', String, default=text('CURRENT_TIMESTAMP')),
        sa.Column('modified_at', String, default=text('CURRENT_TIMESTAMP')),
    )
    op.create_table(
        'users_groups',
        sa.Column('user_id', String)
        sa.Column('group_id', String)
        sa.Column('creator', Integer)
        sa.Column('modifier', Integer)
        sa.Column('created_at', String, default=text('CURRENT_TIMESTAMP'))
        sa.Column('modified_at', String, default=text('CURRENT_TIMESTAMP'))
    )
    op.create_table(
        'groups',
        sa.Column('id', String, primary_key=True)
        sa.Column('name', String, nullable=False)
        sa.Column('is_admin', Integer, default=0, nullable=False)
        sa.Column('creator', Integer)
        sa.Column('modifier', Integer)
        sa.Column('created_at', String, default=text('CURRENT_TIMESTAMP'))
        sa.Column('modified_at', String, default=text('CURRENT_TIMESTAMP'))
    )
    op.create_table(
        'auth',
        sa.Column('group_id', String, primary_key=True)
        sa.Column('data_id', String, primary_key=True)
        sa.Column('read', Integer, default=0, nullable=False)
        # write       = Column(Integer, default=0, nullable=False)
        # exec        = Column(Integer, default=0, nullable=False)
        # own         = Column(Integer, default=0, nullable=False)
        sa.Column('creator', Integer)
        sa.Column('modifier', Integer)
        sa.Column('created_at', String, default=text('CURRENT_TIMESTAMP'))
        sa.Column('modified_at', String, default=text('CURRENT_TIMESTAMP'))
    )


def downgrade():
    op.drop_table('users')
    op.drop_table('groups')
    op.drop_table('users_groups')
    op.drop_table('auth')
