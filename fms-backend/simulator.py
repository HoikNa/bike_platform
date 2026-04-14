#!/usr/bin/env python3
"""
BikeFMS 오토바이 실시간 주행 시뮬레이터
========================================
서울 강남구 테헤란로 일대에서 오토바이 N대가 실제로 주행하는 것처럼
센서 데이터를 백엔드 API로 전송합니다.

실행 방법:
    pip install aiohttp
    python simulator.py

옵션 (환경 변수):
    SIM_BASE_URL    백엔드 URL (기본: http://localhost:8000)
    SIM_EMAIL       로그인 이메일 (기본: admin@fms.com)
    SIM_PASSWORD    로그인 비밀번호 (기본: admin1234)
    SIM_TICK_SECS   틱 간격 초 (기본: 1.5)
"""

import asyncio
import aiohttp
import math
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ── 설정 ─────────────────────────────────────────────────────────────────────
BASE_URL      = os.getenv("SIM_BASE_URL",  "http://localhost:8000")
ADMIN_EMAIL   = os.getenv("SIM_EMAIL",     "admin@fms.com")
ADMIN_PASSWORD= os.getenv("SIM_PASSWORD",  "admin1234")
TICK_SECS     = float(os.getenv("SIM_TICK_SECS", "1.5"))

OVERSPEED_KMH    = 80.0   # 과속 기준 (km/h)
LOW_BATTERY_PCT  = 20.0   # 배터리 경고 기준 (%)
ALERT_COOLDOWN_S = 30.0   # 같은 알림 재발생 방지 쿨다운 (초)

# 서울 강남구 테헤란로 중심 좌표
CENTER_LAT = 37.5012
CENTER_LNG = 127.0396
ROAMING_RADIUS = 0.018    # 이동 반경 (~2 km)

# ── ANSI 컬러 ─────────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    GRAY   = "\033[90m"

# ── 차량 상태 ─────────────────────────────────────────────────────────────────
@dataclass
class VehicleState:
    vehicle_id:   str
    plate_number: str
    index:        int           # 1-based 로그 인덱스

    # GPS
    lat:     float
    lng:     float
    heading: float              # 라디안 (나침반 기준: 0=North, π/2=East)

    # 주행
    speed_kmh:    float = 20.0
    target_speed: float = 20.0  # 서서히 수렴할 목표 속도
    engine_temp:  float = 65.0  # °C

    # 배터리 (일부 차량은 낮게 시작해 곧 경고 트리거)
    battery_pct: float = field(default_factory=lambda: random.uniform(60.0, 100.0))

    # 목표 속도 재설정 카운터
    speed_change_in: int = field(default_factory=lambda: random.randint(5, 20))

    # 알림 쿨다운
    overspeed_cooldown_until: float = 0.0
    low_battery_alerted:      bool  = False

    # 통계
    ticks:          int   = 0
    alerts_sent:    int   = 0
    telemetry_sent: int   = 0

# ── 로그 헬퍼 ─────────────────────────────────────────────────────────────────
def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")

def log_info(vehicle: VehicleState, msg: str) -> None:
    print(
        f"{C.GRAY}[{ts()}]{C.RESET} "
        f"{C.CYAN}🏍  [{vehicle.index:02d}]{C.RESET} "
        f"{C.WHITE}{vehicle.plate_number}{C.RESET}  {msg}"
    )

def log_alert(vehicle: VehicleState, msg: str) -> None:
    print(
        f"{C.GRAY}[{ts()}]{C.RESET} "
        f"{C.RED}{C.BOLD}⚠   [{vehicle.index:02d}]{C.RESET} "
        f"{C.WHITE}{vehicle.plate_number}{C.RESET}  {C.YELLOW}{msg}{C.RESET}"
    )

def log_system(msg: str, color: str = C.GREEN) -> None:
    print(f"{C.GRAY}[{ts()}]{C.RESET} {color}{C.BOLD}{msg}{C.RESET}")

