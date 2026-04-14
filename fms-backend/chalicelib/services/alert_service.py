import base64
import uuid
from datetime import datetime, timezone
from sqlmodel import Session, select
from sqlalchemy import func, desc
from chalicelib.models.alert import Alert
from chalicelib.models.vehicle import Vehicle
from chalicelib.models.user import User
from chalicelib.schemas.alert import AlertRead, VehicleRef, AcknowledgerRef
from chalicelib.core.exceptions import NotFoundException


def _encode_cursor(triggered_at: datetime, alert_id: uuid.UUID) -> str:
    raw = f"{triggered_at.isoformat()}|{alert_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    ts_str, id_str = raw.split("|", 1)
    return datetime.fromisoformat(ts_str), uuid.UUID(id_str)


def _build_alert_read(session: Session, alert: Alert) -> AlertRead:
    vehicle = session.get(Vehicle, alert.vehicle_id)
    vehicle_ref = VehicleRef(
        id=vehicle.id,
        plate_number=vehicle.plate_number,
    ) if vehicle else None

    acknowledger_ref = None
    if alert.acknowledged_by_id:
        user = session.get(User, alert.acknowledged_by_id)
        if user:
            acknowledger_ref = AcknowledgerRef(id=user.id, full_name=user.full_name)

    return AlertRead(
        id=alert.id,
        vehicle=vehicle_ref,
        triggered_at=alert.triggered_at,
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        description=alert.description,
        speed_at_trigger=alert.speed_at_trigger,
        battery_at_trigger=alert.battery_at_trigger,
        location_lat=alert.location_lat,
        location_lng=alert.location_lng,
        is_acknowledged=alert.is_acknowledged,
        acknowledged_by=acknowledger_ref,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at,
    )


class AlertService:
    @staticmethod
    def list_alerts(
        session: Session,
        limit: int = 30,
        cursor: str | None = None,
        vehicle_id: str | None = None,
        severity: list[str] | None = None,
        is_acknowledged: bool | None = None,
    ) -> tuple[list[AlertRead], str | None, bool]:
        stmt = select(Alert)

        if vehicle_id:
            stmt = stmt.where(Alert.vehicle_id == uuid.UUID(vehicle_id))
        if severity:
            stmt = stmt.where(Alert.severity.in_(severity))
        if is_acknowledged is not None:
            stmt = stmt.where(Alert.is_acknowledged == is_acknowledged)

        if cursor:
            ts, aid = _decode_cursor(cursor)
            stmt = stmt.where(
                (Alert.triggered_at < ts) |
                ((Alert.triggered_at == ts) & (Alert.id < aid))
            )

        stmt = stmt.order_by(desc(Alert.triggered_at), desc(Alert.id)).limit(limit + 1)
        rows = session.exec(stmt).all()

        has_next = len(rows) > limit
        rows = rows[:limit]

        next_cursor = None
        if has_next and rows:
            last = rows[-1]
            next_cursor = _encode_cursor(last.triggered_at, last.id)

        data = [_build_alert_read(session, a) for a in rows]
        return data, next_cursor, has_next

    @staticmethod
    def acknowledge(session: Session, alert_id: str, user_id: str) -> AlertRead:
        alert = session.get(Alert, uuid.UUID(alert_id))
        if not alert:
            raise NotFoundException("Alert not found")

        alert.is_acknowledged = True
        alert.acknowledged_by_id = uuid.UUID(user_id)
        alert.acknowledged_at = datetime.now(timezone.utc)
        session.add(alert)
        session.commit()
        session.refresh(alert)
        return _build_alert_read(session, alert)
