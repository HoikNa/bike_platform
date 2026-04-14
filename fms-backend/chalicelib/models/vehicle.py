
import uuid
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlmodel import Field, Relationship, SQLModel

from .base import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .alert import Alert
    from .driver_profile import DriverProfile
    from .sensor_data import SensorData
    from .trip import Trip


class VehicleStatus(str, Enum):
    RUNNING  = "RUNNING"   # 운행 중
    IDLE     = "IDLE"      # 정차
    CHARGING = "CHARGING"  # 충전 중
    ALERT    = "ALERT"     # 경고 상태
    OFFLINE  = "OFFLINE"   # 통신 두절


class Vehicle(UUIDMixin, TimestampMixin, SoftDeleteMixin, table=True):
    """차량 마스터 테이블.

    Soft Delete 적용: deleted_at에 값이 있으면 폐차/매각 처리된 차량입니다.
    삭제 정책:
      - SensorData → RESTRICT  (데이터가 남아있으면 Vehicle 삭제 불가)
      - Alert      → RESTRICT
      - Trip       → RESTRICT
    운영상 차량을 Soft Delete 한 후, 관련 데이터는 별도 아카이브 배치로 처리합니다.
    """

    __tablename__ = "vehicles"
    __table_args__ = {"comment": "등록 차량 정보"}

    plate_number: str = Field(
        sa_column=Column(String(20), nullable=False, unique=True, index=True),
        description="차량 번호판 (고유)",
    )
    model: str = Field(
        sa_column=Column(String(100), nullable=False),
        description="차량 모델명 (예: PCX Electric)",
    )
    manufacturer: str = Field(
        sa_column=Column(String(50), nullable=False),
        description="제조사 (예: Honda)",
    )
    manufacture_year: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="제조 연도",
    )
    status: VehicleStatus = Field(
        default=VehicleStatus.OFFLINE,
        sa_column=Column(String(20), nullable=False, index=True),
        description="현재 차량 상태",
    )
    battery_capacity_kwh: float = Field(
        sa_column=Column(Float, nullable=False),
        description="배터리 총 용량 (kWh)",
    )
    vin: Optional[str] = Field(
        default=None,
        sa_column=Column(String(17), nullable=True, unique=True),
        description="차대 번호 (Vehicle Identification Number)",
    )

    # FK: 현재 배차된 운전자 (없을 수 있음)
    assigned_driver_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            ForeignKey("driver_profiles.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        description="배차된 운전자 프로필 ID (NULL = 미배차)",
    )

    # ── Relationships ─────────────────────────────────────────
    assigned_driver: Optional["DriverProfile"] = Relationship(
        back_populates="assigned_vehicles",
        sa_relationship_kwargs={
            "foreign_keys": "[Vehicle.assigned_driver_id]",
        },
    )
    sensor_data: List["SensorData"] = Relationship(back_populates="vehicle")
    alerts: List["Alert"] = Relationship(back_populates="vehicle")
    trips: List["Trip"] = Relationship(back_populates="vehicle")
