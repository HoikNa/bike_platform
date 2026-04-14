"""SQLModel models and response schemas for the FMS backend.

This module contains the core database tables and the Pydantic/SQLModel schemas
used by API responses.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Vehicle(SQLModel, table=True):
    """Vehicle master table.

    Attributes:
        id: Primary key.
        plate_number: Unique plate number identifier.
        status: Operational status (e.g., RUNNING/IDLE/OFFLINE).
        driver_name: Current driver name (optional).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    plate_number: str = Field(index=True, nullable=False, unique=True, max_length=32)
    status: str = Field(default="UNKNOWN", nullable=False, max_length=32)
    driver_name: Optional[str] = Field(default=None, max_length=64)

    alerts: list["Alert"] = Relationship(back_populates="vehicle")
    sensor_statuses: list["SensorStatus"] = Relationship(back_populates="vehicle")


class Alert(SQLModel, table=True):
    """Event alert table.

    Attributes:
        id: Primary key.
        vehicle_id: Foreign key to Vehicle.
        type: Alert category (e.g., DANGER/WARNING/INFO).
        message: Human-readable description.
        timestamp: Event timestamp (UTC).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    vehicle_id: int = Field(foreign_key="vehicle.id", index=True, nullable=False)
    type: str = Field(nullable=False, max_length=32)
    message: str = Field(nullable=False, max_length=512)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    vehicle: Optional["Vehicle"] = Relationship(back_populates="alerts")


class SensorStatus(SQLModel, table=True):
    """Periodic sensor status for each vehicle."""

    id: Optional[int] = Field(default=None, primary_key=True)
    vehicle_id: int = Field(foreign_key="vehicle.id", index=True, nullable=False)
    battery_level: float = Field(nullable=False, ge=0, le=100)
    engine_temperature: float = Field(nullable=False)
    speed: float = Field(nullable=False, ge=0)
    latitude: float = Field(nullable=False)
    longitude: float = Field(nullable=False)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    vehicle: Optional["Vehicle"] = Relationship(back_populates="sensor_statuses")


class SensorStatusRead(SQLModel):
    """Read schema for latest vehicle sensor status."""

    battery_level: float
    engine_temperature: float
    speed: float
    latitude: float
    longitude: float
    timestamp: datetime


class VehicleCreate(SQLModel):
    """Create schema for Vehicle (API request body)."""

    plate_number: str
    status: str = "IDLE"
    driver_name: Optional[str] = None


class VehicleRead(SQLModel):
    """Read schema for Vehicle (API response)."""

    id: int
    plate_number: str
    status: str
    driver_name: Optional[str]


class VehicleDetailRead(VehicleRead):
    """Vehicle detail response with latest sensor status."""

    latest_sensor_status: Optional[SensorStatusRead] = None


class AlertRead(SQLModel):
    """Read schema for Alert (API response)."""

    id: int
    vehicle_id: int
    type: str
    message: str
    timestamp: datetime


class AlertCreate(SQLModel):
    """Create schema for Alert (API request body)."""

    vehicle_id: int
    type: str
    message: str