# ── 물리 시뮬레이션 ───────────────────────────────────────────────────────────
def tick_vehicle(v: VehicleState) -> None:
    """차량 상태를 TICK_SECS만큼 진행합니다."""
    v.ticks += 1

    # ── 목표 속도 재설정 ─────────────────────────────────────
    v.speed_change_in -= 1
    if v.speed_change_in <= 0:
        # 가끔(10% 확률) 과속 구간 연출
        if random.random() < 0.10:
            v.target_speed = random.uniform(82.0, 95.0)
        else:
            v.target_speed = random.uniform(0.0, 75.0)
        v.speed_change_in = random.randint(8, 25)

    # ── 속도 수렴 (가속도 반영) ───────────────────────────────
    accel = random.uniform(2.0, 6.0)   # km/h per tick
    if v.speed_kmh < v.target_speed:
        v.speed_kmh = min(v.speed_kmh + accel, v.target_speed)
    else:
        v.speed_kmh = max(v.speed_kmh - accel, v.target_speed)
    v.speed_kmh = max(0.0, v.speed_kmh)

    # ── 엔진 온도 (속도에 비례, 서서히 변화) ─────────────────
    target_temp = 55.0 + v.speed_kmh * 0.7
    v.engine_temp += (target_temp - v.engine_temp) * 0.08
    v.engine_temp = round(v.engine_temp, 1)

    # ── 방향 전환 (자연스러운 코너링) ────────────────────────
    v.heading += random.uniform(-0.20, 0.20)

    # 중심에서 너무 멀어지면 중심 방향으로 부드럽게 회전
    dlat = CENTER_LAT - v.lat
    dlng = CENTER_LNG - v.lng
    dist = math.sqrt(dlat**2 + (dlng * math.cos(math.radians(v.lat)))**2)
    if dist > ROAMING_RADIUS:
        toward_center = math.atan2(dlng, dlat)   # 나침반 heading
        diff = (toward_center - v.heading + math.pi) % (2 * math.pi) - math.pi
        v.heading += diff * 0.15

    # ── 위치 갱신 ────────────────────────────────────────────
    # 1 도 위도 ≈ 111,000 m  |  1 도 경도 ≈ 111,000 × cos(lat) m
    dist_m = v.speed_kmh * 1000 / 3600 * TICK_SECS
    v.lat += math.cos(v.heading) * dist_m / 111_000
    v.lng += math.sin(v.heading) * dist_m / (111_000 * math.cos(math.radians(v.lat)))

    # ── 배터리 감소 ──────────────────────────────────────────
    drain = 0.02 + (v.speed_kmh / 60.0) * 0.03   # %/tick
    v.battery_pct = max(0.0, v.battery_pct - drain)

# ── API 호출 ──────────────────────────────────────────────────────────────────
async def login(session: aiohttp.ClientSession) -> str:
    """POST /auth/login → access_token 반환"""
    url = f"{BASE_URL}/auth/login"
    async with session.post(url, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise RuntimeError(f"로그인 실패 ({resp.status}): {text}")
        data = await resp.json()
        token = data["data"]["access_token"]
        log_system(f"🔑  {ADMIN_EMAIL} 로그인 성공", C.GREEN)
        return token


async def fetch_vehicles(session: aiohttp.ClientSession, token: str) -> list[dict]:
    """GET /vehicles → 차량 목록 반환"""
    url = f"{BASE_URL}/vehicles"
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(url, headers=headers, params={"page_size": 100}) as resp:
        if resp.status != 200:
            text = await resp.text()
            raise RuntimeError(f"차량 목록 조회 실패 ({resp.status}): {text}")
        data = await resp.json()
        vehicles = data["data"]
        log_system(f"📡  차량 {len(vehicles)}대 로드 완료", C.GREEN)
        return vehicles


async def send_telemetry(
    session: aiohttp.ClientSession,
    v: VehicleState,
    token: str,
) -> bool:
    """PUT /vehicles/{id}/telemetry"""
    url = f"{BASE_URL}/vehicles/{v.vehicle_id}/telemetry"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "latitude":           round(v.lat, 6),
        "longitude":          round(v.lng, 6),
        "speed_kmh":          round(v.speed_kmh, 1),
        "battery_level_pct":  round(v.battery_pct, 1),
        "engine_temp_celsius": round(v.engine_temp, 1),
    }
    try:
        async with session.put(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                v.telemetry_sent += 1
                return True
            else:
                text = await resp.text()
                log_info(v, f"{C.RED}telemetry 오류 {resp.status}: {text[:80]}{C.RESET}")
                return False
    except Exception as e:
        log_info(v, f"{C.RED}telemetry 전송 실패: {e}{C.RESET}")
        return False


async def send_alert(
    session: aiohttp.ClientSession,
    v: VehicleState,
    token: str,
    alert_type: str,
    severity: str,
    title: str,
    description: str = "",
) -> None:
    """POST /alerts"""
    url = f"{BASE_URL}/alerts"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "vehicle_id":          v.vehicle_id,
        "alert_type":          alert_type,
        "severity":            severity,
        "title":               title,
        "description":         description,
        "speed_at_trigger":    round(v.speed_kmh, 1),
        "battery_at_trigger":  round(v.battery_pct, 1),
        "location_lat":        round(v.lat, 6),
        "location_lng":        round(v.lng, 6),
    }
    try:
        async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 201:
                v.alerts_sent += 1
                log_alert(v, f"{title}  →  알림 전송 완료 ✓")
            else:
                text = await resp.text()
                log_alert(v, f"알림 전송 실패 {resp.status}: {text[:80]}")
    except Exception as e:
        log_alert(v, f"알림 전송 예외: {e}")


