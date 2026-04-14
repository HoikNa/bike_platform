# 18. 구현 현황 (Implementation Status)

> **프로젝트**: 지능형 오토바이 FMS  
> **버전**: v2.1 | **최종 업데이트**: 2026-04-15  
> **목적**: 실제로 구현·동작 중인 기능을 기준으로 작성한 현황 문서.  
> 설계 원본(13~17번 문서)과 다른 부분은 이 문서의 내용이 우선합니다.

---

## 목차

1. [현재 실행 환경](#1-현재-실행-환경)
2. [배포 정보](#2-배포-정보)
3. [백엔드 구현 현황](#3-백엔드-구현-현황)
4. [프론트엔드 구현 현황](#4-프론트엔드-구현-현황)
5. [화면별 기능 현황](#5-화면별-기능-현황)
6. [설계 대비 변경 사항](#6-설계-대비-변경-사항)
7. [미구현 항목](#7-미구현-항목)

---

## 1. 현재 실행 환경

### 1.1 환경별 구성

| 항목 | 로컬 개발 | 프로덕션 (현재 배포됨) |
|---|---|---|
| 운영 환경 | `chalice local` (포트 8000) | **AWS Lambda + API Gateway** |
| 데이터베이스 | SQLite (`fms_local_v2.db`) | **Supabase PostgreSQL** |
| 캐시 / 세션 | 미사용 | 미사용 |
| 실시간 통신 | HTTP 폴링 (2.5초 간격) | HTTP 폴링 (2.5초 간격) |
| 인증 | JWT HS256 | **JWT HS256** |
| 프론트엔드 서버 | Vite Dev Server (`localhost:5173`) | **Vercel** |
| API 프록시 | Vite proxy `/api → localhost:8000` | 없음 (직접 API Gateway URL) |
| OS / 플랫폼 | WSL2 (Windows) | AWS Lambda (Linux) / Vercel (Edge) |

### 1.2 로컬 서버 기동 방법

```bash
# 백엔드 (포트 8000)
cd fms-backend
chalice local --port 8000

# 프론트엔드 (포트 5173)
cd fms-frontend
npm run dev

# 시뮬레이터 (선택 — 백엔드 기동 후 별도 터미널)
cd fms-backend
python simulator.py
```

### 1.3 데이터베이스 환경 분기 (`database.py`)

```python
# DATABASE_URL 환경변수 미설정 → SQLite (로컬)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./fms_local_v2.db")

# 프로덕션: PostgreSQL with NullPool (Lambda stateless 대응)
# "postgres://" → "postgresql+psycopg2://" 자동 변환
```

---

## 2. 배포 정보

### 2.1 프로덕션 엔드포인트

| 서비스 | URL |
|---|---|
| **프론트엔드** (Vercel) | `https://fms-frontend-peach.vercel.app` |
| **백엔드 API** (AWS API Gateway) | `https://gmbsw71bng.execute-api.ap-northeast-2.amazonaws.com/api` |
| **데이터베이스** (Supabase) | `aws-1-ap-northeast-2.pooler.supabase.com:5432` |

### 2.2 백엔드 배포 설정 (`.chalice/config.json`)

```json
{
  "stages": {
    "production": {
      "api_gateway_stage": "api",
      "lambda_memory_size": 256,
      "lambda_timeout": 30,
      "environment_variables": {
        "APP_ENV": "production",
        "DATABASE_URL": "postgresql://...",
        "ALLOWED_ORIGIN": "https://fms-frontend-peach.vercel.app",
        "JWT_SECRET": "..."
      }
    }
  }
}
```

배포 명령: `chalice deploy --stage production`

### 2.3 프론트엔드 배포 설정

**`.env.production`**
```
VITE_API_BASE_URL=https://gmbsw71bng.execute-api.ap-northeast-2.amazonaws.com/api
```

**`vercel.json`** — SPA 라우팅 fallback
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

### 2.4 CORS 설정 (`chalicelib/core/cors.py`)

```python
# ALLOWED_ORIGIN 환경변수 기준 분기
# 미설정(로컬) → "*"   (모든 출처 허용)
# 설정(프로덕션) → "https://fms-frontend-peach.vercel.app"만 허용
cors_config = CORSConfig(
    allow_origin=_origin,
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
    allow_credentials=(_origin != "*"),
)
```

---

## 3. 백엔드 구현 현황

### 3.1 디렉터리 구조 (실제)

```
fms-backend/
├── app.py                          # 진입점, Blueprint 등록, 부트스트랩
├── simulator.py                    # ★ 비동기 IoT 주행 시뮬레이터 (신규)
├── .chalice/config.json            # 로컬/프로덕션 Chalice 설정
├── requirements.txt
└── chalicelib/
    ├── core/
    │   ├── database.py             # SQLite(로컬) / PostgreSQL+NullPool(프로덕션) 분기
    │   ├── cors.py                 # ★ CORSConfig 팩토리 (신규)
    │   ├── exceptions.py           # APIException (code, message, status_code)
    │   ├── jwt_helper.py           # encode_jwt / decode_jwt (HS256)
    │   └── password.py             # bcrypt 해싱
    ├── middlewares/
    │   └── auth.py                 # require_role(request, roles[]) 헬퍼 함수
    ├── models/                     # SQLModel 테이블 정의
    │   ├── base.py
    │   ├── user.py
    │   ├── driver_profile.py
    │   ├── vehicle.py
    │   ├── sensor_data.py
    │   ├── alert.py
    │   ├── trip.py
    │   └── charging_station.py
    ├── schemas/                    # Pydantic 응답 스키마 (model_dump 기반)
    │   ├── auth.py
    │   ├── vehicle.py              # VehicleListRead, VehicleDetailRead
    │   ├── alert.py                # AlertRead (nested vehicle, acknowledger)
    │   └── trip.py                 # TripRead
    ├── services/                   # 비즈니스 로직 (Repository 없이 Session 직접 사용)
    │   ├── auth_service.py         # 로그인, 토큰 발급, 테스트 유저 시드
    │   ├── vehicle_service.py      # 목록/상세 조회, 텔레메트리 수신, 데모 시드
    │   ├── alert_service.py        # 목록 조회, 알림 생성, acknowledge
    │   ├── trip_service.py         # 목록 조회(필터·페이지)
    │   └── seed_service.py         # 전체 데모 데이터 생성 (멱등)
    ├── routes/                     # Chalice Blueprint 라우터
    │   ├── auth_routes.py
    │   ├── vehicle_routes.py       # ★ telemetry PUT 엔드포인트 추가
    │   ├── alert_routes.py         # ★ alert POST 엔드포인트 추가
    │   └── trip_routes.py
    └── utils/
        └── http.py                 # 공통 응답 헬퍼
```

> **미구현 라우터**: `sensor_data_routes`, `charging_station_routes`, `user_routes`

---

### 3.2 구현된 API 엔드포인트

#### 인증 (`/auth`)

| 메서드 | 경로 | 기능 | 권한 |
|---|---|---|---|
| POST | `/auth/login` | 이메일·비밀번호로 로그인 → JWT 반환 | 공개 |
| GET | `/auth/me` | ★ 현재 로그인 사용자 정보 조회 | ADMIN, MANAGER, DRIVER |

**테스트 계정** (부트스트랩 시 자동 생성)

| 이메일 | 비밀번호 | 역할 |
|---|---|---|
| admin@fms.com | admin1234 | ADMIN |
| manager@fms.com | manager1234 | MANAGER |
| driver1@fms.com | driver1234 | DRIVER |

> `POST /auth/refresh` 는 설계서에만 존재하며 실제로는 미구현입니다.

---

#### 차량 (`/vehicles`)

| 메서드 | 경로 | 기능 | 권한 |
|---|---|---|---|
| GET | `/vehicles` | 차량 목록 (페이지·필터·검색) | DRIVER, MANAGER, ADMIN |
| GET | `/vehicles/{id}` | 차량 상세 (센서·드라이버·알림·운행 포함) | DRIVER, MANAGER, ADMIN |
| PUT | `/vehicles/{id}/telemetry` | ★ IoT/시뮬레이터 센서 데이터 수신 | DRIVER, MANAGER, ADMIN |

**쿼리 파라미터** (`GET /vehicles`)

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `page` | int | 페이지 번호 (1-based, 기본값: 1) |
| `page_size` | int | 페이지 크기 (기본값: 50) |
| `status` | string | 콤마 구분 상태 필터 (`RUNNING,IDLE,ALERT,CHARGING,OFFLINE`) |
| `q` | string | 번호판·모델명 텍스트 검색 |

**요청 바디** (`PUT /vehicles/{id}/telemetry`)

| 필드 | 타입 | 설명 |
|---|---|---|
| `latitude` | float | 위도 |
| `longitude` | float | 경도 |
| `speed_kmh` | float | 속도 (km/h). 0 이상 시 RUNNING, 0이면 IDLE로 상태 갱신 |
| `battery_level_pct` | float | 배터리 잔량 (%) |
| `engine_temp_celsius` | float | 엔진 온도 (°C) |

**응답 예시** (`GET /vehicles`)
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "plate_number": "11가3001",
      "model": "PCX Electric",
      "status": "RUNNING",
      "latest_sensor": {
        "latitude": 37.5012,
        "longitude": 127.0396,
        "speed_kmh": 32.4,
        "battery_level_pct": 78.2,
        "recorded_at": "2026-04-15T01:00:00Z"
      },
      "assigned_driver": {
        "driver_profile_id": "uuid",
        "user_full_name": "홍길동"
      },
      "unacknowledged_alerts_count": 2
    }
  ],
  "meta": {
    "total": 8,
    "page": 1,
    "page_size": 50,
    "total_pages": 1
  }
}
```

---

#### 알림 (`/alerts`)

| 메서드 | 경로 | 기능 | 권한 |
|---|---|---|---|
| GET | `/alerts` | 알림 목록 (커서 페이지네이션) | MANAGER, ADMIN |
| POST | `/alerts` | ★ 알림 직접 생성 (시뮬레이터/IoT) | DRIVER, MANAGER, ADMIN |
| PATCH | `/alerts/{id}/acknowledge` | 알림 확인 처리 | MANAGER, ADMIN |

**쿼리 파라미터** (`GET /alerts`)

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `limit` | int | 반환 개수 (기본값: 30) |
| `cursor` | string | Base64 인코딩된 커서 (다음 페이지) |
| `vehicle_id` | string | 특정 차량 필터 |
| `severity` | string | `DANGER,WARNING,INFO` (콤마 구분) |
| `is_acknowledged` | bool | 확인 여부 필터 |

**요청 바디** (`POST /alerts`)

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `vehicle_id` | string (UUID) | ✅ | 차량 ID |
| `alert_type` | string | ✅ | AlertType enum (`OVERSPEED`, `BATTERY_LOW` 등) |
| `severity` | string | ✅ | `DANGER`, `WARNING`, `INFO` |
| `title` | string | ✅ | 알림 제목 |
| `description` | string | - | 상세 설명 |
| `speed_at_trigger` | float | - | 발생 시 속도 (km/h) |
| `battery_at_trigger` | float | - | 발생 시 배터리 잔량 (%) |
| `location_lat` | float | - | 발생 위치 위도 |
| `location_lng` | float | - | 발생 위치 경도 |

---

#### 운행 기록 (`/trips`)

| 메서드 | 경로 | 기능 | 권한 |
|---|---|---|---|
| GET | `/trips` | 운행 기록 목록 (페이지네이션) | MANAGER, ADMIN |

**쿼리 파라미터**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `page` / `page_size` | int | 페이지네이션 |
| `vehicle_id` | string | 차량 필터 |
| `driver_id` | string | 기사 필터 |

---

### 3.3 시뮬레이터 (`simulator.py`)

서울 강남구 테헤란로 일대에서 등록된 모든 차량이 실제 주행하는 것처럼 텔레메트리·알림을 백엔드 API로 전송하는 비동기 Python 시뮬레이터입니다.

**동작 방식**
1. `/auth/login` 으로 JWT 토큰 취득
2. `/vehicles?page_size=100` 으로 전체 차량 목록 로드
3. 각 차량 별 코루틴을 `asyncio.gather` 로 동시 실행
4. 매 틱(기본 1.5초)마다 `PUT /vehicles/{id}/telemetry` 전송
5. 과속(≥80 km/h) 또는 배터리 부족(≤20%) 감지 시 `POST /alerts` 전송 (30초 쿨다운)

**주요 설정 (환경 변수)**

| 변수 | 기본값 | 설명 |
|---|---|---|
| `SIM_BASE_URL` | `http://localhost:8000` | 백엔드 URL |
| `SIM_EMAIL` | `admin@fms.com` | 로그인 이메일 |
| `SIM_PASSWORD` | `admin1234` | 로그인 비밀번호 |
| `SIM_TICK_SECS` | `1.5` | 틱 간격 (초) |

**실행 방법**
```bash
pip install aiohttp
python simulator.py

# 프로덕션 백엔드 대상
SIM_BASE_URL=https://gmbsw71bng.execute-api.ap-northeast-2.amazonaws.com/api python simulator.py
```

**알림 트리거 조건**

| 알림 타입 | 조건 | 심각도 |
|---|---|---|
| `OVERSPEED` | 속도 ≥ 80 km/h | DANGER |
| `BATTERY_LOW` | 배터리 ≤ 20% | WARNING |

---

### 3.4 부트스트랩 및 데모 데이터 (`seed_service.py`)

앱 기동 시 `bootstrap()` 함수가 자동 실행됩니다.

```
bootstrap()
  ├── create_db_and_tables()          # 테이블 자동 생성 (없으면)
  ├── AuthService.seed_test_users()   # 테스트 계정 3개 생성 (멱등)
  ├── VehicleService.seed_demo_vehicles_if_empty()  # 차량 8대 생성
  └── SeedService.seed_all()          # DriverProfile, SensorData, Alert, Trip 생성
```

**생성 데이터 규모**

| 항목 | 내용 |
|---|---|
| 차량 | **8대** (RUNNING 4, IDLE 1, CHARGING 2, ALERT 1) |
| 운전자 | 6명 (일부 차량에 배정) |
| 센서 데이터 | 차량당 최근 1시간치, 5분 간격 |
| 알림 | 차량당 2~5건 |
| 운행 기록 | 차량당 3~8건 |

> 이전 문서(v2.0)의 "차량 10대, OFFLINE 1대" 는 현재 시드 로직과 다릅니다. 실제 코드 기준은 8대입니다.

---

### 3.5 인증 미들웨어

```python
# chalicelib/middlewares/auth.py
def require_role(request, roles: list[str]) -> dict:
    """
    Authorization 헤더에서 JWT 검증 후 역할 체크.
    실패 시 APIException 발생 (401 / 403).
    반환값: JWT payload dict { sub, email, role, ... }
    """
```

---

## 4. 프론트엔드 구현 현황

### 4.1 디렉터리 구조 (실제)

```
fms-frontend/
├── .env.production                 # ★ Vercel 배포용 환경 변수 (VITE_API_BASE_URL)
├── vercel.json                     # ★ SPA 라우팅 fallback 설정
├── vite.config.ts                  # 로컬 Vite proxy 설정 (/api → :8000)
└── src/
    ├── main.ts                     # 앱 진입점 (Pinia, Router, 다크모드 초기화)
    ├── App.vue                     # 루트 컴포넌트
    │
    ├── layouts/
    │   └── AppLayout.vue           # 상단 헤더 레이아웃 (사이드바 없음)
    │
    ├── views/
    │   ├── auth/
    │   │   └── LoginView.vue       # 로그인 페이지
    │   ├── dashboard/
    │   │   └── DashboardView.vue   # 메인 대시보드 ★
    │   ├── vehicles/
    │   │   ├── VehicleListView.vue
    │   │   └── VehicleDetailView.vue
    │   ├── alerts/
    │   │   └── AlertListView.vue
    │   ├── trips/
    │   │   └── TripListView.vue
    │   └── errors/
    │       ├── ForbiddenView.vue
    │       └── NotFoundView.vue
    │
    ├── components/
    │   ├── map/
    │   │   └── RealtimeMap.vue     # Leaflet 지도 컴포넌트 ★
    │   ├── alert/
    │   │   └── EventAlertPanel.vue
    │   ├── common/
    │   │   ├── BaseCard.vue
    │   │   └── StatusBadge.vue
    │   └── vehicle/
    │       └── VehicleStatusWidget.vue
    │
    ├── stores/
    │   ├── auth.ts                 # 인증·사용자 정보
    │   ├── fleet.ts                # 차량 목록, 실시간 위치, 데모 시뮬레이션 ★
    │   ├── alert.ts                # 알림 목록·상태
    │   ├── realtime.ts             # ★ 폴링 연결 상태 플래그 (isConnected)
    │   └── ui.ts                   # Toast 큐, 전역 로딩
    │
    ├── services/
    │   ├── http.ts                 # Axios 인스턴스 (인터셉터: 토큰 주입·에러 파싱)
    │   ├── api.ts                  # ★ 통합 API 클라이언트 (fetchVehicles, fetchAlerts 등)
    │   ├── authService.ts
    │   ├── vehicleService.ts
    │   ├── alertService.ts
    │   └── tripService.ts
    │
    ├── router/
    │   ├── index.ts
    │   └── guards/
    │       ├── authGuard.ts        # 미인증 → /login 리다이렉트
    │       └── roleGuard.ts        # 역할별 접근 제한
    │
    ├── types/
    │   ├── models.ts               # Vehicle, Alert, Trip, LatestSensor 등 인터페이스
    │   └── api.ts                  # PageMeta, CursorMeta, ApiResponse 인터페이스
    │
    └── composables/
        ├── useRealtime.ts          # ★ HTTP 폴링 composable (2.5초 간격)
        ├── useToast.ts
        ├── useDelayedLoading.ts
        └── useInfiniteScroll.ts
```

---

### 4.2 라우트 구조

```
/                   → redirect /app
/login              → LoginView
/app                → AppLayout (인증 필요)
  /app/dashboard    → DashboardView
  /app/vehicles     → VehicleListView
  /app/vehicles/:id → VehicleDetailView
  /app/alerts       → AlertListView
  /app/trips        → TripListView
/403                → ForbiddenView
/*                  → NotFoundView
```

---

### 4.3 AppLayout — 상단 헤더 구조

설계 문서의 사이드바 레이아웃 대신 **상단 헤더 단일 레이아웃**으로 구현됨.

```
┌─────────────────────────────────────────────────────────────┐
│ [BikeFMS 로고]  [대시보드] [차량관리] [알림관리] [운행기록]  [● 실시간] [☀/☾] [👤▾] │
└─────────────────────────────────────────────────────────────┘
│                                                              │
│                       <RouterView />                         │
│                                                              │
```

| 영역 | 내용 |
|---|---|
| 좌측 (w-36) | BikeFMS 로고 |
| 중앙 (flex-1) | 네비게이션 링크 4개 (미확인 알림 배지 포함) |
| 우측 (w-36) | 실시간 연결 상태 · 다크모드 토글 · 사용자 메뉴(로그아웃) |

---

### 4.4 실시간 데이터 갱신 — HTTP 폴링 방식

WebSocket / Socket.IO 대신 **단기 HTTP 폴링**으로 구현됩니다.

```typescript
// composables/useRealtime.ts
export function useRealtime(intervalMs = 2500) {
  // mount 시: setInterval → 2.5초마다 fetchVehicles + fetchAlerts 동시 호출
  // unmount 시: clearInterval + isConnected = false
}
```

| 항목 | 내용 |
|---|---|
| 폴링 간격 | 기본 2,500ms |
| 갱신 대상 | `fleetStore.refreshVehicles()` + `alertStore.refreshAlerts()` 동시 실행 |
| 연결 상태 표시 | `realtimeStore.isConnected` (mount=true / unmount=false) |
| 헤더 인디케이터 | `● 실시간` (초록) / `○ 오프라인` (회색) |

---

### 4.5 통합 API 클라이언트 (`services/api.ts`)

`http.ts`(Axios 인스턴스)를 기반으로 각 화면이 직접 호출할 수 있는 함수 모음입니다.

```typescript
// 차량
fetchVehicles(pageSize = 100): Promise<Vehicle[]>
fetchVehicleDetail(id: string): Promise<Vehicle>

// 알림
fetchAlerts(limit = 30): Promise<Alert[]>
```

**baseURL 환경 분기 (`http.ts`)**
- 로컬: `VITE_API_BASE_URL` 미설정 → Vite proxy `/api → localhost:8000`
- 프로덕션(Vercel): `.env.production` 의 `VITE_API_BASE_URL` (API Gateway URL 직접 호출)

---

### 4.6 DashboardView — 레이아웃

```
┌──────────────────────────────────────────────────────────────┐
│  [전체차량 ⚡ N] [운행중 ▶ N] [미확인알림 🔔 N] [오프라인 📶 N]  │  ← 상단 4개 카드
├──────────────┬───────────────────────────────────────────────┤
│              │  [전체][운행중][충전필요][미운행]  ← 필터 버튼  │
│  차량 현황   │                                               │
│  (w-48)      │         RealtimeMap (Leaflet)                  │
│  ↕ 스크롤    │                                               │
└──────────────┴───────────────────────────────────────────────┘
```

| 기능 | 설명 |
|---|---|
| 통계 카드 | 전체 차량 수, 운행 중, 미확인 알림, 오프라인 실시간 표시 |
| 차량 목록 | 전체 높이 스크롤, 클릭 시 해당 차량 선택 (지도 중심 이동) |
| 지도 필터 | 전체 / 운행중 / 충전 필요(배터리 ≤30%) / 미운행 |
| 데모 시뮬레이션 | RUNNING·ALERT 차량 1.5초마다 클라이언트에서 위치 계산 이동 |
| 폴링 갱신 | 2.5초마다 서버에서 실제 위치 데이터 자동 갱신 |

---

### 4.7 RealtimeMap — 구현 상세

**기술 스택**: Leaflet.js + Vue 3 DOM 오버레이 (CSS 마커)

| 기능 | 구현 방식 |
|---|---|
| 타일 레이어 | CartoCDN Light/Dark (다크모드 자동 전환) |
| 차량 마커 | 절대 좌표 `<div>` (`latLngToContainerPoint` 변환) |
| 마커 색상 | RUNNING=초록, IDLE=회색, CHARGING=파랑, ALERT=빨강, OFFLINE=연회색 |
| 알림 뱃지 | 미확인 알림 있는 차량 마커 하단에 colored pill 표시 |
| 선택 효과 | 클릭 시 강조 링 + 다른 차량 30% 투명도 |
| 경로 표시 | 선택 차량 6시간 이력 SVG polyline (글로우 + 주선) |
| 방향 화살표 | 경로선 위 65px 간격으로 `>` 모양 화살표 (진행 방향 자동 회전) |
| 출발점 표시 | 초록 원 + "출발" 텍스트 |
| 줌 컨트롤 | 커스텀 +/- 버튼 + 세로 슬라이더 (10~18) |
| 하단 상태바 | 운행 중 / 알림 / 충전 / 전체 대수 요약 |

---

### 4.8 Fleet Store — 데모 시뮬레이션

```typescript
// stores/fleet.ts
fleetStore.startDemoSimulation(intervalMs = 1500)
fleetStore.stopDemoSimulation()
```

- RUNNING / ALERT 상태 차량을 1.5초마다 이동
- 각 차량은 방향(heading)을 유지하면서 ±0.35rad 범위로 조금씩 방향 전환
- 위치 이력(`positionHistory`)에 자동 누적 → 경로 화살표 실시간 업데이트
- `DashboardView` 마운트/언마운트 시 자동 시작/중지

---

### 4.9 Pinia 스토어 요약

| 스토어 | 파일 | 주요 상태 / 액션 |
|---|---|---|
| **auth** | `stores/auth.ts` | `currentUser`, `login()`, `logout()` |
| **fleet** | `stores/fleet.ts` | `vehicles`, `selectedVehicleId`, `realtimeLocations`, `positionHistory`, `fetchVehicles()`, `refreshVehicles()`, `selectVehicle()`, `startDemoSimulation()` |
| **alert** | `stores/alert.ts` | `alerts`, `unacknowledgedCount`, `fetchAlerts()`, `refreshAlerts()`, `acknowledge()` |
| **realtime** | `stores/realtime.ts` | `isConnected`, `setConnected(bool)` (폴링 상태 플래그) |
| **ui** | `stores/ui.ts` | `toastQueue`, `addToast()`, `removeToast()` |

---

## 5. 화면별 기능 현황

| 화면 | 경로 | 상태 | 주요 기능 |
|---|---|---|---|
| 로그인 | `/login` | ✅ 완료 | 이메일·비밀번호 로그인, JWT 저장 |
| 대시보드 | `/app/dashboard` | ✅ 완료 | 통계 카드, 차량 목록, 실시간 지도, 시뮬레이션, 2.5초 폴링 |
| 차량 목록 | `/app/vehicles` | ✅ 완료 | 페이지네이션, 상태·검색 필터 |
| 차량 상세 | `/app/vehicles/:id` | ✅ 완료 | 센서·드라이버·알림·운행 이력 |
| 알림 관리 | `/app/alerts` | ✅ 완료 | 커서 페이지네이션, 심각도 필터, 알림 확인 처리 |
| 운행 기록 | `/app/trips` | ✅ 완료 | 페이지네이션, 차량·기사 필터 |

---

## 6. 설계 대비 변경 사항

### 백엔드

| 항목 | 설계 (15번 문서) | 실제 구현 |
|---|---|---|
| DB (로컬) | PostgreSQL | SQLite (`fms_local_v2.db`) |
| DB (프로덕션) | PostgreSQL + TimescaleDB | **Supabase PostgreSQL** (NullPool, SSL) |
| 캐시 | Redis | 미사용 |
| MQTT | EMQX 브로커 | 미구현 — 대신 `simulator.py`가 REST API로 직접 전송 |
| Repository 계층 | `repositories/` 별도 디렉터리 | 서비스에서 Session 직접 사용 |
| 에러 계층 | `AppError` 서브클래스 다수 | `APIException(code, message, status_code)` 단일 클래스 |
| 인증 | JWT RS256 + Redis 블랙리스트 | JWT HS256, 블랙리스트 없음 |
| Blueprint URL prefix | `url_prefix="/vehicles"` 방식 | 라우트 경로에 직접 포함 |
| IoT 수신 | MQTT 구독 | `PUT /vehicles/{id}/telemetry` REST 엔드포인트 |
| 추가 | — | `simulator.py`, `cors.py`, `seed_service.py` |

### 프론트엔드

| 항목 | 설계 (16번 문서) | 실제 구현 |
|---|---|---|
| 레이아웃 | Header + Sidebar + Main | **상단 헤더만** (사이드바 없음) |
| 배포 | CDN / S3 | **Vercel** (`vercel.json` + `.env.production`) |
| 실시간 통신 | WebSocket / Socket.IO | **HTTP 폴링** (`useRealtime` composable, 2.5초) |
| realtimeStore | WebSocket 클라이언트 로직 | **연결 상태 플래그**만 관리 (`setConnected`) |
| API 클라이언트 | 개별 서비스 파일만 | 개별 서비스 파일 + `api.ts` 통합 클라이언트 추가 |
| 실시간 이동 | WebSocket 수신 | **데모 시뮬레이션** (클라이언트 자체 계산) + 폴링 갱신 |
| 지도 마커 | 계획 없음 | Leaflet DOM 오버레이, 경로선, 방향 화살표 |

---

## 7. 미구현 항목

### 백엔드

| 항목 | 비고 |
|---|---|
| MQTT 수신 서비스 | `simulator.py`가 REST로 대체 중이나 실제 IoT 단말기 연동은 미구현 |
| WebSocket 푸시 | 서버→클라이언트 실시간 알림. 현재 클라이언트 폴링으로 대체 |
| 충전소 API (`/charging-stations`) | 라우터 미작성 |
| 센서 데이터 조회 API (`/vehicles/{id}/sensors`) | 라우터 미작성 |
| 사용자 관리 API (`/users`) | 라우터 미작성 |
| 차량 생성·수정·삭제 API | GET만 구현, POST/PUT/DELETE 미작성 |
| 운행 기록 생성·종료 API | GET만 구현 |
| Redis 연동 | JWT 블랙리스트, 캐시 |
| DB 마이그레이션 (Alembic) | 현재는 `SQLModel.metadata.create_all()` 방식 |

### 프론트엔드

| 항목 | 비고 |
|---|---|
| WebSocket 실시간 연동 | 현재 HTTP 폴링으로 운영 중 |
| 차량 생성·편집 폼 | UI 없음 |
| 모바일 레이아웃 | 관제 웹만 구현 |
| 지도 클러스터링 | 차량 밀집 시 마커 겹침 발생 |
| 다국어(i18n) | 한국어 고정 |
| E2E 테스트 | 미작성 |
