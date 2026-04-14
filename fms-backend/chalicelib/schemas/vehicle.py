from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID


class SensorStatusRead(BaseModel):
    time: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    speed_kmh: Optional[float] = None
    battery_level_pct: Optional[float] = None
    battery_voltage_v: Optional[float] = None
    battery_temp_celsius: Optional[float] = None
    engine_rpm: Optional[int] = None
    odometer_km: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


class DriverProfileRead(BaseModel):
    id: UUID
    user_full_name: str
    license_number: str
    license_expiry: date
    phone: str
    emergency_contact: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ActiveTripRead(BaseModel):
    id: UUID
    started_at: datetime
    start_address: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class VehicleRead(BaseModel):
    id: UUID
    plate_number: str
    model: str
    manufacturer: str
    manufacture_year: int
    status: str
    battery_capacity_kwh: float
    vin: Optional[str] = None
    assigned_driver: Optional[DriverProfileRead] = None
    latest_sensor: Optional[SensorStatusRead] = None
    unacknowledged_alerts_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VehicleDetailRead(VehicleRead):
    active_trip: Optional[ActiveTripRead] = None
