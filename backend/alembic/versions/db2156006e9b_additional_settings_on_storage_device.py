"""additional settings on storage device

Revision ID: db2156006e9b
Revises: 57e8b396ea52
Create Date: 2023-08-19 20:19:20.427646

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "db2156006e9b"
down_revision = "57e8b396ea52"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "storage_device",
        sa.Column(
            "sync_all_episodes", sa.Boolean(), nullable=False, server_default="1"
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("storage_device", "sync_all_episodes")
    # ### end Alembic commands ###