# ── 차량별 시뮬레이션 루프 ────────────────────────────────────────────────────
async def simulate_vehicle(v: VehicleState, token: str) -> None:
    """하나의 차량을 독립적으로 시뮬레이션합니다."""
    connector = aiohttp.TCPConnector(limit=2)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            tick_start = asyncio.get_event_loop().time()

            # ── 물리 계산 ──────────────────────────────────
            tick_vehicle(v)

            # ── 텔레메트리 전송 ────────────────────────────
            ok = await send_telemetry(session, v, token)

            # ── 로그 출력 (5틱마다) ────────────────────────
            if ok and v.ticks % 5 == 0:
                bat_color = (
                    C.RED    if v.battery_pct < 20 else
                    C.YELLOW if v.battery_pct < 40 else
                    C.GREEN
                )
                spd_color = C.RED if v.speed_kmh > OVERSPEED_KMH else C.WHITE
                log_info(
                    v,
                    f"{spd_color}{v.speed_kmh:5.1f} km/h{C.RESET}"
                    f"  {C.GRAY}│{C.RESET}"
                    f"  배터리 {bat_color}{v.battery_pct:5.1f}%{C.RESET}"
                    f"  {C.GRAY}│{C.RESET}"
                    f"  🌡  {v.engine_temp:4.0f}°C"
                    f"  {C.GRAY}│{C.RESET}"
                    f"  {C.MAGENTA}{v.lat:.4f}, {v.lng:.4f}{C.RESET}"
                )

            # ── 과속 알림 ──────────────────────────────────
            now = time.monotonic()
            if v.speed_kmh > OVERSPEED_KMH and now > v.overspeed_cooldown_until:
                v.overspeed_cooldown_until = now + ALERT_COOLDOWN_S
                await send_alert(
                    session, v, token,
                    alert_type  = "OVERSPEED",
                    severity    = "DANGER",
                    title       = f"[{v.plate_number}] 과속 감지 — {v.speed_kmh:.0f} km/h",
                    description = f"제한 속도({OVERSPEED_KMH:.0f} km/h)를 {v.speed_kmh - OVERSPEED_KMH:.0f} km/h 초과했습니다.",
                )

            # ── 배터리 경고 (20% 최초 1회) ─────────────────
            if v.battery_pct < LOW_BATTERY_PCT and not v.low_battery_alerted:
                v.low_battery_alerted = True
                await send_alert(
                    session, v, token,
                    alert_type  = "BATTERY_LOW",
                    severity    = "WARNING",
                    title       = f"[{v.plate_number}] 배터리 교체 권고 — {v.battery_pct:.1f}%",
                    description = f"배터리 잔량이 {v.battery_pct:.1f}%로 교체 권고 수준({LOW_BATTERY_PCT:.0f}%) 이하입니다.",
                )

            # ── 배터리 위험 (10% 최초 1회) ─────────────────
            if v.battery_pct < 10.0 and not hasattr(v, "_critical_alerted"):
                v._critical_alerted = True  # type: ignore[attr-defined]
                await send_alert(
                    session, v, token,
                    alert_type  = "BATTERY_CRITICAL",
                    severity    = "DANGER",
                    title       = f"[{v.plate_number}] 배터리 위험 — {v.battery_pct:.1f}%",
                    description = f"배터리 잔량이 {v.battery_pct:.1f}%로 위험 수준입니다. 즉시 충전이 필요합니다.",
                )

            # ── 틱 간격 유지 ───────────────────────────────
            elapsed  = asyncio.get_event_loop().time() - tick_start
            sleep_for = max(0.0, TICK_SECS - elapsed)
            await asyncio.sleep(sleep_for)


