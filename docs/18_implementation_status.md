# 18. 구현 현황 (Implementation Status)

> **프로젝트**: 지능형 오토바이 FMS  
> **버전**: v2.0 | **최종 업데이트**: 2026-04-14  
> **목적**: 실제로 구현·동작 중인 기능을 기준으로 작성한 현황 문서.  
> 설계 원본(13~17번 문서)과 다른 부분은 이 문서의 내용이 우선합니다.

---

## 목차

1. [현재 실행 환경](#1-현재-실행-환경)
2. [백엔드 구현 현황](#2-백엔드-구현-현황)
3. [프론트엔드 구현 현황](#3-프론트엔드-구현-현황)
4. [화면별 기능 현황](#4-화면별-기능-현황)
5. [설계 대비 변경 사항](#5-설계-대비-변경-사항)
6. [미구현 항목](#6-미구현-항목)

---

## 1. 현재 실행 환경

| 항목 | 설계 | 실제 |
|---|---|---|
| 운영 환경 | AWS Lambda + API Gateway | **로컬 개발 서버** (`chalice local`) |
| 데이터베이스 | PostgreSQL 16 + TimescaleDB | **SQLite** (로컬 파일 `fms.db`) |
| 캐시 / 세션 | Redis | **미사용** |
| 실시간 통신 | EMQX MQTT + Socket.IO | **미구현** (HTTP polling 대체) |
| 인증 | JWT RS256 (공개키 기반) | **JWT HS256** (단순 시크릿 키) |
| 프론트엔드 서버 | CDN / S3 | **Vite Dev Server** (`localhost:5173`) |
| API 프록시 | 없음 (직접 API Gateway) | **Vite proxy** `/api → localhost:8000` |
| OS | Linux (Lambda) | WSL2 (Windows) — `host: "0.0.0.0"` 필수 |

### 서버 기동 방법

```bash
# 백엔드 (포트 8000)
cd fms-backend
chalice local --port 8000

# 프론트엔드 (포트 5173)
cd fms-frontend
npm run dev
```

---

## 2. 백엔드 구현 현황

### 2.1 디렉터리 구조 (실제)

```
fms-backend/
├── app.py                          # 진입점, Blueprint 등록, 부트스트랩
├── .chalice/config.json
├── requirements.txt
└── chalicelib/
    ├── core/
    │   ├── database.py             # SQLite 엔진, get_session() 컨텍스트 매니저
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
    │   ├── vehicle_service.py      # 목록 조회(필터·페이지), 상세 조회, 데모 시드
    │   ├── alert_service.py        # 목록 조회(커서 페이지네이션), acknowledge
    │   ├── trip_service.py         # 목록 조회(필터·페이지)
    │   └── seed_service.py         # 전체 데모 데이터 생성 (멱등)
    ├── routes/                     # Chalice Blueprint 라우터
    │   ├── auth_routes.py
    │   ├── vehicle_routes.py
    │   ├── alert_routes.py
    │   └── trip_routes.py
    └── utils/
        └── http.py                 # 공통 응답 헬퍼
```

> **미구현 라우터**: `sensor_data_routes`, `charging_station_routes`, `user_routes`

---

### 2.2 구현된 API 엔드포인트

#### 인증 (`/auth`)

| 메서드 | 경로 | 기능 | 권한 |
|---|---|---|---|
| POST | `/auth/login` | 이메일·비밀번호로 로그인 → JWT 반환 | 공개 |
| POST | `/auth/refresh` | 리프레시 토큰으로 액세스 토큰 재발급 | 공개 |

**테스트 계정** (부트스트랩 시 자동 생성)

| 이메일 | 비밀번호 | 역할 |
|---|---|---|
| admin@fms.com | admin1234 | ADMIN |
| manager@fms.com | manager1234 | MANAGER |
| driver1@fms.com | driver1234 | DRIVER |

---

#### 차량 (`/vehicles`)

| 메서드 | 경로 | 기능 | 권한 |
|---|---|---|---|
| GET | `/vehicles` | 차량 목록 (페이지·필터·검색) | DRIVER, MANAGER, ADMIN |
| GET | `/vehicles/{id}` | 차량 상세 (센서·드라이버·알림·운행 포함) | DRIVER, MANAGER, ADMIN |

**쿼리 파라미터** (`GET /vehicles`)

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `page` | int | 페이지 번호 (1-based, 기본값: 1) |
| `page_size` | int | 페이지 크기 (기본값: 50) |
| `status` | string | 콤마 구분 상태 필터 (`RUNNING,IDLE,ALERT,CHARGING,OFFLINE`) |
| `q` | string | 번호판·모델명 텍스트 검색 |

**응답 예시** (`GET /vehicles`)
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "plate_number": "서울12가3456",
      "model": "PCX 125",
      "status": "RUNNING",
      "latest_sensor": {
        "latitude": 37.5548,
        "longitude": 127.0420,
        "speed_kmh": 32.4,
        "battery_level_pct": 78.2,
        "recorded_at": "2026-04-14T10:30:00Z"
      },
      "assigned_driver": {
        "driver_profile_id": "uuid",
        "user_full_name": "홍길동"
      },
      "unacknowledged_alerts_count": 2
    }
  ],
  "meta": {
    "total": 10,
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
| GET | `/alerts` | 알림 목록 (커서 페이지네이션) | DRIVER, MANAGER, ADMIN |
| PATCH | `/alerts/{id}/acknowledge` | 알림 확인 처리 | MANAGER, ADMIN |

**쿼리 파라미터** (`GET /alerts`)

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `limit` | int | 반환 개수 (기본값: 30) |
| `cursor` | string | Base64 인코딩된 커서 (다음 페이지) |
| `vehicle_id` | string | 특정 차량 필터 |
| `severity` | string | `DANGER`, `WARNING`, `INFO` |
| `is_acknowledged` | bool | 확인 여부 필터 |

---

#### 운행 기록 (`/trips`)

| 메서드 | 경로 | 기능 | 권한 |
|---|---|---|---|
| GET | `/trips` | 운행 기록 목록 (페이지네이션) | DRIVER, MANAGER, ADMIN |

**쿼리 파라미터**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `page` / `page_size` | int | 페이지네이션 |
| `vehicle_id` | string | 차량 필터 |
| `driver_id` | string | 기사 필터 |

---

### 2.3 부트스트랩 및 데모 데이터 (`seed_service.py`)

앱 기동 시 `bootstrap()` 함수가 자동 실행됩니다.

```
bootstrap()
  ├── create_db_and_tables()          # SQLite 테이블 생성 (없으면)
  ├── AuthService.seed_test_users()   # 테스트 계정 3개 생성 (멱등)
  ├── VehicleService.seed_demo_vehicles_if_empty()  # 차량 10대 생성
  └── SeedService.seed_all()          # DriverProfile, SensorData, Alert, Trip 생성
```

**생성 데이터 규모**

| 항목 | 내용 |
|---|---|
| 차량 | 10대 (RUNNING 4, IDLE 2, CHARGING 2, ALERT 1, OFFLINE 1) |
| 운전자 | 8명 (차량에 배정) |
| 센서 데이터 | 차량당 최근 1시간치, 5분 간격 (총 120건) |
| 알림 | 차량당 2~5건 (총 약 35건) |
| 운행 기록 | 차량당 3~8건 (총 약 55건) |

---

### 2.4 인증 미들웨어

```python
# chalicelib/middlewares/auth.py
def require_role(request, roles: list[str]) -> dict:
    """
    Authorization 헤더에서 JWT 검증 후 역할 체크.
    실패 시 APIException 발생 (401 / 403).
    반환값: JWT payload dict
    """
```

---

## 3. 프론트엔드 구현 현황

### 3.1 디렉터리 구조 (실제)

```
fms-frontend/src/
├── main.ts                         # 앱 진입점 (Pinia, Router, 다크모드 초기화)
├── App.vue                         # 루트 컴포넌트
│
├── layouts/
│   └── AppLayout.vue               # 상단 헤더 레이아웃 (사이드바 없음)
│
├── views/
│   ├── auth/
│   │   └── LoginView.vue           # 로그인 페이지
│   ├── dashboard/
│   │   └── DashboardView.vue       # 메인 대시보드 ★
│   ├── vehicles/
│   │   ├── VehicleListView.vue     # 차량 목록
│   │   └── VehicleDetailView.vue   # 차량 상세
│   ├── alerts/
│   │   └── AlertListView.vue       # 알림 목록
│   ├── trips/
│   │   └── TripListView.vue        # 운행 기록 목록
│   └── errors/
│       ├── ForbiddenView.vue
│       └── NotFoundView.vue
│
├── components/
│   ├── map/
│   │   └── RealtimeMap.vue         # Leaflet 지도 컴포넌트 ★
│   ├── alert/
│   │   └── EventAlertPanel.vue
│   ├── common/
│   │   ├── BaseCard.vue
│   │   └── StatusBadge.vue
│   └── vehicle/
│       └── VehicleStatusWidget.vue
│
├── stores/
│   ├── auth.ts                     # 인증·사용자 정보
│   ├── fleet.ts                    # 차량 목록, 실시간 위치, 데모 시뮬레이션 ★
│   ├── alert.ts                    # 알림 목록·상태
│   ├── realtime.ts                 # WebSocket 연결 상태 (미연결)
│   └── ui.ts                       # Toast 큐, 전역 로딩
│
├── services/
│   ├── http.ts                     # Axios 인스턴스 (인터셉터: 토큰 주입·갱신·에러 파싱)
│   ├── authService.ts
│   ├── vehicleService.ts
│   ├── alertService.ts
│   └── tripService.ts
│
├── router/
│   ├── index.ts                    # 라우트 정의
│   └── guards/
│       ├── authGuard.ts            # 미인증 → /login 리다이렉트
│       └── roleGuard.ts            # 역할별 접근 제한
│
├── types/
│   ├── models.ts                   # Vehicle, Alert, Trip, LatestSensor 등 인터페이스
│   └── api.ts                      # PageMeta, CursorMeta, ApiResponse 인터페이스
│
└── composables/
    ├── useToast.ts
    ├── useDelayedLoading.ts
    └── useInfiniteScroll.ts
```

---

### 3.2 라우트 구조

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

### 3.3 AppLayout — 상단 헤더 구조

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

### 3.4 DashboardView — 레이아웃

```
┌──────────────────────────────────────────────────────────────┐
│  [전체차량 ⚡ N] [운행중 ▶ N] [미확인알림 🔔 N] [오프라인 📶 N]  │  ← 상단 4개 카드 (compact, 1행)
├──────────────┬───────────────────────────────────────────────┤
│              │  [전체][운행중][충전필요][미운행]  ← 필터 버튼  │
│  차량 현황   │                                               │
│  (w-48)      │                                               │
│              │         RealtimeMap (Leaflet)                  │
│  - 번호판    │                                               │
│  - 드라이버  │                                               │
│  - 배터리%   │                                               │
│  - 알림 수   │                                               │
│  ↕ 스크롤    │                                               │
└──────────────┴───────────────────────────────────────────────┘
```

**기능 목록**

| 기능 | 설명 |
|---|---|
| 통계 카드 | 전체 차량 수, 운행 중, 미확인 알림, 오프라인 실시간 표시 |
| 차량 목록 | 전체 높이 스크롤, 클릭 시 해당 차량 선택 (지도 중심 이동) |
| 지도 필터 | 전체 / 운행중 / 충전 필요(배터리 ≤30%) / 미운행 |
| 데모 시뮬레이션 | 대시보드 진입 시 RUNNING·ALERT 차량 1.5초마다 이동 |
| 자동 지도 이동 | 차량 클릭 시 해당 위치로 `panTo` 애니메이션 |

---

### 3.5 RealtimeMap — 구현 상세

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

### 3.6 Fleet Store — 데모 시뮬레이션

```typescript
// stores/fleet.ts
fleetStore.startDemoSimulation(intervalMs = 1500)
fleetStore.stopDemoSimulation()
```

- RUNNING / ALERT 상태 차량을 1.5초마다 이동
- 각 차량은 방향(heading)을 유지하면서 ±0.35rad 범위로 조금씩 방향 전환
- 이동 속도: 약 20~40 km/h 수준
- 위치 이력(`positionHistory`)에 자동 누적 → 경로 화살표 실시간 업데이트
- `DashboardView` 마운트/언마운트 시 자동 시작/중지

---

### 3.7 Pinia 스토어 요약

| 스토어 | 파일 | 주요 상태 / 액션 |
|---|---|---|
| **auth** | `stores/auth.ts` | `currentUser`, `login()`, `logout()`, `refreshToken()` |
| **fleet** | `stores/fleet.ts` | `vehicles`, `selectedVehicleId`, `realtimeLocations`, `positionHistory`, `fetchVehicles()`, `selectVehicle()`, `startDemoSimulation()`, `updateRealtimeLocation()` |
| **alert** | `stores/alert.ts` | `alerts`, `unacknowledgedCount`, `fetchAlerts()`, `acknowledge()`, `prependAlert()` |
| **realtime** | `stores/realtime.ts` | `isConnected`, `connect()`, `disconnect()` (WebSocket 미연결) |
| **ui** | `stores/ui.ts` | `toastQueue`, `addToast()`, `removeToast()` |

---

### 3.8 HTTP 서비스 레이어

```
Axios 인스턴스 (services/http.ts)
├── baseURL: /api  (Vite proxy → localhost:8000)
├── 요청 인터셉터: Authorization 헤더 자동 주입
└── 응답 인터셉터: 401 시 토큰 자동 갱신 → 재시도
```

---

## 4. 화면별 기능 현황

| 화면 | 경로 | 상태 | 주요 기능 |
|---|---|---|---|
| 로그인 | `/login` | ✅ 완료 | 이메일·비밀번호 로그인, JWT 저장 |
| 대시보드 | `/app/dashboard` | ✅ 완료 | 통계 카드, 차량 목록, 실시간 지도, 시뮬레이션 |
| 차량 목록 | `/app/vehicles` | ✅ 완료 | 페이지네이션, 상태·검색 필터, 차량 선택 |
| 차량 상세 | `/app/vehicles/:id` | ✅ 완료 | 센서·드라이버·알림·운행 이력 |
| 알림 관리 | `/app/alerts` | ✅ 완료 | 커서 페이지네이션, 심각도 필터, 알림 확인 처리 |
| 운행 기록 | `/app/trips` | ✅ 완료 | 페이지네이션, 차량·기사 필터 |

---

## 5. 설계 대비 변경 사항

### 백엔드

| 항목 | 설계 (15번 문서) | 실제 구현 |
|---|---|---|
| DB | PostgreSQL + TimescaleDB | SQLite (로컬 개발) |
| 캐시 | Redis | 미사용 |
| MQTT | EMQX 브로커 | 미구현 |
| Repository 계층 | `repositories/` 별도 디렉터리 | 서비스에서 Session 직접 사용 |
| 에러 계층 | `AppError` 서브클래스 다수 | `APIException(code, message, status_code)` 단일 클래스 |
| 인증 | JWT RS256 + Redis 블랙리스트 | JWT HS256, 블랙리스트 없음 |
| Blueprint URL prefix | `url_prefix="/vehicles"` 방식 | 라우트 경로에 직접 포함 |
| 추가 서비스 | — | `seed_service.py` (데모 데이터) |

### 프론트엔드

| 항목 | 설계 (16번 문서) | 실제 구현 |
|---|---|---|
| 레이아웃 | Header + Sidebar + Main | **상단 헤더만** (사이드바 없음) |
| 대시보드 좌측 | 차량 목록 + 최근 알림 | **차량 목록만** (w-48) |
| 대시보드 우측 | 지도만 | **지도 + 상단 필터 버튼** |
| 지도 마커 | 계획 없음 | Leaflet DOM 오버레이 방식 |
| 실시간 이동 | WebSocket 수신 | **데모 시뮬레이션** (클라이언트 자체 계산) |
| 알림 배지 | 계획 없음 | 마커 하단 colored pill |
| 경로 표시 | 계획 없음 | SVG polyline + 방향 화살표 |
| WebSocket | Socket.IO 연결 | 미연결 (realtimeStore 스텁만 존재) |

---

## 6. 미구현 항목

### 백엔드

| 항목 | 비고 |
|---|---|
| MQTT 수신 서비스 | IoT 단말기 연동 필요 |
| WebSocket 푸시 | 실시간 알림 서버→클라이언트 |
| 충전소 API (`/charging-stations`) | 라우터 미작성 |
| 센서 데이터 API (`/vehicles/{id}/sensors`) | 라우터 미작성 |
| 사용자 관리 API (`/users`) | 라우터 미작성 |
| 차량 생성·수정·삭제 API | GET만 구현, POST/PUT/DELETE 미작성 |
| 운행 기록 생성·종료 API | GET만 구현 |
| PostgreSQL 마이그레이션 | Alembic 설정 필요 |
| Redis 연동 | JWT 블랙리스트, 캐시 |
| AWS 배포 설정 | `.chalice/config.json` 프로덕션 설정 |

### 프론트엔드

| 항목 | 비고 |
|---|---|
| WebSocket 실시간 연동 | `realtimeStore.connect()` 스텁만 존재 |
| 차량 생성·편집 폼 | UI 없음 |
| 모바일 레이아웃 | 관제 웹만 구현 |
| 지도 클러스터링 | 차량 밀집 시 마커 겹침 발생 |
| 다국어(i18n) | 한국어 고정 |
| E2E 테스트 | 미작성 |
