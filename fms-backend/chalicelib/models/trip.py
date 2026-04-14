
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, Text
from sqlmodel import Field, Relationship, SQLModel

from .base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .driver_profile import DriverProfile
    from .vehicle import Vehicle


class Trip(UUIDMixin, TimestampMixin, table=True):
    """운행 기록 요약 테이블.

    SensorData가 초 단위 원시 데이터라면,
    Trip은 "출발~도착" 한 구간의 요약 통계입니다.
    (총 거리, 평균/최고속도, 배터리 소모량, 발생 알림 수 등)

    Cascade 정책:
        - Vehicle 삭제 → RESTRICT
        - DriverProfile 삭제 → SET NULL (운행 기록은 유지, 기사 정보만 해제)
    """

    __tablename__ = "trips"
    __table_args__ = (
        Index("idx_trips_vehicle_started", "vehicle_id", "started_at"),
        Index("idx_trips_driver_started", "driver_id", "started_at"),
        {"comment": "차량 운행 구간 요약 기록"},
    )

    vehicle_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("vehicles.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
    )
    driver_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            ForeignKey("driver_profiles.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        description="운행 기사 ID (미배차 운행 시 NULL 가능)",
    )

    # ── 운행 시간 ─────────────────────────────────────────────
    started_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            comment="운행 시작 일시 (UTC)",
        ),
    )
    ended_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=True,
            comment="운행 종료 일시 (NULL = 운행 중)",
        ),
    )

    # ── 운행 경로 ─────────────────────────────────────────────
    start_address: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="출발지 주소 (역지오코딩 결과)",
    )
    end_address: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="도착지 주소",
    )

    # ── 운행 통계 (SensorData 집계값) ────────────────────────
    distance_km: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="총 운행 거리 (km)",
    )
    avg_speed_kmh: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="평균 속도 (km/h)",
    )
    max_speed_kmh: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="최고 속도 (km/h)",
    )
    battery_start_pct: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="출발 시 배터리 잔량 (%)",
    )
    battery_end_pct: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="도착 시 배터리 잔량 (%)",
    )
    alert_count: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False),
        description="운행 중 발생한 알림 수",
    )

    # ── Relationships ─────────────────────────────────────────
    vehicle: Optional["Vehicle"] = Relationship(back_populates="trips")
    driver: Optional["DriverProfile"] = Relationship(back_populates="trips")
