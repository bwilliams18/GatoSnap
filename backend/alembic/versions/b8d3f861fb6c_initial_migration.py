"""initial migration

Revision ID: b8d3f861fb6c
Revises: 
Create Date: 2023-08-17 17:47:56.049149

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8d3f861fb6c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('storage_device',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('base_path', sa.String(), nullable=False),
    sa.Column('sync_on_deck', sa.Boolean(), nullable=False),
    sa.Column('sync_continue_watching', sa.Boolean(), nullable=False),
    sa.Column('sync_playlist', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('func', sa.String(), nullable=False),
    sa.Column('args', sa.JSON(), nullable=False),
    sa.Column('kwargs', sa.JSON(), nullable=False),
    sa.Column('progress', sa.Float(), nullable=False),
    sa.Column('total', sa.Float(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', name='taskstatus'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('file',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('storage_device_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('remote_path', sa.String(), nullable=False),
    sa.Column('storage_path', sa.String(), nullable=True),
    sa.Column('rating_key', sa.Integer(), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('md5', sa.String(), nullable=False),
    sa.Column('status', sa.Enum('MISSING', 'SYNCED', 'WATCHED', name='filestatus'), nullable=False),
    sa.ForeignKeyConstraint(['storage_device_id'], ['storage_device.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('file')
    op.drop_table('task')
    op.drop_table('storage_device')
    # ### end Alembic commands ###
