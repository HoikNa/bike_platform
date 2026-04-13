# API 인터페이스 명세서 (API Specification)

**프로젝트**: 지능형 오토바이 FMS  
**버전**: v1.0 | **작성일**: 2026-04-13  
**기술 스택**: AWS Chalice, Python 3.12  
**Base URL**: `https://api.bikefms.io/v1`

---

## 1. 공통 규격

### 1.1 인증

```
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

- JWT는 `RS256` 알고리즘 서명, 유효기간 1시간
- Refresh Token은 `HttpOnly Cookie`로 관리 (XSS 방어)

### 1.2 공통 응답 Envelope

```typescript
// 성공
{
  "success": true,
  "data": T,
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-04-13T09:00:00Z"
  }
}

// 에러
{
  "success": false,
  "error": {
    "code": "VEHICLE_NOT_FOUND",   // 앱 레벨 에러 코드
    "message": "차량을 찾을 수 없습니다.",
    "detail": { ... }              // 개발 환경에서만 포함
  },
  "meta": { "request_id": "req_abc123", "timestamp": "..." }
}
```

### 1.3 에러 코드 정의

| HTTP | code | 상황 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | 요청 파라미터 형식 오류 |
| 401 | `TOKEN_EXPIRED` | JWT 만료 |
| 401 | `TOKEN_INVALID` | JWT 서명 불일치 |
| 403 | `PERMISSION_DENIED` | 역할 권한 부족 |
| 404 | `NOT_FOUND` | 리소스 없음 |
| 409 | `CONFLICT` | 중복 리소스 |
| 422 | `UNPROCESSABLE` | 비즈니스 로직 검증 실패 |
| 429 | `RATE_LIMITED` | 요청 한도 초과 |
| 500 | `INTERNAL_ERROR` | 서버 내부 오류 |

---

## 2. 페이징 및 필터링 정책

### 2.1 정책 선택 기준

| 페이징 방식 | 적용 대상 | 이유 |
|---|---|---|
| **Cursor 기반** | `GET /sensor-data`, `GET /alerts` | 고빈도 삽입 테이블 — Offset 방식은 SKIP 비용 폭증 |
| **Offset/Limit 기반** | `GET /vehicles`, `GET /trips`, `GET /charging-stations` | 수량이 적고 전체 페이지 탐색 필요 |

### 2.2 Cursor 기반 페이징

실시간으로 삽입되는 센서 데이터나 알림 목록에 적용합니다.

**SensorData 전용 설계**  
`SensorData`는 `vehicle_id`가 쿼리 파라미터로 항상 고정되므로, cursor는 **`time` 하나**만으로 구성합니다.  
`Alert`는 여러 차량에 걸친 조회가 가능하므로 **`time + id`** 복합 cursor를 사용합니다.

```
# SensorData: time만으로 cursor 구성
GET /vehicles/{vehicle_id}/sensor-data?cursor=eyJ0aW1lIjoiMjAyNi0wNC0xM1QwOTowMDowMFoifQ==&limit=200

# Alert: time + id 복합 cursor
GET /alerts?cursor=eyJ0aW1lIjoiMjAyNi0wNC0xM1QwOTowMDowMFoiLCJpZCI6InV1aWQifQ==&limit=30
```

**Response**:
```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "pagination": {
      "type": "cursor",
      "next_cursor": "eyJ0aW1lIjoiMjAyNi0wNC0xM1QwOTowMDowMFoifQ==",
      "has_next": true,
      "limit": 200
    }
  }
}
```

**Cursor 인코딩 규칙** (`chalicelib/helpers/pagination.py`):
```python
import base64, json
from datetime import datetime
from uuid import UUID
from typing import Optional

def encode_cursor_time(time: datetime) -> str:
    """SensorData 전용: time 단일 cursor"""
    raw = json.dumps({"time": time.isoformat()})
    return base64.urlsafe_b64encode(raw.encode()).decode()

