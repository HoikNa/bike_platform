import math
import uuid
from sqlmodel import Session, select
from sqlalchemy import func, desc
from chalicelib.models.trip import Trip
from chalicelib.models.vehicle import Vehicle
from chalicelib.models.driver_profile import DriverProfile
from chalicelib.models.user import User
from chalicelib.schemas.trip import TripRead, VehicleRef, DriverRef


def _build_trip_read(session: Session, trip: Trip) -> TripRead:
    vehicle = session.get(Vehicle, trip.vehicle_id)
    vehicle_ref = VehicleRef(id=vehicle.id, plate_number=vehicle.plate_number) if vehicle else None

    driver_ref = None
    if trip.driver_id:
        dp = session.get(DriverProfile, trip.driver_id)
        if dp:
            user = session.get(User, dp.user_id)
            driver_ref = DriverRef(
                id=dp.id,
                user_full_name=user.full_name if user else "알 수 없음",
            )

    return TripRead(
        id=trip.id,
        vehicle=vehicle_ref,
        driver=driver_ref,
        started_at=trip.started_at,
        ended_at=trip.ended_at,
        start_address=trip.start_address,
        end_address=trip.end_address,
        distance_km=trip.distance_km,
        avg_speed_kmh=trip.avg_speed_kmh,
        max_speed_kmh=trip.max_speed_kmh,
        battery_start_pct=trip.battery_start_pct,
        battery_end_pct=trip.battery_end_pct,
        alert_count=trip.alert_count,
        created_at=trip.created_at,
    )


class TripService:
    @staticmethod
    def list_trips(
        session: Session,
        page: int = 1,
        page_size: int = 20,
        vehicle_id: str | None = None,
        driver_id: str | None = None,
    ) -> tuple[list[TripRead], dict]:
        stmt = select(Trip)

        if vehicle_id:
            stmt = stmt.where(Trip.vehicle_id == uuid.UUID(vehicle_id))
        if driver_id:
            stmt = stmt.where(Trip.driver_id == uuid.UUID(driver_id))

        total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
        offset = (page - 1) * page_size

        trips = session.exec(
            stmt.order_by(desc(Trip.started_at)).offset(offset).limit(page_size)
        ).all()

        data = [_build_trip_read(session, t) for t in trips]
        total_pages = math.ceil(total / page_size) if page_size else 1

        meta = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
        return data, meta
