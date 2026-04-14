"""Alert service functions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from sqlalchemy import func
from sqlmodel import Session, select

from chalicelib.models import Alert, AlertCreate, AlertRead


def list_alerts(
    session: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    sort: str = "timestamp",
    order: str = "desc",
) -> List[AlertRead]:
    """Return alerts with pagination and sorting."""

    sort_column = Alert.timestamp if sort == "timestamp" else Alert.id
    order_by_clause = sort_column.desc() if order == "desc" else sort_column.asc()
    alerts = session.exec(select(Alert).order_by(order_by_clause).offset(offset).limit(limit)).all()
    return [AlertRead.model_validate(a) for a in alerts]


def count_alerts(session: Session) -> int:
    """Return total number of alerts."""

    total = session.exec(select(func.count()).select_from(Alert)).one()
    return int(total)


def create_alert(session: Session, payload: AlertCreate) -> AlertRead:
    """Create a new alert and return it."""

    alert = Alert(
        vehicle_id=payload.vehicle_id,
        type=payload.type,
        message=payload.message,
        timestamp=datetime.now(timezone.utc),
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return AlertRead.model_validate(alert)

