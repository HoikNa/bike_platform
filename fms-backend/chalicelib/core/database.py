"""
database.py — SQLAlchemy 엔진 + 세션 팩토리

환경 분기:
  로컬 (DATABASE_URL 미설정)  → SQLite  (파일 기반, 개발 전용)
  프로덕션 (DATABASE_URL 설정) → PostgreSQL (AWS RDS / Supabase / Neon 등)

AWS Lambda는 stateless 실행 환경이므로 PostgreSQL 연결 시
NullPool 을 사용해 호출마다 커넥션을 새로 생성·반환합니다.
(커넥션 풀 유지 시 워커 재사용 시점에 "stale connection" 에러 발생 가능)
"""

from contextlib import contextmanager
from typing import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

# ── 환경 변수 ──────────────────────────────────────────────────────────────
DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./fms_local_v2.db")

_is_sqlite = DATABASE_URL.startswith("sqlite")

# ── 엔진 생성 ──────────────────────────────────────────────────────────────
if _is_sqlite:
    # 로컬 개발: SQLite (단일 스레드 체크 비활성화)
    _engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    # 프로덕션: PostgreSQL — Lambda stateless 환경에 맞게 NullPool 사용
    from sqlalchemy.pool import NullPool

    # Supabase / Neon 등 일부 서비스는 "postgresql+psycopg2://" 접두어를 요구합니다.
    # DATABASE_URL 이 "postgres://" 로 시작하면 자동 변환합니다.
    _db_url = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

    _engine = create_engine(
        _db_url,
        echo=False,
        poolclass=NullPool,          # Lambda: 호출마다 커넥션 새로 생성
        pool_pre_ping=True,          # 커넥션 유효성 사전 확인
        connect_args={
            "connect_timeout": 10,   # DB 연결 타임아웃 (초)
            "sslmode": "require",    # RDS / Supabase 기본 SSL 요구
        },
    )

# ── 세션 팩토리 ────────────────────────────────────────────────────────────
_SessionFactory = sessionmaker(bind=_engine, class_=Session, expire_on_commit=False)


def create_db_and_tables() -> None:
    """애플리케이션 시작 시 테이블 자동 생성 (idempotent)."""
    import chalicelib.models  # noqa: F401 — 모든 모델을 SQLModel 메타데이터에 등록
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
