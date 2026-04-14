
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """항상 timezone-aware UTC datetime을 반환합니다."""
    return datetime.now(timezone.utc)


class UUIDMixin(SQLModel):
    """UUID 기본키 Mixin — table=True 없이 상속만 받아 사용합니다."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"comment": "기본키 (UUID v4)"},
    )


class TimestampMixin(SQLModel):
    """created_at / updated_at 자동 관리 Mixin.

    - created_at: 레코드 최초 생성 시 자동 기록 (DB 레벨 default)
    - updated_at: UPDATE 발생 시 SQLAlchemy onupdate 트리거로 자동 갱신
    """

    created_at: datetime = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "nullable": False,
            "comment": "생성 일시 (UTC)",
        },
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "nullable": False,
            "onupdate": utcnow,
            "comment": "최종 수정 일시 (UTC)",
        },
    )


class SoftDeleteMixin(SQLModel):
    """Soft Delete Mixin.

    deleted_at 이 None → 유효한 레코드
    deleted_at 에 값   → 삭제된 레코드 (물리 삭제 X)
    """

    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "nullable": True,
            "index": True,
            "comment": "소프트 삭제 일시 (NULL=유효)",
        },
    )
