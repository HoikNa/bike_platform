"""데모 데이터 시딩 서비스.

앱 최초 실행 시 driver_profiles, sensor_data, alerts, trips 를
현실적인 더미 데이터로 채웁니다.
"""

import random
from datetime import datetime, timedelta, timezone, date
from sqlmodel import Session, select
from sqlalchemy import func

from chalicelib.models.user import User, UserRole
from chalicelib.models.driver_profile import DriverProfile
from chalicelib.models.vehicle import Vehicle, VehicleStatus
from chalicelib.models.sensor_data import SensorData
from chalicelib.models.alert import Alert, AlertType, AlertSeverity
from chalicelib.models.trip import Trip
from chalicelib.core.password import get_password_hash


# ── 서울 성동구 반경 좌표 범위 ─────────────────────────────────
LAT_MIN, LAT_MAX = 37.530, 37.575
LNG_MIN, LNG_MAX = 127.015, 127.065

DRIVER_NAMES = [
    "김민수", "이서준", "박지훈", "최도윤", "정하늘",
    "윤지호", "강유진", "한지민",
]

ADDRESSES = [
    "서울 성동구 왕십리로 50", "서울 성동구 행당동 21-3", "서울 성동구 마장동 497",
    "서울 성동구 용답동 117", "서울 광진구 군자동 58", "서울 광진구 중곡동 300",
    "서울 중구 황학동 12", "서울 동대문구 장안동 20",
]

ALERT_TEMPLATES = [
    (AlertType.OVERSPEED,          AlertSeverity.WARNING, "과속 감지 — {speed:.0f} km/h",          "제한속도 초과 구간 주행 감지"),
    (AlertType.BATTERY_LOW,        AlertSeverity.WARNING, "배터리 부족 — {battery:.0f}%",           "배터리 잔량 30% 미만. 가까운 충전소를 확인하세요."),
    (AlertType.BATTERY_CRITICAL,   AlertSeverity.DANGER,  "배터리 위험 — {battery:.0f}%",           "배터리 잔량 10% 미만. 즉시 충전이 필요합니다."),
    (AlertType.GEOFENCE_EXIT,      AlertSeverity.WARNING, "운행 구역 이탈",                          "지정된 운행 구역을 벗어났습니다."),
    (AlertType.SUDDEN_ACCEL,       AlertSeverity.INFO,    "급가속 감지",                             "급가속이 감지되었습니다. 안전 운행을 권고합니다."),
    (AlertType.SUDDEN_BRAKE,       AlertSeverity.INFO,    "급감속 감지",                             "급감속이 감지되었습니다."),
    (AlertType.MAINTENANCE_DUE,    AlertSeverity.INFO,    "정비 권고",                               "누적 주행거리 5,000km 초과. 정기 점검을 권고합니다."),
    (AlertType.COMMUNICATION_LOST, AlertSeverity.DANGER,  "통신 두절",                               "차량과의 통신이 30분 이상 끊겼습니다."),
]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def rand_lat() -> float:
    return round(random.uniform(LAT_MIN, LAT_MAX), 6)


def rand_lng() -> float:
    return round(random.uniform(LNG_MIN, LNG_MAX), 6)


