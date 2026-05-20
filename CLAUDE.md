# FMS (Fleet Management System) — bike_platform

## 프로젝트 개요
- **이름**: FMS (Intelligent Motorcycle Fleet Management System)
- **목적**: 오토바이 플릿의 실시간 위치 추적, 센서 데이터 수집, 알림 관리, 운행 이력 조회
- **단계**: 운영 중 (Production deployed)
- **프론트엔드**: https://fms-frontend-peach.vercel.app
- **백엔드 API**: https://gmbsw71bng.execute-api.ap-northeast-2.amazonaws.com/api
- **데이터베이스**: Supabase PostgreSQL (`aws-1-ap-northeast-2.pooler.supabase.com:5432`)

## 역할
시니어 풀스택 엔지니어로서 운영 중인 시스템을 안정적으로 유지·개선한다.
`docs/18_implementation_status.md`가 현재 구현 상태의 기준 문서다 — 설계 문서와 충돌 시 이 파일을 우선한다.

---

## 기술 스택

### 백엔드 (`fms-backend/`)
| 항목 | 내용 |
|------|------|
| 언어 | Python 3.12 |
| 프레임워크 | AWS Chalice 1.x (Serverless) |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| 인증 | JWT HS256 + bcrypt |
| DB (로컬) | SQLite (`fms_local_v2.db`) |
| DB (운영) | Supabase PostgreSQL (NullPool — Lambda stateless 필수) |
| 배포 | AWS Lambda + API Gateway (ap-northeast-2) |
| 린터 | 없음 (Chalice 프레임워크 관례 따름) |

### 프론트엔드 (`fms-frontend/`)
| 항목 | 내용 |
|------|------|
| 언어 | TypeScript |
| 프레임워크 | Vue 3 (Composition API) |
| 빌드 | Vite |
| 상태 관리 | Pinia |
| 라우팅 | Vue Router 4 |
| 스타일 | TailwindCSS |
| 아이콘 | Lucide Vue Next |
| 지도 | Leaflet.js |
| HTTP | Axios |
| 배포 | Vercel |
| 패키지 매니저 | npm |

---

## 디렉토리 구조

```
bike_platform/
├── docs/                          # 설계·운영 문서
│   └── 18_implementation_status.md  # ★ 현재 구현 상태 기준 문서
├── fms-backend/
│   ├── app.py                     # 진입점, Blueprint 등록, DB bootstrap
│   ├── simulator.py               # IoT 시뮬레이터 (async, 실시간 텔레메트리)
│   ├── requirements.txt
│   ├── .chalice/config.json       # Chalice 스테이지 설정 (dev/production)
│   └── chalicelib/
│       ├── models/                # SQLModel 테이블 정의
│       │   ├── user.py            # User (ADMIN/MANAGER/DRIVER)
│       │   ├── vehicle.py         # Vehicle (plate, status, driver FK)
│       │   ├── sensor_data.py     # SensorData (lat, lng, speed, battery)
│       │   ├── alert.py           # Alert (type, severity, acknowledged)
│       │   ├── trip.py            # Trip (start/end, distance)
│       │   ├── driver_profile.py  # DriverProfile
│       │   └── charging_station.py
│       ├── schemas/               # Pydantic 응답 스키마
│       ├── services/              # 비즈니스 로직
│       ├── routes/                # Chalice Blueprint 라우트
│       │   ├── auth_routes.py     # POST /auth/login, GET /auth/me
│       │   ├── vehicle_routes.py  # GET|PUT /vehicles, GET /vehicles/{id}
│       │   ├── alert_routes.py    # GET|POST /alerts, PATCH /alerts/{id}/acknowledge
│       │   └── trip_routes.py     # GET /trips
│       └── core/
│           ├── database.py        # SQLite(로컬) / PostgreSQL NullPool(운영) 분기
│           ├── jwt_helper.py      # JWT 인코딩/디코딩
│           ├── password.py        # bcrypt 해싱
│           ├── cors.py            # CORS 팩토리
│           └── exceptions.py      # APIException
└── fms-frontend/
    ├── vite.config.ts             # Vite proxy: /api → localhost:8000 (개발)
    ├── vercel.json                # SPA fallback (/(.*) → /index.html)
    ├── .env.production            # VITE_API_BASE_URL = AWS API Gateway URL
    └── src/
        ├── views/                 # 페이지 컴포넌트
        │   ├── auth/LoginView.vue
        │   ├── dashboard/DashboardView.vue
        │   ├── vehicles/(List|Detail)View.vue
        │   ├── alerts/AlertListView.vue
        │   └── trips/TripListView.vue
        ├── components/
        │   ├── map/RealtimeMap.vue       # Leaflet 실시간 지도
        │   ├── alert/EventAlertPanel.vue
        │   └── common/(BaseCard|StatusBadge).vue
        ├── stores/
        │   ├── auth.ts            # 로그인·토큰
        │   ├── fleet.ts           # 차량 목록, 실시간 위치, 데모 시뮬레이션
        │   ├── alert.ts           # 알림 목록·상태
        │   ├── realtime.ts        # isConnected 폴링 상태
        │   └── ui.ts              # Toast, 글로벌 로딩
        ├── services/
        │   ├── http.ts            # Axios 인스턴스 (인터셉터)
        │   └── api.ts             # 통합 API 클라이언트
        └── composables/
            └── useRealtime.ts     # HTTP 폴링 2.5초 간격
```