def encode_cursor_time_id(time: datetime, record_id: UUID) -> str:
    """Alert 전용: time + id 복합 cursor"""
    raw = json.dumps({"time": time.isoformat(), "id": str(record_id)})
    return base64.urlsafe_b64encode(raw.encode()).decode()

def decode_cursor(cursor: str) -> dict:
    # urlsafe_b64decode는 padding 없어도 동작하도록 보정
    padded = cursor + "==" * ((4 - len(cursor) % 4) % 4)
    raw = base64.urlsafe_b64decode(padded.encode()).decode()
    return json.loads(raw)
```

### 2.3 Offset 기반 페이징

```
GET /vehicles?page=1&limit=20
```

**Response**:
```json
{
  "data": {
    "items": [ ... ],
    "pagination": {
      "type": "offset",
      "total": 150,
      "page": 1,
      "limit": 20,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### 2.4 공통 필터링 규칙

| 파라미터 패턴 | 예시 | 동작 |
|---|---|---|
| 단일 값 | `status=ACTIVE` | 정확 일치 |
| 다중 값 | `status=ACTIVE&status=CHARGING` | OR 조건 |
| 범위 (시작) | `created_after=2026-04-01T00:00:00Z` | >= |
| 범위 (종료) | `created_before=2026-04-13T23:59:59Z` | <= |
| 정렬 | `sort_by=created_at&order=desc` | 컬럼 + 방향 |
| 텍스트 검색 | `q=홍길동` | ILIKE `%q%` |

---

## 3. API 엔드포인트 명세

### 3.1 인증 (Auth)

#### `POST /auth/login`

```
POST /auth/login
Content-Type: application/json
```

**Request**:
```json
{ "username": "admin01", "password": "P@ssw0rd!" }
```

**Response 200**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "550e8400-...",
      "username": "admin01",
      "role": "ADMIN",
      "is_active": true
    }
  }
}
```

**Response 401** (`TOKEN_INVALID`):
```json
{
  "success": false,
  "error": { "code": "TOKEN_INVALID", "message": "아이디 또는 비밀번호가 올바르지 않습니다." }
}
```

---

#### `POST /auth/refresh`

**Request**: Body 없음 — `RefreshToken`이 `HttpOnly Cookie`로 자동 전송됨

**Response 200**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

**Response 401** (RefreshToken 만료 또는 없음):
```json
{
  "success": false,
  "error": { "code": "TOKEN_INVALID", "message": "세션이 만료되었습니다. 다시 로그인해주세요." }
}
```

---

#### `GET /auth/me` — 현재 사용자 정보 조회

토큰 갱신 후 `currentUser` 객체 복원에 사용합니다.

**Response 200**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-...",
    "username": "admin01",
    "role": "ADMIN",
    "is_active": true,
    "driver_profile": null
  }
}
```

---

#### `POST /auth/logout`

RefreshToken Cookie 무효화  
**Response 200**: `{ "success": true, "data": { "message": "로그아웃 되었습니다." } }`

---

### 3.2 차량 (Vehicles)

#### `GET /vehicles` — 목록 조회 (Offset 페이징)

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `status` | `string[]` | N | ACTIVE / INACTIVE / MAINTENANCE / CHARGING |
| `driver_id` | `UUID` | N | 특정 운전자 배정 차량 |
| `q` | `string` | N | plate_number, model_name 텍스트 검색 |
| `page` | `int` | N | default: 1 |
| `limit` | `int` | N | default: 20, max: 100 |
| `sort_by` | `string` | N | created_at / plate_number / status |
| `order` | `string` | N | asc / desc (default: desc) |

