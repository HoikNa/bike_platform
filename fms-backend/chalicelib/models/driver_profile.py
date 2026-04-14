
import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Date, ForeignKey, String, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from .base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .trip import Trip
    from .user import User
    from .vehicle import Vehicle


class DriverProfile(UUIDMixin, TimestampMixin, table=True):
    """운전자 세부 프로필.

    User(role=DRIVER) 와 1:1 관계입니다.
    User 삭제 시 CASCADE DELETE 처리됩니다 (User의 Soft Delete가 발생해도 물리 행은 유지).
    단, User 물리 삭제(admin 정리 배치) 시에만 Cascade가 실제로 작동합니다.
    """

    __tablename__ = "driver_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_driver_profiles_user_id"),
        UniqueConstraint("license_number", name="uq_driver_profiles_license"),
        {"comment": "운전자 면허 및 연락처 정보"},
    )

    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("users.id", ondelete="CASCADE"),  # User 물리 삭제 시 함께 삭제
            nullable=False,
            unique=True,
        ),
        description="연결된 User ID",
    )
    license_number: str = Field(
        sa_column=Column(String(30), nullable=False),
        description="운전면허 번호",
    )
    license_expiry: date = Field(
        sa_column=Column(Date, nullable=False),
        description="운전면허 만료일",
    )
    phone: str = Field(
        sa_column=Column(String(20), nullable=False),
        description="연락처",
    )
    emergency_contact: Optional[str] = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
        description="비상 연락처",
    )

    # ── Relationships ─────────────────────────────────────────
    user: Optional["User"] = Relationship(back_populates="driver_profile")

    # DriverProfile 1 ─── N Vehicle  (배차 관계)
    assigned_vehicles: List["Vehicle"] = Relationship(
        back_populates="assigned_driver",
        sa_relationship_kwargs={
            "foreign_keys": "[Vehicle.assigned_driver_id]",
        },
    )
    # DriverProfile 1 ─── N Trip
    trips: List["Trip"] = Relationship(back_populates="driver")
