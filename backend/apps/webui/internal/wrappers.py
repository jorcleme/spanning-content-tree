from contextvars import ContextVar
from peewee import *
from peewee import PostgresqlDatabase, InterfaceError as PeeWeeInterfaceError

import logging
from playhouse.db_url import connect, parse
from playhouse.shortcuts import ReconnectMixin

from config import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["DB"])

db_state_default = {"closed": None, "conn": None, "ctx": None, "transactions": None}
db_state = ContextVar("db_state", default=db_state_default.copy())


class PeeweeConnectionState(object):
    def __init__(self, **kwargs):
        super().__setattr__("_state", db_state)
        super().__init__(**kwargs)

    def __setattr__(self, name, value):
        self._state.get()[name] = value

    def __getattr__(self, name):
        value = self._state.get()[name]
        return value


class CustomReconnectMixin(ReconnectMixin):
    reconnect_errors = (
        # psycopg2
        (OperationalError, "termin"),
        (InterfaceError, "closed"),
        # peewee
        (PeeWeeInterfaceError, "closed"),
    )


class ReconnectingPostgresqlDatabase(CustomReconnectMixin, PostgresqlDatabase):
    pass


def register_connection(db_url):
    db = connect(db_url)
    if isinstance(db, PostgresqlDatabase):
        # Enable autoconnect for SQLite databases, managed by Peewee
        db.autoconnect = True
        db.reuse_if_open = True
        log.info("Connected to PostgreSQL database")

        # Get the connection details
        connection = parse(db_url)

        # Use our custom database class that supports reconnection
        db = ReconnectingPostgresqlDatabase(
            connection["database"],
            user=connection["user"],
            password=connection["password"],
            host=connection["host"],
            port=connection["port"],
        )
        db.connect(reuse_if_open=True)
    elif isinstance(db, SqliteDatabase):
        # Enable autoconnect for SQLite databases, managed by Peewee
        db.autoconnect = True
        db.reuse_if_open = True
        db.foreign_keys = (
            True  # Enables foreign key tracking within Peewee's database context
        )
        db.execute_sql(
            "PRAGMA foreign_keys = ON;"
        )  # Enables foreign key tracking within SQLite
        log.info("Connected to SQLite database with foreign key support enabled")
    else:
        raise ValueError("Unsupported database connection")
    return db
