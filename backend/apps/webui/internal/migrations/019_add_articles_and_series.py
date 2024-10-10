"""Peewee migrations -- 019_add_articles_and_series.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress

import peewee as pw
from peewee import DeferredForeignKey
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    @migrator.create_model
    class Series(pw.Model):
        id = pw.TextField(unique=True, primary_key=True)
        name = pw.TextField(unique=True)
        admin_guide_urls = pw.TextField(null=True)
        datasheet_urls = pw.TextField(null=True)
        cli_guide_urls = pw.TextField(null=True)
        software_url = pw.TextField(null=True)

        created_at = pw.BigIntegerField(null=False)
        updated_at = pw.BigIntegerField(null=False)

        articles = pw.ManyToManyField(
            pw.DeferredForeignKey("Article"),
            backref="series",
            on_delete="CASCADE",
            on_update="CASCADE",
        )

        class Meta:
            table_name = "series"

    @migrator.create_model
    class Article(pw.Model):
        id = pw.TextField(unique=True, primary_key=True)
        title = pw.TextField()
        document_id = pw.TextField(unique=True)
        category = pw.TextField()
        url = pw.TextField(unique=True)
        objective = pw.TextField()
        applicable_devices = pw.TextField()
        introduction = pw.TextField()
        steps = pw.TextField()

        series = pw.ManyToManyField(DeferredForeignKey("Series"), backref="articles")

        created_at = pw.BigIntegerField(null=False)
        updated_at = pw.BigIntegerField(null=False)

        class Meta:
            table_name = "articles"

    @migrator.create_model
    class ArticleOnSeries(pw.Model):
        article = pw.ForeignKeyField(
            Article,
            backref="series",
            on_delete="CASCADE",
            lazy_load=True,
        )
        series = pw.ForeignKeyField(
            Series,
            backref="articles",
            on_delete="CASCADE",
            lazy_load=True,
        )

        class Meta:
            table_name = "article_on_series"
            primary_key = pw.CompositeKey("article", "series")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model("article_on_series")
    migrator.remove_model("articles")
    migrator.remove_model("series")
