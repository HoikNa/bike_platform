"""Database engine and session management.

This module provides:
- Engine creation (SQLite by default for local/dev)
- A session generator for request handlers
- Table auto-creation helper for app startup
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Iterator

from sqlmodel import Session, SQLModel, create_engine


def _default_database_url() -> str:
    """Return the default database URL for local development."""

    # Local SQLite file (created automatically).
    # Can be overridden with DATABASE_URL (e.g., PostgreSQL in the future).
    return "sqlite:///./fms_local_v2.db"


DATABASE_URL: str = os.environ.get("DATABASE_URL", _default_database_url())

# For SQLite, check_same_thread must be False when used across threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def create_db_and_tables() -> None:
    """Create all tables defined on SQLModel metadata."""

    SQLModel.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""

    with Session(engine) as session:
        yield session


def get_session() -> Generator[Session, None, None]:
    """Yield a DB session for a request handler.

    Chalice does not have built-in dependency injection, so handlers can use:

        for session in get_session():
            ...
    """

    with Session(engine) as session:
        yield session

