"""create user table

Revision ID: 88beadc294df
Revises: 
Create Date: 2020-01-10 16:02:20.735468

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INTEGER

# revision identifiers, used by Alembic.
revision = '88beadc294df'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', INTEGER, primary_key=True, autoincrement=True),
        sa.Column('email', sa.String, nullable=False, unique=True),
        sa.Column('password', sa.String),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('creator', INTEGER),
        sa.Column('modifier', INTEGER),
        sa.Column('created_at', TIMESTAMP, default=text('statement_timestamp()')),
        sa.Column('modified_at', TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()')),
    )
    op.create_table(
        'users_groups',
        sa.Column('user_id', INTEGER, primary_key=True),
        sa.Column('group_id', INTEGER, primary_key=True),
        sa.Column('creator', INTEGER),
        sa.Column('modifier', INTEGER),
        sa.Column('created_at', TIMESTAMP, default=text('statement_timestamp()')),
        sa.Column('modified_at', TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()')),
    )
    op.create_table(
        'groups',
        sa.Column('id', INTEGER, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('is_admin', sa.Integer, default=0, nullable=False),
        sa.Column('creator', INTEGER),
        sa.Column('modifier', INTEGER),
        sa.Column('created_at', TIMESTAMP, default=text('statement_timestamp()')),
        sa.Column('modified_at', TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()')),
    )
    op.create_table(
        'auth',
        sa.Column('group_id', INTEGER, primary_key=True),
        sa.Column('data_id', INTEGER, primary_key=True),
        sa.Column('read', sa.Integer, default=0, nullable=False),
        # sa.Column('write', sa.Integer, default=0, nullable=False),
        # sa.Column('exec', sa.Integer, default=0, nullable=False),
        # sa.Column('own', sa.Integer, default=0, nullable=False),
        sa.Column('creator', INTEGER),
        sa.Column('modifier', INTEGER),
        sa.Column('created_at', TIMESTAMP, default=text('statement_timestamp()')),
        sa.Column('modified_at', TIMESTAMP, default=text('statement_timestamp()'), onupdate=text('statement_timestamp()')),
    )


def downgrade():
    op.drop_table('users')
    op.drop_table('groups')
    op.drop_table('users_groups')
    op.drop_table('auth')
