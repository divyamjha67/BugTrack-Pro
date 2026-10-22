"""Database connection and the session used for each API request."""

import os
from collections.abc import Generator
from pathlib import Path

from fastapi import Request
from sqlalchemy import URL, Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    """Every table model inherits from this class."""


DEFAULT_DATABASE_URL = URL.create(
    "sqlite", database=str(Path(__file__).resolve().parent.parent / "bugtrack.db")
)


def create_database_engine(database_url: str | URL) -> Engine:
    database_engine = create_engine(database_url)
    if database_engine.dialect.name == "sqlite":

        @event.listens_for(database_engine, "connect")
        def enable_foreign_keys(connection, _connection_record):
            # SQLite does not enforce foreign keys unless each connection enables them.
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return database_engine


engine = create_database_engine(os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL)


def initialize_database(database_engine: Engine) -> None:
    # Importing the models registers all four tables with Base.metadata.
    from . import models  # noqa: F401

    Base.metadata.create_all(database_engine)


def get_db(request: Request) -> Generator[Session, None, None]:
    # Use this app's engine, including when a test supplies a temporary database.
    with Session(request.app.state.database_engine, autoflush=False) as session:
        yield session