# ── 메인 ─────────────────────────────────────────────────────────────────────
def print_banner(vehicle_count: int) -> None:
    w = 64
    print(f"\n{C.CYAN}{'═' * w}{C.RESET}")
    print(f"{C.CYAN}  {C.BOLD}🏍  BikeFMS 주행 시뮬레이터  v1.0{C.RESET}")
    print(f"{C.CYAN}  대상: 서울 강남구 테헤란로 일대  │  차량 수: {vehicle_count}대{C.RESET}")
    print(f"{C.CYAN}  서버: {BASE_URL}  │  틱: {TICK_SECS}s{C.RESET}")
    print(f"{C.CYAN}{'═' * w}{C.RESET}\n")


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        # 1. 로그인
        token = await login(session)

        # 2. 차량 목록 조회
        vehicles_data = await fetch_vehicles(session, token)

    if not vehicles_data:
        print(f"{C.RED}차량 데이터가 없습니다. 백엔드가 정상 실행 중인지 확인하세요.{C.RESET}")
        return

    print_banner(len(vehicles_data))

    # 3. VehicleState 초기화
    states: list[VehicleState] = []
    for idx, v in enumerate(vehicles_data, start=1):
        # 최신 센서 위치가 있으면 그 위치에서 시작, 없으면 중심 근처 랜덤
        sensor = v.get("latest_sensor") or {}
        init_lat = sensor.get("latitude") or CENTER_LAT + random.uniform(-ROAMING_RADIUS, ROAMING_RADIUS)
        init_lng = sensor.get("longitude") or CENTER_LNG + random.uniform(-ROAMING_RADIUS, ROAMING_RADIUS)

        # 일부 차량은 배터리를 낮게 시작해 경고 빠르게 트리거
        if idx <= 2:
            init_battery = random.uniform(21.0, 30.0)   # 수분 내 LOW 알림 발생
        else:
            init_battery = random.uniform(55.0, 100.0)

        state = VehicleState(
            vehicle_id   = v["id"],
            plate_number = v["plate_number"],
            index        = idx,
            lat          = init_lat,
            lng          = init_lng,
            heading      = random.uniform(0, 2 * math.pi),
            speed_kmh    = random.uniform(10.0, 50.0),
            battery_pct  = init_battery,
        )
        states.append(state)

    # 4. 모든 차량 동시 시뮬레이션
    log_system(f"🚀  시뮬레이션 시작 — Ctrl+C 로 종료\n", C.CYAN)
    tasks = [simulate_vehicle(s, token) for s in states]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        # 종료 통계
        print(f"\n{C.CYAN}{'═' * 64}{C.RESET}")
        log_system("🏁  시뮬레이션 종료 — 통계", C.CYAN)
        total_telem = sum(s.telemetry_sent for s in states)
        total_alerts = sum(s.alerts_sent for s in states)
        print(f"   총 텔레메트리 전송: {C.GREEN}{total_telem}{C.RESET}건")
        print(f"   총 알림 발생:       {C.RED}{total_alerts}{C.RESET}건")
        print(f"{C.CYAN}{'═' * 64}{C.RESET}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}시뮬레이터가 중단되었습니다.{C.RESET}\n")
