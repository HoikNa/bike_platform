
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, Boolean
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .vehicle import Vehicle


class SensorData(SQLModel, table=True):
    """IoT 센서 원격측정 데이터 테이블.

    ⚠️  이 테이블은 TimescaleDB Hypertable로 변환됩니다.
        create_hypertable('sensor_data', 'time') 실행 후에는
        time 컬럼이 복합 Primary Key의 일부가 됩니다.

    PK 구성: (time, vehicle_id)
        - time 단독 PK로는 같은 시각 다중 차량 데이터 충돌 발생
        - vehicle_id 포함 복합 PK로 TimescaleDB 청크 내 고유성 보장

    데이터 규모 추정:
        - 차량 1대 × 1초 간격 × 86,400초 = 86,400 rows/일/대
        - 차량 100대 기준 약 864만 rows/일
        - 30일 = 약 2억 5,920만 rows
    """

    __tablename__ = "sensor_data"
    __table_args__ = (
        Index("idx_sensor_data_vehicle_time", "vehicle_id", "time"),
        {"comment": "IoT 센서 시계열 데이터 (TimescaleDB Hypertable)"},
    )

    # ── Primary Key (복합) ──────────────────────────────────────
    time: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            primary_key=True,
            comment="측정 시각 (UTC) — Hypertable 파티셔닝 기준",
        ),
    )
    vehicle_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("vehicles.id", ondelete="RESTRICT"),  # 센서 데이터 보존 원칙
            nullable=False,
            primary_key=True,
        ),
        description="센서 데이터를 발생시킨 차량 ID",
    )

    # ── GPS 데이터 ────────────────────────────────────────────
    latitude: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="위도 (°, WGS84)",
    )
    longitude: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="경도 (°, WGS84)",
    )
    altitude_m: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="해발 고도 (m)",
    )
    heading_deg: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="진행 방향 (°, 0=북, 90=동)",
    )

    # ── 주행 데이터 (OBD) ─────────────────────────────────────
    speed_kmh: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="현재 속도 (km/h)",
    )
    engine_rpm: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="엔진 RPM",
    )
    odometer_km: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="누적 주행 거리 (km)",
    )
    throttle_pct: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="스로틀 개도율 (%)",
    )
    brake_engaged: Optional[bool] = Field(
        default=None,
        sa_column=Column(Boolean, nullable=True),
        description="브레이크 작동 여부",
    )

    # ── 배터리 데이터 (BMS) ───────────────────────────────────
    battery_level_pct: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="배터리 잔량 (%)",
    )
    battery_voltage_v: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="배터리 전압 (V)",
    )
    battery_current_a: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="배터리 전류 (A, 양수=방전, 음수=충전)",
    )
    battery_temp_celsius: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="배터리 셀 온도 (°C)",
    )

    # ── 통신 품질 ─────────────────────────────────────────────
    signal_strength_dbm: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="LTE/4G 신호 강도 (dBm)",
    )

    # ── Relationship ──────────────────────────────────────────
    vehicle: Optional["Vehicle"] = Relationship(back_populates="sensor_data")
