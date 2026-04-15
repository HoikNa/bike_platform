from datetime import datetime, timezone, timedelta
import uuid
import random

from sqlmodel import Session, select
from sqlalchemy import func, desc
from chalicelib.models.vehicle import Vehicle, VehicleStatus
from chalicelib.models.sensor_data import SensorData
from chalicelib.models.alert import Alert
from chalicelib.models.trip import Trip
from chalicelib.models.driver_profile import DriverProfile
from chalicelib.schemas.vehicle import (
    VehicleRead, VehicleDetailRead, SensorStatusRead,
    DriverProfileRead, ActiveTripRead,
)
from chalicelib.core.password import get_password_hash
from chalicelib.core.exceptions import NotFoundException


def _build_vehicle_read(session: Session, vehicle: Vehicle) -> VehicleRead:
    """Vehicle ORM → VehicleRead (latest_sensor, driver, unacked count 포함)."""
    # 최신 센서 데이터
    latest_sd = session.exec(
        select(SensorData)
        .where(SensorData.vehicle_id == vehicle.id)
        .order_by(desc(SensorData.time))
        .limit(1)
    ).first()

    sensor = SensorStatusRead.model_validate(latest_sd) if latest_sd else None

    # 운전자 프로필
    driver = None
    if vehicle.assigned_driver_id:
        dp = session.get(DriverProfile, vehicle.assigned_driver_id)
        if dp:
            user = session.get(__import__("chalicelib.models.user", fromlist=["User"]).User, dp.user_id)
            driver_data = {
                "id": dp.id,
                "user_full_name": user.full_name if user else "알 수 없음",
                "license_number": dp.license_number,
                "license_expiry": dp.license_expiry,
                "phone": dp.phone,
                "emergency_contact": dp.emergency_contact,
            }
            driver = DriverProfileRead(**driver_data)

    # 미확인 알림 수
    unacked_count = session.exec(
        select(func.count(Alert.id))
        .where(Alert.vehicle_id == vehicle.id)
        .where(Alert.is_acknowledged == False)
    ).one()

    return VehicleRead(
        id=vehicle.id,
        plate_number=vehicle.plate_number,
        model=vehicle.model,
        manufacturer=vehicle.manufacturer,
        manufacture_year=vehicle.manufacture_year,
        status=vehicle.status,
        battery_capacity_kwh=vehicle.battery_capacity_kwh,
        vin=vehicle.vin,
        assigned_driver=driver,
        latest_sensor=sensor,
        unacknowledged_alerts_count=unacked_count,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )


class VehicleService:
    @staticmethod
    def list_vehicles(session: Session, limit: int = 50, offset: int = 0,
                      status_filter: list = None, q: str = None):
        stmt = select(Vehicle).where(Vehicle.deleted_at == None)

        if status_filter:
            stmt = stmt.where(Vehicle.status.in_(status_filter))
        if q:
            stmt = stmt.where(Vehicle.plate_number.ilike(f"%{q}%"))

        total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
        vehicles = session.exec(stmt.offset(offset).limit(limit)).all()
        data = [_build_vehicle_read(session, v) for v in vehicles]
        return data, total

    @staticmethod
    def get_vehicle_detail(session: Session, vehicle_id: str) -> VehicleDetailRead | None:
        vehicle = session.get(Vehicle, uuid.UUID(vehicle_id))
        if not vehicle or vehicle.deleted_at:
            return None

        base = _build_vehicle_read(session, vehicle)

        # 현재 진행 중인 운행 (ended_at = NULL)
        active_trip = session.exec(
            select(Trip)
            .where(Trip.vehicle_id == vehicle.id)
            .where(Trip.ended_at == None)
            .order_by(desc(Trip.started_at))
            .limit(1)
        ).first()

        active = None
        if active_trip:
            active = ActiveTripRead(
                id=active_trip.id,
                started_at=active_trip.started_at,
                start_address=active_trip.start_address,
            )

        return VehicleDetailRead(
            **base.model_dump(),
            active_trip=active,
        )

    @staticmethod
    def update_telemetry(session: Session, vehicle_id: str, payload: dict) -> dict:
        """시뮬레이터/IoT 단말기로부터 실시간 센서 데이터를 수신하여 저장합니다.

        Args:
            payload: {
                latitude, longitude, speed_kmh,
                battery_level_pct, engine_temp_celsius
            }
        """
        vehicle = session.get(Vehicle, uuid.UUID(vehicle_id))
        if not vehicle or vehicle.deleted_at:
            raise NotFoundException(f"Vehicle {vehicle_id} not found")

        speed = float(payload.get("speed_kmh", 0))

        # ── 차량 상태 업데이트 ────────────────────────────────────
        if speed > 0:
            vehicle.status = VehicleStatus.RUNNING
        else:
            vehicle.status = VehicleStatus.IDLE
        session.add(vehicle)

        # ── SensorData 삽입 (복합 PK 충돌 방지: 마이크로초 지터 추가) ──
        jitter = timedelta(microseconds=random.randint(0, 999))
        now = datetime.now(timezone.utc) + jitter

        sd = SensorData(
            time=now,
            vehicle_id=vehicle.id,
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
            speed_kmh=speed,
            battery_level_pct=payload.get("battery_level_pct"),
            battery_temp_celsius=payload.get("engine_temp_celsius"),  # 엔진 온도 재사용
        )
        session.add(sd)
        session.commit()

        return {
            "vehicle_id": str(vehicle.id),
            "status": vehicle.status,
            "recorded_at": now.isoformat(),
        }

    @staticmethod
    def seed_demo_vehicles_if_empty(session: Session):
        existing_count = session.exec(select(func.count(Vehicle.id))).one()
        if existing_count > 0:
            return 0

        statuses = [
            VehicleStatus.RUNNING, VehicleStatus.IDLE, VehicleStatus.CHARGING,
            VehicleStatus.RUNNING, VehicleStatus.RUNNING, VehicleStatus.OFFLINE,
            VehicleStatus.RUNNING, VehicleStatus.ALERT,
            VehicleStatus.RUNNING, VehicleStatus.IDLE,
        ]

        vehicles = []
        for idx in range(1, 11):
            plate = f"{10 + idx}가{3000 + idx}"
            vehicle = Vehicle(
                plate_number=plate,
                model="PCX Electric",
                manufacturer="Honda",
                manufacture_year=2023,
                status=statuses[idx - 1],
                battery_capacity_kwh=5.0,
            )
            session.add(vehicle)
            vehicles.append(vehicle)

        session.commit()
        return len(vehicles)
