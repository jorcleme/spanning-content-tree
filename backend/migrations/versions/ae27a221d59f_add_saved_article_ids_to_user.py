"""add saved article ids to user

Revision ID: ae27a221d59f
Revises: ed434c47b7c1
Create Date: 2024-12-04 11:10:51.252282

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import apps.webui.internal.db


# revision identifiers, used by Alembic.
revision: str = "ae27a221d59f"
down_revision: Union[str, None] = "ed434c47b7c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "saved_article_ids", apps.webui.internal.db.JSONField(), nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_column("user", "saved_article_ids")
