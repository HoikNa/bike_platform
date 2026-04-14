from contextlib import contextmanager
from typing import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

# Local SQLite file
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./fms_local_v2.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

_engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True if not DATABASE_URL.startswith("sqlite") else False,
    connect_args=connect_args,
)

_SessionFactory = sessionmaker(bind=_engine, class_=Session, expire_on_commit=False)

def create_db_and_tables() -> None:
    # Need to import all models to ensure SQLModel registers them
    import chalicelib.models  # noqa: F401
    SQLModel.metadata.create_all(_engine)

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """SQLModel 세션 컨텍스트 매니저."""
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