**Response 200**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "plate_number": "12가 3456",
        "model_name": "Honda PCX 125e",
        "imei": "358000000000001",
        "status": "ACTIVE",
        "odometer_km": 12450,
        "assigned_driver": {
          "id": "...",
          "username": "driver01",
          "phone": "010-1234-5678"
        },
        "last_state": {
          "latitude": 37.5665,
          "longitude": 126.9780,
          "speed_kmh": 45.2,
          "soc_pct": 78.5,
          "engine_temp_c": 85.3,
          "updated_at": "2026-04-13T09:00:00Z"
        },
        "created_at": "2025-01-15T10:00:00Z"
      }
    ],
    "pagination": {
      "type": "offset",
      "total": 150,
      "page": 1,
      "limit": 20,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

#### `GET /vehicles/{vehicle_id}` — 단건 조회

**Response 200**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-...",
    "plate_number": "12가 3456",
    "model_name": "Honda PCX 125e",
    "vin": "JH2PC44CXMM000001",
    "imei": "358000000000001",
    "status": "ACTIVE",
    "odometer_km": 12450,
    "assigned_driver": { ... },
    "active_trip": {
      "id": "trip-uuid",
      "started_at": "2026-04-13T08:00:00Z",
      "distance_km": 25.3,
      "alert_count": 1
    },
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

**Response 404**:
```json
{ "success": false, "error": { "code": "NOT_FOUND", "message": "차량을 찾을 수 없습니다." } }
```

---

#### `POST /vehicles` — 차량 등록 `[ADMIN, MANAGER]`

**Request**:
```json
{
  "plate_number": "99나 8765",
  "model_name": "Yamaha EC-05",
  "vin": "JYACE18E6FA000001",
  "imei": "358000000000099"
}
```

**Response 201**:
```json
{ "success": true, "data": { "id": "new-uuid", "plate_number": "99나 8765", ... } }
```

**Response 409** (중복 plate_number):
```json
{ "success": false, "error": { "code": "CONFLICT", "message": "이미 등록된 차량번호입니다." } }
```

---

#### `PUT /vehicles/{vehicle_id}` — 차량 정보 수정 `[ADMIN, MANAGER]`

**Request** (변경할 필드만 전송):
```json
{
  "status": "MAINTENANCE",
  "assigned_driver_id": "driver-uuid-001"
}
```

---

#### `DELETE /vehicles/{vehicle_id}` — 차량 논리 삭제 `[ADMIN]`

논리 삭제 (`deleted_at` 설정) — SensorData 보존

**Response 200**:
```json
{ "success": true, "data": { "id": "...", "deleted_at": "2026-04-13T09:00:00Z" } }
```

---

### 3.3 센서 데이터 (Sensor Data)

#### `GET /vehicles/{vehicle_id}/sensor-data` — 시계열 데이터 조회 (Cursor 페이징)

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `start_time` | `ISO8601` | Y | 조회 시작 시각 |
| `end_time` | `ISO8601` | Y | 조회 종료 시각 (최대 범위: 24시간) |
| `fields` | `string[]` | N | 반환 필드 선택 (예: `fields=latitude&fields=speed_kmh`) |
| `cursor` | `string` | N | 다음 페이지 커서 |
| `limit` | `int` | N | default: 200, max: 1000 |

**Response 200**:
```json
{
  "success": true,
  "data": {
    "vehicle_id": "550e8400-...",
    "items": [
      {
        "time": "2026-04-13T08:00:00Z",
        "latitude": 37.5665,
        "longitude": 126.9780,
        "speed_kmh": 0.0,
        "soc_pct": 82.0,
        "engine_temp_c": 20.5
      }
    ],
    "pagination": {
      "type": "cursor",
      "next_cursor": "eyJ0aW1lIjoiMjAyNi0wNC0xM1QwOTowMDowMFoifQ==",
      "has_next": true,
      "limit": 200
    }
  }
}
```

> **최대 조회 범위**: 단일 요청 24시간. 초과 시 `422 UNPROCESSABLE` 반환.

---

#### `GET /vehicles/{vehicle_id}/sensor-data/latest` — 최신 스냅샷

Redis 캐시에서 즉시 반환. DB 조회 없음.

**Response 200**:
```json
{
  "success": true,
  "data": {
    "time": "2026-04-13T09:00:05Z",
    "latitude": 37.5666,
    "longitude": 126.9782,
    "speed_kmh": 45.3,
    "soc_pct": 72.5,
    "soh_pct": 91.2,
    "engine_temp_c": 88.5,
    "remaining_km": 38.5,
    "source": "cache"
  }
}
```

---

### 3.4 알림 (Alerts)

#### `GET /alerts` — 알림 목록 (Cursor 페이징)

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `vehicle_id` | `UUID` | N | 특정 차량 필터 |
| `driver_id` | `UUID` | N | 특정 운전자 필터 |
| `type` | `string[]` | N | OVERSPEED / BATTERY_LOW / ... |
| `severity` | `string[]` | N | INFO / WARNING / CRITICAL |
| `is_resolved` | `bool` | N | 처리 여부 |
| `created_after` | `ISO8601` | N | |
| `created_before` | `ISO8601` | N | |
| `cursor` | `string` | N | 페이지 커서 |
| `limit` | `int` | N | default: 30, max: 100 |

**Response 200**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "alert-uuid-001",
        "vehicle_id": "...",
        "plate_number": "12가 3456",
        "driver_name": "홍길동",
        "type": "OVERSPEED",
        "severity": "WARNING",
        "payload": {
          "speed_kmh": 78.5,
          "speed_limit_kmh": 60,
          "latitude": 37.5200,
          "longitude": 127.0100
        },
        "is_resolved": false,
        "created_at": "2026-04-13T08:45:00Z"
      }
    ],
    "pagination": {
      "type": "cursor",
      "next_cursor": "eyJ0aW1lIjoi...",
      "has_next": true,
      "limit": 30
    }
  }
}
```

---

#### `PATCH /alerts/{alert_id}/resolve` — 알림 처리 `[ADMIN, MANAGER]`

**Request**:
```json
{ "comment": "운전자에게 경고 전달 완료" }
```

**Response 200**:
```json
{
  "success": true,
  "data": {
    "id": "alert-uuid-001",
    "is_resolved": true,
    "resolved_by": { "id": "...", "username": "manager01" },
    "resolved_at": "2026-04-13T09:05:00Z"
  }
}
```

---

### 3.5 운행 이력 (Trips)

#### `GET /vehicles/{vehicle_id}/trips` — 운행 이력 목록 (Offset 페이징)

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `start_date` | `ISO8601` | Y | 조회 시작 |
| `end_date` | `ISO8601` | Y | 조회 종료 |
| `status` | `string[]` | N | IN_PROGRESS / COMPLETED / INTERRUPTED |
| `page` | `int` | N | default: 1 |
| `limit` | `int` | N | default: 20 |

**Response 200**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "trip-uuid-001",
        "started_at": "2026-04-13T08:00:00Z",
        "ended_at": "2026-04-13T09:30:00Z",
        "duration_minutes": 90,
        "distance_km": 45.2,
        "avg_speed_kmh": 30.1,
        "max_speed_kmh": 68.5,
        "energy_consumed_wh": 850.3,
        "alert_count": 2,
        "status": "COMPLETED"
      }
    ],
    "summary": {
      "total_trips": 12,
      "total_distance_km": 420.5,
      "total_alerts": 8
    },
    "pagination": {
      "type": "offset",
      "total": 12,
      "page": 1,
      "limit": 20,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

---

### 3.6 충전소 (Charging Stations)

#### `GET /charging-stations` — 목록 조회 (Offset 페이징 + 공간 필터)

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `lat` | `float` | N | 기준 위도 (lng와 함께 사용 시 근거리 정렬) |
| `lng` | `float` | N | 기준 경도 |
| `radius_m` | `int` | N | 검색 반경 (m, default: 5000, max: 20000) |
| `status` | `string[]` | N | OPEN / FULL / CLOSED |
| `min_slots` | `int` | N | 최소 잔여 슬롯 수 |
| `page` | `int` | N | default: 1 |
| `limit` | `int` | N | default: 10, max: 50 |

**Response 200**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "station-uuid-001",
        "name": "명동 전기오토바이 충전소",
        "address": "서울 중구 명동 2가 34-1",
        "latitude": 37.5638,
        "longitude": 126.9830,
        "distance_m": 450,
        "total_slots": 10,
        "available_slots": 4,
        "status": "OPEN",
        "updated_at": "2026-04-13T09:00:00Z"
      }
    ],
    "pagination": {
      "type": "offset",
      "total": 5,
      "page": 1,
      "limit": 10,
      "total_pages": 1,
      "has_next": false
    }
  }
}
```