class SeedService:

    @staticmethod
    def seed_all(session: Session) -> None:
        """전체 데모 데이터 시딩 — 이미 존재하면 스킵."""
        SeedService._seed_driver_users(session)
        SeedService._seed_sensor_data(session)
        SeedService._seed_alerts(session)
        SeedService._seed_trips(session)

    # ── 1. 운전자 User + DriverProfile ────────────────────────
    @staticmethod
    def _seed_driver_users(session: Session) -> None:
        vehicles = session.exec(select(Vehicle)).all()
        if not vehicles:
            return

        for idx, vehicle in enumerate(vehicles):
            name = DRIVER_NAMES[idx % len(DRIVER_NAMES)]
            email = f"driver{idx + 1}@fms.io"

            existing_user = session.exec(select(User).where(User.email == email)).first()
            if existing_user:
                # 이미 DriverProfile 있으면 배차만 확인
                dp = session.exec(
                    select(DriverProfile).where(DriverProfile.user_id == existing_user.id)
                ).first()
                if dp and not vehicle.assigned_driver_id:
                    vehicle.assigned_driver_id = dp.id
                continue

            user = User(
                email=email,
                hashed_password=get_password_hash("driver123"),
                full_name=name,
                role=UserRole.DRIVER,
            )
            session.add(user)
            session.flush()  # id 확보

            dp = DriverProfile(
                user_id=user.id,
                license_number=f"12-{10 + idx}-{100000 + idx * 7}",
                license_expiry=date(2027, (idx % 12) + 1, 15),
                phone=f"010-{1000 + idx * 13:04d}-{2000 + idx * 7:04d}",
                emergency_contact=f"010-{3000 + idx * 11:04d}-{4000 + idx * 3:04d}",
            )
            session.add(dp)
            session.flush()

            vehicle.assigned_driver_id = dp.id

        session.commit()

    # ── 2. SensorData (최근 1시간 × 5분 간격 × 차량별) ────────
    @staticmethod
    def _seed_sensor_data(session: Session) -> None:
        existing = session.exec(select(func.count()).select_from(SensorData)).one()
        if existing > 0:
            return

        vehicles = session.exec(select(Vehicle)).all()
        now = utcnow()
        rows = []

        for vehicle in vehicles:
            lat = rand_lat()
            lng = rand_lng()
            battery = random.uniform(20, 95)
            odometer = random.uniform(500, 8000)

            for minutes_ago in range(60, -1, -5):  # 60분 전 → 현재
                t = now - timedelta(minutes=minutes_ago)
                is_running = vehicle.status in (VehicleStatus.RUNNING, VehicleStatus.ALERT)

                if is_running:
                    lat += random.uniform(-0.001, 0.001)
                    lng += random.uniform(-0.001, 0.001)
                    speed = round(random.uniform(15, 65), 1)
                    odometer += random.uniform(0.05, 0.15)
                    battery = max(5, battery - random.uniform(0, 0.3))
                elif vehicle.status == VehicleStatus.CHARGING:
                    speed = 0.0
                    battery = min(100, battery + random.uniform(0, 1.5))
                else:
                    speed = 0.0
                    battery = max(5, battery - random.uniform(0, 0.05))

                sd = SensorData(
                    time=t,
                    vehicle_id=vehicle.id,
                    latitude=round(lat, 6),
                    longitude=round(lng, 6),
                    speed_kmh=speed if is_running else 0.0,
                    battery_level_pct=round(battery, 1),
                    battery_voltage_v=round(48.0 + battery * 0.05, 2),
                    battery_current_a=round(-2.5 if is_running else (5.0 if vehicle.status == VehicleStatus.CHARGING else 0.0), 2),
                    battery_temp_celsius=round(25 + random.uniform(-3, 8), 1),
                    engine_rpm=int(speed * 25) if is_running else 0,
                    odometer_km=round(odometer, 2),
                    signal_strength_dbm=random.randint(-90, -60),
                )
                rows.append(sd)

        for row in rows:
            session.add(row)
        session.commit()

    # ── 3. Alerts (차량별 2-5개, 최근 24시간) ─────────────────
    @staticmethod
    def _seed_alerts(session: Session) -> None:
        existing = session.exec(select(func.count()).select_from(Alert)).one()
        if existing > 0:
            return

        vehicles = session.exec(select(Vehicle)).all()
        now = utcnow()

        for vehicle in vehicles:
            num_alerts = random.randint(2, 5)
            for _ in range(num_alerts):
                tpl = random.choice(ALERT_TEMPLATES)
                a_type, severity, title_fmt, desc = tpl
                hours_ago = random.uniform(0.2, 23)
                speed = round(random.uniform(82, 105), 1)
                battery = round(random.uniform(5, 28), 1)

                title = title_fmt.format(speed=speed, battery=battery)

                alert = Alert(
                    vehicle_id=vehicle.id,
                    triggered_at=now - timedelta(hours=hours_ago),
                    alert_type=a_type,
                    severity=severity,
                    title=title,
                    description=desc,
                    speed_at_trigger=speed if a_type == AlertType.OVERSPEED else None,
                    battery_at_trigger=battery if a_type in (AlertType.BATTERY_LOW, AlertType.BATTERY_CRITICAL) else None,
                    location_lat=rand_lat(),
                    location_lng=rand_lng(),
                    is_acknowledged=random.random() < 0.4,
                )
                session.add(alert)

        session.commit()

    # ── 4. Trips (차량별 3-8건, 최근 7일) ─────────────────────
    @staticmethod
    def _seed_trips(session: Session) -> None:
        existing = session.exec(select(func.count()).select_from(Trip)).one()
        if existing > 0:
            return

        vehicles = session.exec(select(Vehicle)).all()
        now = utcnow()

        for vehicle in vehicles:
            dp = None
            if vehicle.assigned_driver_id:
                dp = session.get(DriverProfile, vehicle.assigned_driver_id)

            num_trips = random.randint(3, 8)
            cursor = now - timedelta(days=7)

            for _ in range(num_trips):
                start_offset = random.uniform(0.5, 4)
                duration_h = random.uniform(0.3, 2.5)
                started = cursor + timedelta(hours=start_offset)
                ended = started + timedelta(hours=duration_h)

                if ended > now:
                    break  # 미래 trip 생성 방지

                distance = round(duration_h * random.uniform(10, 30), 2)
                avg_spd = round(random.uniform(20, 50), 1)
                max_spd = round(avg_spd + random.uniform(10, 30), 1)
                bat_start = round(random.uniform(40, 95), 1)
                bat_end = round(max(5, bat_start - distance * 0.5), 1)
                n_alerts = random.randint(0, 3)

                # 현재 운행 중인 차량 중 하나는 active trip (ended_at=None)
                is_active = (
                    vehicle.status == VehicleStatus.RUNNING
                    and _ == num_trips - 1
                    and (now - started).total_seconds() < 7200
                )

                trip = Trip(
                    vehicle_id=vehicle.id,
                    driver_id=dp.id if dp else None,
                    started_at=started,
                    ended_at=None if is_active else ended,
                    start_address=random.choice(ADDRESSES),
                    end_address=None if is_active else random.choice(ADDRESSES),
                    distance_km=None if is_active else distance,
                    avg_speed_kmh=None if is_active else avg_spd,
                    max_speed_kmh=None if is_active else max_spd,
                    battery_start_pct=bat_start,
                    battery_end_pct=None if is_active else bat_end,
                    alert_count=n_alerts,
                )
                session.add(trip)
                cursor = ended

        session.commit()
