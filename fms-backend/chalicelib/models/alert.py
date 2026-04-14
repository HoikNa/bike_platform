
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, String, Text
from sqlmodel import Field, Relationship, SQLModel

from .base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .user import User
    from .vehicle import Vehicle


class AlertType(str, Enum):
    OVERSPEED          = "OVERSPEED"           # 과속
    BATTERY_LOW        = "BATTERY_LOW"         # 배터리 부족 (≤30%)
    BATTERY_CRITICAL   = "BATTERY_CRITICAL"    # 배터리 위험 (≤10%)
    GEOFENCE_EXIT      = "GEOFENCE_EXIT"       # 운행 구역 이탈
    SUDDEN_ACCEL       = "SUDDEN_ACCEL"        # 급가속
    SUDDEN_BRAKE       = "SUDDEN_BRAKE"        # 급감속
    ACCIDENT_SUSPECTED = "ACCIDENT_SUSPECTED"  # 사고 의심 (충격 감지)
    MAINTENANCE_DUE    = "MAINTENANCE_DUE"     # 정비 권고
    COMMUNICATION_LOST = "COMMUNICATION_LOST"  # 통신 두절


class AlertSeverity(str, Enum):
    INFO    = "INFO"     # 참고 (파란색)
    WARNING = "WARNING"  # 주의 (노란색)
    DANGER  = "DANGER"   # 위험 (빨간색)


class Alert(UUIDMixin, TimestampMixin, table=True):
    """이벤트 및 경고 내역 테이블.

    Cascade 정책:
        - Vehicle 삭제 → RESTRICT (경고 기록 보존 원칙)
        - acknowledged_by User 삭제 → SET NULL (기록은 유지, 담당자 정보만 해제)
    """

    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alerts_vehicle_triggered", "vehicle_id", "triggered_at"),
        Index("idx_alerts_severity_ack", "severity", "is_acknowledged"),
        {"comment": "차량 이벤트 및 경고 내역"},
    )

    # ── 핵심 필드 ─────────────────────────────────────────────
    vehicle_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("vehicles.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
    )
    triggered_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            index=True,
            comment="경고 발생 시각 (UTC)",
        ),
    )
    alert_type: AlertType = Field(
        sa_column=Column(String(30), nullable=False, index=True),
    )
    severity: AlertSeverity = Field(
        sa_column=Column(String(10), nullable=False, index=True),
    )
    title: str = Field(
        sa_column=Column(String(200), nullable=False),
        description="경고 제목 (예: '17호차 과속 감지 — 92km/h')",
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="경고 상세 설명",
    )

    # ── 발생 시점 컨텍스트 (스냅샷) ──────────────────────────
    # 이 값들은 나중에 SensorData가 삭제/압축되어도 경고 내용 파악이 가능하도록
    # 경고 발생 시점의 값을 비정규화하여 함께 저장합니다.
    speed_at_trigger: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="경고 발생 시 속도 (km/h)",
    )
    battery_at_trigger: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="경고 발생 시 배터리 잔량 (%)",
    )
    location_lat: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="경고 발생 위치 — 위도",
    )
    location_lng: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="경고 발생 위치 — 경도",
    )

    # ── 처리 상태 ─────────────────────────────────────────────
    is_acknowledged: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, index=True),
        description="관제사 확인 여부",
    )
    acknowledged_by_id: Optional[uuid.UUID] = Field(
        default=None,
        sa_column=Column(
            ForeignKey("users.id", ondelete="SET NULL"),  # 담당자 퇴사해도 경고 기록 유지
            nullable=True,
        ),
        description="확인한 관제사 User ID",
    )
    acknowledged_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="확인 처리 일시",
    )

    # ── Relationships ─────────────────────────────────────────
    vehicle: Optional["Vehicle"] = Relationship(back_populates="alerts")
    acknowledger: Optional["User"] = Relationship(
        back_populates="acknowledged_alerts",
        sa_relationship_kwargs={"foreign_keys": "[Alert.acknowledged_by_id]"},
    )