---

### 3.7 사용자 / 운전자 (Users & Drivers)

#### `GET /users` — 사용자 목록 `[ADMIN, MANAGER]`

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `role` | `string[]` | ADMIN / MANAGER / DRIVER |
| `is_active` | `bool` | 활성 계정 필터 |
| `q` | `string` | username, email 검색 |
| `page` / `limit` | `int` | Offset 페이징 |

**Response 200**: Offset 페이징 형식, `items`에 User 객체 목록

---

#### `POST /users` — 사용자 생성 `[ADMIN]`

**Request**:
```json
{
  "username": "driver_new",
  "email": "new@bikefms.io",
  "password": "TempP@ss1!",
  "role": "DRIVER",
  "phone": "010-9999-8888"
}
```

**Response 201**: 생성된 User 객체 (password_hash 제외)  
**Response 409**: `{ "error": { "code": "CONFLICT", "message": "이미 사용 중인 username입니다." } }`

---

#### `PUT /users/{user_id}` — 사용자 수정 `[ADMIN]`

**Request** (변경 필드만):
```json
{ "is_active": false, "role": "MANAGER" }
```

---

#### `DELETE /users/{user_id}` — 사용자 논리 삭제 `[ADMIN]`

`deleted_at` 설정. DriverProfile은 CASCADE 물리 삭제됨.

