
import uuid
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, String, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from .base import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .alert import Alert
    from .driver_profile import DriverProfile


class UserRole(str, Enum):
    ADMIN   = "ADMIN"    # 시스템 전체 관리자
    MANAGER = "MANAGER"  # 운영 매니저 (차량 배차, 알림 조회)
    DRIVER  = "DRIVER"   # 배달 기사 (본인 차량 정보만 접근)


class User(UUIDMixin, TimestampMixin, SoftDeleteMixin, table=True):
    """사용자 테이블.

    관리자·매니저는 DriverProfile이 없고, DRIVER 역할 사용자만 DriverProfile을 가집니다.
    비밀번호는 bcrypt 해시로만 저장합니다 (평문 절대 금지).
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        {"comment": "시스템 사용자 (관리자/매니저/기사)"},
    )

    email: str = Field(
        sa_column=Column(String(255), nullable=False, index=True),
        description="로그인 이메일 (고유)",
    )
    hashed_password: str = Field(
        sa_column=Column(String(255), nullable=False),
        description="bcrypt 해시 비밀번호",
    )
    full_name: str = Field(
        sa_column=Column(String(100), nullable=False),
        description="사용자 실명",
    )
    role: UserRole = Field(
        default=UserRole.DRIVER,
        sa_column=Column(String(20), nullable=False, index=True),
        description="권한 역할",
    )
    is_active: bool = Field(
        default=True,
        description="계정 활성화 여부 (False = 정지 계정)",
    )

    # ── Relationships ─────────────────────────────────────────
    # User 1 ─── 1 DriverProfile  (role=DRIVER인 경우에만 존재)
    driver_profile: Optional["DriverProfile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False},
    )
    # User 1 ─── N Alert  (acknowledged_by 역방향)
    acknowledged_alerts: List["Alert"] = Relationship(
        back_populates="acknowledger",
        sa_relationship_kwargs={
            "foreign_keys": "[Alert.acknowledged_by_id]",
            "lazy": "select",
        },
    )