---

## API 엔드포인트

| Method | Path | 권한 | 설명 |
|--------|------|------|------|
| POST | `/auth/login` | Public | email+password → JWT |
| GET | `/auth/me` | 필요 | 현재 사용자 프로필 |
| GET | `/vehicles` | 필요 | 목록 (pagination, 필터, 검색) |
| GET | `/vehicles/{id}` | 필요 | 상세 (센서, 드라이버, 알림, 운행) |
| PUT | `/vehicles/{id}/telemetry` | 필요 | 센서 데이터 업데이트 |
| GET | `/alerts` | MANAGER/ADMIN | 목록 (cursor pagination) |
| POST | `/alerts` | 필요 | 알림 생성 |
| PATCH | `/alerts/{id}/acknowledge` | MANAGER/ADMIN | 알림 확인 처리 |
| GET | `/trips` | MANAGER/ADMIN | 운행 이력 목록 |

**표준 응답**: `{"data": ..., "meta": {...}}` 또는 `{"error": {"code": "...", "message": "..."}}`

---

## 데이터베이스 모델

| 테이블 | 파일 | 주요 필드 |
|--------|------|-----------|
| User | `user.py` | email, hashed_password, role(ADMIN/MANAGER/DRIVER) |
| Vehicle | `vehicle.py` | plate_number, status, driver_id(FK) |
| SensorData | `sensor_data.py` | vehicle_id, lat, lng, speed, battery, temperature, timestamp |
| Alert | `alert.py` | vehicle_id, type, severity(DANGER/WARNING/INFO), acknowledged |
| Trip | `trip.py` | vehicle_id, driver_id, start_time, end_time, distance |
| DriverProfile | `driver_profile.py` | user_id, name, license |
| ChargingStation | `charging_station.py` | name, lat, lng, status |

**DB 분기**: `core/database.py`에서 `CHALICE_STAGE` 환경변수로 SQLite(로컬) / PostgreSQL NullPool(운영) 선택

---

## 인증 및 권한

- **JWT HS256** — 토큰 유효기간: 설정 확인 필요
- **역할**: `ADMIN` > `MANAGER` > `DRIVER`
- **미들웨어**: `chalicelib/middlewares/auth.py`의 `require_role()` 데코레이터

**테스트 계정** (자동 시드):
```
admin@fms.com    / admin1234    → ADMIN
manager@fms.com  / manager1234  → MANAGER
driver1@fms.com  / driver1234   → DRIVER
```

---

## 실시간 전략

- **WebSocket 없음** — HTTP 폴링 2.5초 간격 (`useRealtime.ts`)
- **클라이언트 시뮬레이션**: RUNNING/ALERT 차량을 1.5초마다 로컬에서 이동 (`fleet.ts`)
- **서버 동기화**: 2.5초마다 실제 위치로 업데이트
- **연결 표시**: 헤더의 "● 실시간" (연결) / "○ 오프라인" (미연결)

---

## 로컬 개발

```bash
# 백엔드 (포트 8000)
cd fms-backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/chalice local --host 0.0.0.0 --port 8000

# 프론트엔드 (포트 5173)
cd fms-frontend
npm install && npm run dev

# IoT 시뮬레이터 (선택, 별도 터미널)
cd fms-backend
python simulator.py
```

- 백엔드 최초 실행 시 DB 테이블 자동 생성 및 테스트 데이터 시드
- 프론트엔드 Vite proxy: `/api/*` → `localhost:8000` (개발 환경 전용)

---

## 배포

| 컴포넌트 | 방법 | 설정 파일 |
|----------|------|----------|
| 백엔드 | `chalice deploy` | `.chalice/config.json` (256MB, 30s timeout) |
| 프론트엔드 | Vercel (자동) | `vercel.json`, `.env.production` |

```bash
# 백엔드 배포
cd fms-backend
.venv/bin/chalice deploy --stage production

# 프론트엔드 빌드 확인
cd fms-frontend
npm run build
```

---

## 작업 원칙

1. **기준 문서**: `docs/18_implementation_status.md`가 현재 구현 상태의 정답 — 다른 설계 문서와 충돌 시 이 파일 우선
2. **DB 연결**: Lambda 환경에서 반드시 `NullPool` 사용 (커넥션 풀 누수 방지)
3. **CORS**: 운영 환경에서 `https://fms-frontend-peach.vercel.app`으로만 제한
4. **오류 대응**: 즉시 수정 금지 — 근본 원인 분석 → 보고 → 수정
5. **코드 변경**: 변경된 부분만 출력, 전체 파일 재출력 금지
6. **언어**: 코드·변수명은 영어, 커밋 메시지·주석은 한국어 무방

---

## 사용 가능한 Skills

| 명령 | 설명 | 호출 시점 |
|------|------|----------|
| /plan-discovery | 1단계: 기획 (PRD, 페르소나) | 신규 기능 기획 시 |
| /plan-design | 2단계: 설계 (DB, API, 디자인 시스템) | 기획 완료 후 |
| /implement-frontend | 3단계: 프론트엔드 구현 | 설계 완료 후 |
| /implement-backend | 4단계: 백엔드 구현 | 프론트 완료 후 |
| /run-tests | 5단계: 테스트 + 통합 | 구현 완료 후 |
| /production-ready | 6단계: 운영 준비 | MVP 검증 후 |
