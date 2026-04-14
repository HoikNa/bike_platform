
from typing import Optional
from sqlalchemy import Column, Boolean, Float, Integer, String
from sqlmodel import Field, SQLModel

from .base import TimestampMixin, UUIDMixin


class ChargingStation(UUIDMixin, TimestampMixin, table=True):
    """충전소 정보 테이블.

    차량과 직접적인 FK 관계는 없습니다.
    기사 앱의 "충전소 찾기" 기능에서 위경도 기반 반경 검색(PostGIS 또는 수식)에 사용됩니다.
    """

    __tablename__ = "charging_stations"
    __table_args__ = {"comment": "충전소 위치 및 슬롯 정보"}

    name: str = Field(
        sa_column=Column(String(100), nullable=False),
        description="충전소 명칭",
    )
    address: str = Field(
        sa_column=Column(String(255), nullable=False),
        description="도로명 주소",
    )
    latitude: float = Field(
        sa_column=Column(Float, nullable=False, index=True),
        description="위도",
    )
    longitude: float = Field(
        sa_column=Column(Float, nullable=False, index=True),
        description="경도",
    )
    total_slots: int = Field(
        default=1,
        sa_column=Column(Integer, nullable=False),
        description="총 충전 슬롯 수",
    )
    available_slots: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False),
        description="현재 사용 가능한 슬롯 수",
    )
    operator_name: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
        description="운영 업체명",
    )
    contact_phone: Optional[str] = Field(
        default=None,
        sa_column=Column(String(20), nullable=True),
        description="충전소 연락처",
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, index=True),
        description="운영 여부",
    )
