"""add fields to articles table

Revision ID: ed434c47b7c1
Revises: 5e424685f01a
Create Date: 2024-11-21 12:10:57.059086

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ed434c47b7c1"
down_revision: Union[str, None] = "5e424685f01a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = [column["name"] for column in inspector.get_columns("articles")]
    if "published" not in columns:
        sa.Column("published", sa.Boolean())
    if "user_id" not in columns:
        sa.Column("user_id", sa.String())
    if "sources" not in columns:
        sa.Column("sources", sa.Text())


def downgrade() -> None:
    op.drop_column("articles", "published")
    op.drop_column("articles", "user_id")
    op.drop_column("articles", "sources")
