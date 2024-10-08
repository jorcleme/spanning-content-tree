"""Ensure Article and Series tables exist

Revision ID: 5e424685f01a
Revises: 7e5b5dc7342b
Create Date: 2024-09-05 12:25:15.331396

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import apps.webui.internal.db
from migrations.util import get_existing_tables


# revision identifiers, used by Alembic.
revision: str = "5e424685f01a"
down_revision: Union[str, None] = "7e5b5dc7342b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(get_existing_tables())
    # ### commands auto generated by Alembic - please adjust! ###
    # ### commands auto generated by Alembic - please adjust! ###
    if "auth" not in existing_tables:
        op.create_table(
            "auth",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("password", sa.Text(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "chat" not in existing_tables:
        inspector = sa.inspect(op.get_bind())
        columns = [column["name"] for column in inspector.get_columns("chat")]
        op.create_table(
            "chat",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("chat", sa.Text(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("archived", sa.Boolean(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

        if "share_id" not in columns:
            op.add_column("chat", sa.Column("share_id", sa.Text(), nullable=True))
            sa.UniqueConstraint("share_id")

    if "chatidtag" not in existing_tables:
        op.create_table(
            "chatidtag",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("tag_name", sa.String(), nullable=True),
            sa.Column("chat_id", sa.String(), nullable=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("timestamp", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "document" not in existing_tables:
        op.create_table(
            "document",
            sa.Column("collection_name", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("filename", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("timestamp", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("collection_name"),
            sa.UniqueConstraint("name"),
        )

    if "file" not in existing_tables:
        op.create_table(
            "file",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("filename", sa.Text(), nullable=True),
            sa.Column("meta", apps.webui.internal.db.JSONField(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "function" not in existing_tables:
        op.create_table(
            "function",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("name", sa.Text(), nullable=True),
            sa.Column("type", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("meta", apps.webui.internal.db.JSONField(), nullable=True),
            sa.Column("valves", apps.webui.internal.db.JSONField(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("is_global", sa.Boolean(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "memory" not in existing_tables:
        op.create_table(
            "memory",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "model" not in existing_tables:
        op.create_table(
            "model",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("user_id", sa.Text(), nullable=True),
            sa.Column("base_model_id", sa.Text(), nullable=True),
            sa.Column("name", sa.Text(), nullable=True),
            sa.Column("params", apps.webui.internal.db.JSONField(), nullable=True),
            sa.Column("meta", apps.webui.internal.db.JSONField(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "prompt" not in existing_tables:
        op.create_table(
            "prompt",
            sa.Column("command", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("timestamp", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("command"),
        )

    if "tag" not in existing_tables:
        op.create_table(
            "tag",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("data", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "tool" not in existing_tables:
        op.create_table(
            "tool",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("name", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("specs", apps.webui.internal.db.JSONField(), nullable=True),
            sa.Column("meta", apps.webui.internal.db.JSONField(), nullable=True),
            sa.Column("valves", apps.webui.internal.db.JSONField(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "user" not in existing_tables:
        op.create_table(
            "user",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("role", sa.String(), nullable=True),
            sa.Column("profile_image_url", sa.Text(), nullable=True),
            sa.Column("last_active_at", sa.BigInteger(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.Column("api_key", sa.String(), nullable=True),
            sa.Column("settings", apps.webui.internal.db.JSONField(), nullable=True),
            sa.Column("info", apps.webui.internal.db.JSONField(), nullable=True),
            sa.Column("oauth_sub", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("api_key"),
            sa.UniqueConstraint("oauth_sub"),
        )

    if "series" not in existing_tables:
        op.create_table(
            "series",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column(
                "admin_guide_urls", apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column(
                "datasheet_urls", apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column(
                "cli_guide_urls", apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column("software_url", sa.Text(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=False),
            sa.Column("updated_at", sa.BigInteger(), nullable=False),
            sa.Column("articles", apps.webui.internal.db.JSONField(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )

    if "articles" not in existing_tables:
        op.create_table(
            "articles",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("document_id", sa.String(), nullable=False),
            sa.Column("category", sa.String(), nullable=False),
            sa.Column("url", sa.String(), nullable=False),
            sa.Column("objective", sa.Text(), nullable=True),
            sa.Column(
                "applicable_devices", apps.webui.internal.db.JSONField(), nullable=True
            ),
            sa.Column("introduction", sa.Text(), nullable=True),
            sa.Column("steps", apps.webui.internal.db.JSONField(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=False),
            sa.Column("updated_at", sa.BigInteger(), nullable=False),
            sa.Column("series", apps.webui.internal.db.JSONField(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("document_id"),
            sa.UniqueConstraint("url"),
        )

    if "article_on_series" not in existing_tables:
        op.create_table(
            "article_on_series",
            sa.Column("article_id", sa.String(), nullable=False),
            sa.Column("series_id", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(
                ["article_id"], ["articles.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["series_id"], ["series.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("article_id", "series_id"),
        )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("article_on_series")
    op.drop_table("articles")
    op.drop_table("series")
    # ### end Alembic commands ###