---

#### `GET /users/{user_id}/driver-profile` — 운전자 프로필 조회 `[ADMIN, MANAGER]`

**Response 200**:
```json
{
  "success": true,
  "data": {
    "id": "...",
    "user_id": "...",
    "license_number": "12-34-567890-00",
    "license_expiry": "2028-06-30",
    "assigned_zone": "서울 강남구"
  }
}
```

---

#### `POST /users/{user_id}/driver-profile` — 운전자 프로필 생성 `[ADMIN, MANAGER]`

`role=DRIVER` 인 User에 한해 생성 가능.

**Request**:
```json
{
  "license_number": "12-34-567890-00",
  "license_expiry": "2028-06-30",
  "assigned_zone": "서울 강남구"
}
```

---

## 4. Chalice Route 권한 매트릭스

| Endpoint | ADMIN | MANAGER | DRIVER |
|---|:---:|:---:|:---:|
| `GET /vehicles` | ✅ | ✅ | 자신 배정 차량만 |
| `POST /vehicles` | ✅ | ✅ | ❌ |
| `PUT /vehicles/{id}` | ✅ | ✅ | ❌ |
| `DELETE /vehicles/{id}` | ✅ | ❌ | ❌ |
| `GET /sensor-data` | ✅ | ✅ | 자신 배정 차량만 |
| `GET /alerts` | ✅ | ✅ | 자신 관련만 |
| `PATCH /alerts/{id}/resolve` | ✅ | ✅ | ❌ |
| `GET /charging-stations` | ✅ | ✅ | ✅ |
| `POST /charging-stations` | ✅ | ❌ | ❌ |
| `GET /users` | ✅ | ✅ | ❌ |
| `POST /users` | ✅ | ❌ | ❌ |
| `PUT /users/{id}` | ✅ | ❌ | ❌ |
| `DELETE /users/{id}` | ✅ | ❌ | ❌ |
| `GET /users/{id}/driver-profile` | ✅ | ✅ | 자신만 |
| `POST /users/{id}/driver-profile` | ✅ | ✅ | ❌ |
| `GET /auth/me` | ✅ | ✅ | ✅ |
