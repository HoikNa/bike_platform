from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class VehicleRef(BaseModel):
    id: UUID
    plate_number: str
    model_config = ConfigDict(from_attributes=True)


class DriverRef(BaseModel):
    id: UUID
    user_full_name: str
    model_config = ConfigDict(from_attributes=True)


class TripRead(BaseModel):
    id: UUID
    vehicle: VehicleRef
    driver: Optional[DriverRef] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    start_address: Optional[str] = None
    end_address: Optional[str] = None
    distance_km: Optional[float] = None
    avg_speed_kmh: Optional[float] = None
    max_speed_kmh: Optional[float] = None
    battery_start_pct: Optional[float] = None
    battery_end_pct: Optional[float] = None
    alert_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
