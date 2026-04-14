from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class VehicleRef(BaseModel):
    id: UUID
    plate_number: str
    model_config = ConfigDict(from_attributes=True)


class AcknowledgerRef(BaseModel):
    id: UUID
    full_name: str
    model_config = ConfigDict(from_attributes=True)


class AlertRead(BaseModel):
    id: UUID
    vehicle: VehicleRef
    triggered_at: datetime
    alert_type: str
    severity: str
    title: str
    description: Optional[str] = None
    speed_at_trigger: Optional[float] = None
    battery_at_trigger: Optional[float] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    is_acknowledged: bool
    acknowledged_by: Optional[AcknowledgerRef] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
