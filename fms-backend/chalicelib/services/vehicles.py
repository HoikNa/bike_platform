"""Vehicle service functions."""

from __future__ import annotations

from datetime import datetime, timezone
from random import choice, randint, uniform
from typing import List, Optional, Tuple

from sqlmodel import Session, select
from sqlalchemy import func

from chalicelib.models import (
    SensorStatus,
    SensorStatusRead,
    Vehicle,
    VehicleCreate,
    VehicleDetailRead,
    VehicleRead,
)


SEOUL_POINTS: List[tuple[float, float]] = [
    (37.5665, 126.9780),
    (37.5700, 126.9920),
    (37.5570, 126.9240),
    (37.5796, 126.9770),
    (37.5512, 127.0910),
    (37.4979, 127.0276),
    (37.5340, 126.9946),
    (37.5150, 127.1020),
]


def list_vehicles(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    sort: str = "id",
    order: str = "asc",
) -> List[VehicleRead]:
    """Return vehicles with pagination and sorting."""

    sort_column = Vehicle.id if sort == "id" else Vehicle.plate_number
    order_by_clause = sort_column.desc() if order == "desc" else sort_column.asc()
    vehicles = session.exec(select(Vehicle).order_by(order_by_clause).offset(offset).limit(limit)).all()
    return [VehicleRead.model_validate(v) for v in vehicles]


def count_vehicles(session: Session) -> int:
    """Return total number of vehicles."""

    total = session.exec(select(func.count()).select_from(Vehicle)).one()
    return int(total)


def create_vehicle(session: Session, payload: VehicleCreate) -> VehicleRead:
    """Create vehicle with one initial sensor-status row in one transaction."""

    vehicle = Vehicle(**payload.model_dump())
    session.add(vehicle)
    session.flush()

    seed_lat, seed_lng = choice(SEOUL_POINTS)
    initial_sensor = SensorStatus(
        vehicle_id=vehicle.id or 0,
        battery_level=100.0,
        engine_temperature=25.0,
        speed=0.0,
        latitude=seed_lat,
        longitude=seed_lng,
        timestamp=datetime.now(timezone.utc),
    )
    session.add(initial_sensor)
    session.commit()
    session.refresh(vehicle)
    return VehicleRead.model_validate(vehicle)


def get_vehicle_by_id(session: Session, vehicle_id: int) -> Optional[VehicleDetailRead]:
    """Return vehicle detail with latest sensor status, or None."""

    vehicle = session.get(Vehicle, vehicle_id)
    if vehicle is None:
        return None

    latest_sensor = session.exec(
        select(SensorStatus)
        .where(SensorStatus.vehicle_id == vehicle_id)
        .order_by(SensorStatus.timestamp.desc())
        .limit(1)
    ).first()

    latest_sensor_read = (
        SensorStatusRead.model_validate(latest_sensor) if latest_sensor else None
    )
    return VehicleDetailRead(
        **VehicleRead.model_validate(vehicle).model_dump(),
        latest_sensor_status=latest_sensor_read,
    )


def seed_demo_vehicles_if_empty(session: Session) -> Tuple[int, int]:
    """Seed demo vehicles and sensor statuses when DB is empty.

    Returns:
        (vehicle_count, sensor_status_count) inserted in this call.
    """

    existing_count = len(session.exec(select(Vehicle.id)).all())
    if existing_count > 0:
        return (0, 0)

    drivers = ["김민수", "이서준", "박지훈", "최도윤", "정하늘", "윤지호", "강유진", "한지민"]
    statuses = ["RUNNING", "IDLE", "CHARGING", "DELIVERING"]
    vehicles: List[Vehicle] = []
    sensor_rows: List[SensorStatus] = []

    for idx, _ in enumerate(SEOUL_POINTS, start=1):
        plate = f"{10 + idx}가{3000 + idx}"
        vehicle = Vehicle(
            plate_number=plate,
            status=statuses[idx % len(statuses)],
            driver_name=drivers[idx - 1],
        )
        vehicles.append(vehicle)
        session.add(vehicle)

    session.flush()

    for vehicle, (lat, lng) in zip(vehicles, SEOUL_POINTS):
        sensor = SensorStatus(
            vehicle_id=vehicle.id or 0,
            battery_level=round(uniform(35, 98), 1),
            engine_temperature=round(uniform(68, 102), 1),
            speed=float(randint(0, 75)),
            latitude=lat,
            longitude=lng,
            timestamp=datetime.now(timezone.utc),
        )
        sensor_rows.append(sensor)
        session.add(sensor)

    session.commit()
    return (len(vehicles), len(sensor_rows))

