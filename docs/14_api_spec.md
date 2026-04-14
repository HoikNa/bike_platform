# 14. API Spec — 인터페이스 명세서

> **스택**: AWS Chalice (Python) · Vue3 (TypeScript)  
> **인증**: JWT HS256 — `Authorization: Bearer <access_token>`  
> **공통 응답 봉투(Envelope)**: 모든 REST 응답은 `{ success, data, meta }` 구조를 따릅니다.  
>
> **구현 상태 표기**: ✅ 구현됨 | ⚠️ 설계만 존재 (미구현)  
> 실제 구현 현황의 정확한 내용은 [18_implementation_status.md](18_implementation_status.md) 문서를 우선 참조하세요.

---

> ### 프로덕션 BaseURL
> `https://gmbsw71bng.execute-api.ap-northeast-2.amazonaws.com/api`

---

## 목차

1. [공통 규격](#1-공통-규격)
   - 1.1 응답 봉투 (Response Envelope)
   - 1.2 인증 및 권한
   - 1.3 페이지네이션 전략
   - 1.4 공통 에러 응답
2. [REST API — 인증](#2-rest-api--인증)
3. [REST API — 차량](#3-rest-api--차량)
4. [REST API — 센서 데이터](#4-rest-api--센서-데이터)
5. [REST API — 알림(Alert)](#5-rest-api--알림alert)
6. [REST API — 운행 기록(Trip)](#6-rest-api--운행-기록trip)
7. [REST API — 충전소](#7-rest-api--충전소)
8. [REST API — 사용자 및 운전자](#8-rest-api--사용자-및-운전자)
9. [MQTT — 단말기 → 서버 (Device Telemetry)](#9-mqtt--단말기--서버)
10. [WebSocket — 서버 → 클라이언트 (Realtime Push)](#10-websocket--서버--클라이언트)
11. [권한 매트릭스](#11-권한-매트릭스)

---

## 1. 공통 규격

### 1.1 응답 봉투 (Response Envelope)

모든 REST API는 아래 봉투 구조로 응답합니다. 프론트엔드의 Axios 인터셉터가 이 구조를 기준으로 `data`를 추출합니다.

**성공 응답 (단건)**
```json
{
  "success": true,
  "data": { ... },
  "meta": null
}
```

**성공 응답 (목록 — Offset 페이지네이션)**
```json
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "total": 247,
    "page": 2,
    "page_size": 20,
    "total_pages": 13
  }
}
```

**성공 응답 (목록 — Cursor 페이지네이션)**
```json
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "next_cursor": "eyJ0aW1lIjogIjIwMjYtMDQtMTNUMDk6MDA6MDBaIn0=",
    "has_next": true,
    "limit": 50
  }
}
```

**에러 응답**
```json
{
  "success": false,
  "data": null,
  "meta": null,
  "error": {
    "code": "VEHICLE_NOT_FOUND",
    "message": "요청한 차량을 찾을 수 없습니다.",
    "detail": null
  }
}
```

---

### 1.2 인증 및 권한

| 방식 | 설명 |
|---|---|
| 알고리즘 | **HS256** (단일 시크릿 키) — 설계의 RS256에서 변경 |
| Access Token | 만료: 1시간, `Authorization: Bearer <token>` 헤더로 전달 |
| Refresh Token | ⚠️ 미구현 (쿠키 방식 설계되었으나 실제 사용 안 함) |
| 토큰 갱신 | ⚠️ `POST /auth/refresh` 미구현 — 만료 시 재로그인 필요 |

**JWT Payload 구조**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@fms.io",
  "role": "ADMIN",
  "iat": 1744123456,
  "exp": 1744127056
}
```

---

### 1.3 페이지네이션 전략

| 테이블 | 방식 | 이유 |
|---|---|---|
| `Vehicle` | **Offset** | 총 수백 건 이하, 전체 페이지 수 표시 필요 |
| `Trip` | **Offset** | 차량당 수백~수천 건, 페이지 이동 UI 필요 |
| `User` | **Offset** | 관리자 목록, 전체 건수 표시 필요 |
| `SensorData` | **Cursor (time)** | 분당 수만 건, `OFFSET`은 깊은 페이지에서 O(n) 풀스캔 발생 |
| `Alert` | **Cursor (time + id)** | 무한 스크롤 UI, 실시간 삽입으로 Offset 기준 불안정 |

**Cursor 인코딩 규칙**

```python
# chalicelib/utils/cursor.py
import base64
import json
from datetime import datetime
from uuid import UUID


def encode_cursor_time(time: datetime) -> str:
    """SensorData 전용 — time 단일 커서."""
    raw = json.dumps({"time": time.isoformat()})
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def encode_cursor_time_id(time: datetime, record_id: UUID) -> str:
    """Alert 전용 — time + id 복합 커서 (실시간 삽입 시 중복 방지)."""
    raw = json.dumps({"time": time.isoformat(), "id": str(record_id)})
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> dict:
    """커서 디코딩 — 패딩 복원 후 JSON 파싱."""
    padded = cursor + "==" * ((4 - len(cursor) % 4) % 4)
    return json.loads(base64.urlsafe_b64decode(padded).decode())
```

---

### 1.4 공통 에러 응답

#### HTTP Status Code 정책

| HTTP 코드 | 의미 | 사용 상황 |
|---|---|---|
| `200 OK` | 성공 | 조회, 수정 성공 |
| `201 Created` | 생성 성공 | 새 리소스 생성 |
| `204 No Content` | 삭제 성공 | DELETE 후 본문 없음 |
| `400 Bad Request` | 잘못된 요청 | 파라미터 유효성 오류 |
| `401 Unauthorized` | 인증 실패 | 토큰 없음, 만료, 서명 불일치 |
| `403 Forbidden` | 권한 없음 | 역할(Role) 미충족 |
| `404 Not Found` | 리소스 없음 | ID 오류, Soft Delete된 항목 |
| `409 Conflict` | 중복 충돌 | 이메일/번호판 중복 |
| `422 Unprocessable Entity` | 비즈니스 규칙 위반 | 삭제 불가 상태 등 |
| `500 Internal Server Error` | 서버 오류 | 예상치 못한 예외 |

#### 에러 코드 목록

| `error.code` | HTTP | 설명 |
|---|---|---|
| `INVALID_CREDENTIALS` | 401 | 이메일 또는 비밀번호 불일치 |
| `TOKEN_EXPIRED` | 401 | Access Token 만료 |
| `TOKEN_INVALID` | 401 | 서명 불일치 또는 변조 |
| `FORBIDDEN` | 403 | 역할 권한 부족 |
| `VEHICLE_NOT_FOUND` | 404 | 차량 없음 또는 삭제됨 |
| `USER_NOT_FOUND` | 404 | 사용자 없음 또는 삭제됨 |
| `ALERT_NOT_FOUND` | 404 | 알림 없음 |
| `TRIP_NOT_FOUND` | 404 | 운행 기록 없음 |
| `DUPLICATE_EMAIL` | 409 | 이메일 중복 |
| `DUPLICATE_PLATE` | 409 | 차량 번호판 중복 |
| `VEHICLE_HAS_DATA` | 422 | 센서 데이터가 존재해 삭제 불가 |
| `DRIVER_ALREADY_ASSIGNED` | 422 | 이미 다른 차량에 배차된 기사 |
| `VALIDATION_ERROR` | 400 | 요청 바디/쿼리 파라미터 유효성 오류 |
| `INTERNAL_ERROR` | 500 | 서버 내부 오류 |

**`VALIDATION_ERROR` 상세 응답 예시**
```json
{
  "success": false,
  "data": null,
  "meta": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "요청 데이터가 유효하지 않습니다.",
    "detail": [
      { "field": "email", "message": "올바른 이메일 형식이 아닙니다." },
      { "field": "role",  "message": "허용된 값: ADMIN, MANAGER, DRIVER" }
    ]
  }
}
```

---

## 2. REST API — 인증

**Base Path**: `/auth`

---

### `POST /auth/login` ✅

> 이메일·비밀번호로 로그인하여 Access Token을 발급합니다.  
> **인증 불필요** (Public)

**Request Body**
```json
{
  "email": "admin@fms.io",
  "password": "P@ssw0rd!"
}
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `email` | `string` | ✅ | 로그인 이메일 |
| `password` | `string` | ✅ | 평문 비밀번호 (TLS 전송) |

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "admin@fms.io",
      "full_name": "홍길동",
      "role": "ADMIN"
    }
  },
  "meta": null
}
```

> Refresh Token은 `Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Path=/auth/refresh` 응답 헤더로 전달됩니다.

**Error Cases**

| HTTP | `error.code` | 상황 |
|---|---|---|
| 401 | `INVALID_CREDENTIALS` | 이메일/비밀번호 불일치 |
| 400 | `VALIDATION_ERROR` | 이메일 형식 오류 |

---

### `POST /auth/refresh` ⚠️ 미구현

> Refresh Token 쿠키를 검증하여 새 Access Token을 발급합니다.  
> **인증 불필요** (쿠키로 인증)

**Request**: Body 없음. `Cookie: refresh_token=...` 헤더 자동 전달.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  },
  "meta": null
}
```

**Error Cases**

| HTTP | `error.code` | 상황 |
|---|---|---|
| 401 | `TOKEN_EXPIRED` | Refresh Token 만료 (재로그인 필요) |
| 401 | `TOKEN_INVALID` | 쿠키 없음 또는 서명 불일치 |

---

### `GET /auth/me` ✅

> 현재 Access Token의 사용자 정보를 반환합니다.  
> 페이지 새로고침 후 `currentUser` 복원에 사용합니다.  
> **인증 필요** (`Bearer`)

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@fms.io",
    "full_name": "홍길동",
    "role": "ADMIN",
    "is_active": true
  },
  "meta": null
}
```

---

### `POST /auth/logout` ⚠️ 미구현

> Refresh Token 쿠키를 무효화합니다. (서버 측 블랙리스트 + 쿠키 만료 설정)  
> **인증 필요** (`Bearer`)

**Response `204 No Content`**

---

## 3. REST API — 차량

**Base Path**: `/vehicles`  
**인증 필요**: 모든 엔드포인트 (`Bearer`)

---

### `GET /vehicles` ✅

> 차량 목록 조회. Soft Delete된 차량은 기본 제외됩니다.

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `page` | `integer` | `1` | 페이지 번호 |
| `page_size` | `integer` | `20` | 페이지당 건수 (최대 100) |
| `status` | `string[]` | — | 차량 상태 필터 (다중 가능: `?status=RUNNING&status=ALERT`) |
| `q` | `string` | — | 번호판 또는 모델명 검색 (부분 일치) |
| `include_deleted` | `boolean` | `false` | Soft Delete 포함 여부 (ADMIN 전용) |

> **Chalice 다중 값 파라미터**: `request.multi_query_params.get("status") or []`

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "a1b2c3d4-...",
      "plate_number": "서울12가3456",
      "model": "PCX Electric",
      "manufacturer": "Honda",
      "status": "RUNNING",
      "battery_capacity_kwh": 3.0,
      "assigned_driver": {
        "id": "d1e2f3...",
        "user_full_name": "김철수",
        "phone": "010-1234-5678"
      },
      "latest_sensor": {
        "time": "2026-04-13T09:43:21Z",
        "latitude": 37.5012,
        "longitude": 127.0396,
        "speed_kmh": 42.5,
        "battery_level_pct": 68.2
      },
      "created_at": "2025-01-15T00:00:00Z"
    }
  ],
  "meta": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

---

### `POST /vehicles` ⚠️ 미구현

> 신규 차량 등록.  
> **권한**: `ADMIN`, `MANAGER`

**Request Body**
```json
{
  "plate_number": "서울12가3456",
  "model": "PCX Electric",
  "manufacturer": "Honda",
  "manufacture_year": 2025,
  "battery_capacity_kwh": 3.0,
  "vin": "1HGBH41JXMN109186"
}
```

| 필드 | 타입 | 필수 | 제약 |
|---|---|---|---|
| `plate_number` | `string` | ✅ | 고유, 최대 20자 |
| `model` | `string` | ✅ | 최대 100자 |
| `manufacturer` | `string` | ✅ | 최대 50자 |
| `manufacture_year` | `integer` | ✅ | 2000 이상 |
| `battery_capacity_kwh` | `float` | ✅ | 0 초과 |
| `vin` | `string` | — | 17자 고유 |

**Response `201 Created`**
```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-...",
    "plate_number": "서울12가3456",
    "status": "OFFLINE",
    "created_at": "2026-04-13T10:00:00Z"
  },
  "meta": null
}
```

**Error Cases**

| HTTP | `error.code` | 상황 |
|---|---|---|
| 409 | `DUPLICATE_PLATE` | 번호판 중복 |
| 400 | `VALIDATION_ERROR` | 필수 필드 누락 또는 형식 오류 |

---

### `GET /vehicles/{vehicle_id}` ✅

> 차량 상세 조회. 최신 센서 데이터 및 진행 중인 운행 정보 포함.

**Path Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `vehicle_id` | `UUID` | 차량 ID |

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-...",
    "plate_number": "서울12가3456",
    "model": "PCX Electric",
    "manufacturer": "Honda",
    "manufacture_year": 2025,
    "status": "RUNNING",
    "battery_capacity_kwh": 3.0,
    "vin": "1HGBH41JXMN109186",
    "assigned_driver": {
      "id": "d1e2f3...",
      "user_full_name": "김철수",
      "license_number": "12-34-567890-01",
      "license_expiry": "2028-06-30",
      "phone": "010-1234-5678"
    },
    "latest_sensor": {
      "time": "2026-04-13T09:43:21Z",
      "latitude": 37.5012,
      "longitude": 127.0396,
      "speed_kmh": 42.5,
      "battery_level_pct": 68.2,
      "battery_voltage_v": 72.4,
      "battery_temp_celsius": 28.1,
      "engine_rpm": 3200,
      "odometer_km": 12453.7
    },
    "active_trip": {
      "id": "t1r2i3p4-...",
      "started_at": "2026-04-13T08:00:00Z",
      "start_address": "서울시 강남구 테헤란로 123"
    },
    "unacknowledged_alerts_count": 2,
    "created_at": "2025-01-15T00:00:00Z",
    "updated_at": "2026-04-13T09:43:21Z"
  },
  "meta": null
}
```

---

### `PUT /vehicles/{vehicle_id}` ⚠️ 미구현

> 차량 정보 수정.  
> **권한**: `ADMIN`, `MANAGER`

**Request Body** (변경할 필드만 포함 — 부분 업데이트)
```json
{
  "model": "PCX Electric 2026",
  "assigned_driver_id": "d1e2f3a4-..."
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `model` | `string` | 모델명 변경 |
| `manufacture_year` | `integer` | 제조 연도 변경 |
| `battery_capacity_kwh` | `float` | 배터리 용량 변경 |
| `assigned_driver_id` | `UUID \| null` | 배차 변경 (`null` = 미배차) |

**Response `200 OK`**: 수정된 차량 상세 응답 (단건 조회와 동일 구조)

**Error Cases**

| HTTP | `error.code` | 상황 |
|---|---|---|
| 404 | `VEHICLE_NOT_FOUND` | 차량 없음 |
| 422 | `DRIVER_ALREADY_ASSIGNED` | 해당 기사가 다른 차량에 이미 배차됨 |

---

### `DELETE /vehicles/{vehicle_id}`

> ⚠️ **미구현** — 설계만 존재  
> 차량 Soft Delete.  
> **권한**: `ADMIN`

**Response `204 No Content`**

**Error Cases**

| HTTP | `error.code` | 상황 |
|---|---|---|
| 422 | `VEHICLE_HAS_DATA` | 센서 데이터 또는 알림이 존재하여 삭제 불가 (아카이브 배치 선행 필요) |

---

### `PUT /vehicles/{vehicle_id}/telemetry` ✅

> IoT 단말기 또는 시뮬레이터(`simulator.py`)가 실시간 센서 데이터를 전송합니다.  
> 수신 즉시 SensorData 행을 삽입하고 Vehicle 상태(`RUNNING` / `IDLE`)를 갱신합니다.  
> **권한**: `DRIVER`, `MANAGER`, `ADMIN`

**Path Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `vehicle_id` | `UUID` | 차량 ID |

**Request Body**
```json
{
  "latitude": 37.5012,
  "longitude": 127.0396,
  "speed_kmh": 42.5,
  "battery_level_pct": 68.2,
  "engine_temp_celsius": 72.3
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `latitude` | `float` | 위도 |
| `longitude` | `float` | 경도 |
| `speed_kmh` | `float` | 속도 (km/h). 0 초과 시 → RUNNING, 0 이하 → IDLE |
| `battery_level_pct` | `float` | 배터리 잔량 (%) |
| `engine_temp_celsius` | `float` | 엔진 온도 (°C) |

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "vehicle_id": "a1b2c3d4-...",
    "status": "RUNNING",
    "recorded_at": "2026-04-15T01:23:45.123456Z"
  },
  "meta": null
}
```

**Error Cases**

| HTTP | `error.code` | 상황 |
|---|---|---|
| 404 | `NOT_FOUND` | 차량 없음 |
| 401 | `TOKEN_INVALID` | 인증 실패 |

---

## 4. REST API — 센서 데이터

> ⚠️ **이 섹션의 모든 엔드포인트는 미구현입니다.**  
> 센서 데이터는 `PUT /vehicles/{id}/telemetry` 로 수신 후 DB에만 저장되며, 조회 API는 아직 없습니다.

**Base Path**: `/vehicles/{vehicle_id}/sensors`  
**인증 필요**: `Bearer`  
**페이지네이션**: Cursor-based (time 커서)

---

### `GET /vehicles/{vehicle_id}/sensors` ⚠️ 미구현

> 특정 차량의 센서 데이터 이력 조회 (시계열, 최신순).  
> 무한 스크롤 또는 그래프 차트 데이터 로드에 사용합니다.

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `limit` | `integer` | `50` | 반환할 건수 (최대 500) |
| `cursor` | `string` | — | 이전 응답의 `next_cursor` 값 |
| `from` | `ISO8601` | — | 조회 시작 시각 (`cursor` 없을 때) |
| `to` | `ISO8601` | — | 조회 종료 시각 |
| `fields` | `string[]` | all | 반환 필드 선택 (예: `?fields=time&fields=speed_kmh&fields=battery_level_pct`) |

**커서 기반 쿼리 로직**

```python
# chalicelib/repositories/sensor_data_repository.py
from chalicelib.utils.cursor import decode_cursor
from sqlalchemy import and_
from sqlmodel import select

def list_by_vehicle(
    self,
    vehicle_id: UUID,
    limit: int = 50,
    cursor: str | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
) -> list[SensorData]:
    stmt = (
        select(SensorData)
        .where(SensorData.vehicle_id == vehicle_id)
        .order_by(SensorData.time.desc())
        .limit(limit + 1)  # 다음 페이지 존재 여부 확인용 +1
    )
    if cursor:
        payload = decode_cursor(cursor)
        # time < cursor_time (이미 본 데이터 제외)
        stmt = stmt.where(SensorData.time < datetime.fromisoformat(payload["time"]))
    else:
        if from_time:
            stmt = stmt.where(SensorData.time >= from_time)
        if to_time:
            stmt = stmt.where(SensorData.time <= to_time)
    return self.session.exec(stmt).all()
```

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "time": "2026-04-13T09:43:21Z",
      "latitude": 37.5012,
      "longitude": 127.0396,
      "speed_kmh": 42.5,
      "battery_level_pct": 68.2,
      "battery_voltage_v": 72.4,
      "battery_temp_celsius": 28.1,
      "engine_rpm": 3200,
      "odometer_km": 12453.7,
      "throttle_pct": 45.2,
      "brake_engaged": false,
      "signal_strength_dbm": -78
    }
  ],
  "meta": {
    "next_cursor": "eyJ0aW1lIjogIjIwMjYtMDQtMTNUMDk6NDM6MjFaIn0",
    "has_next": true,
    "limit": 50
  }
}
```

---

### `GET /vehicles/{vehicle_id}/sensors/latest`

> 특정 차량의 가장 최신 센서 데이터 1건 조회.  
> 차량 상세 카드의 실시간 데이터 표시에 사용합니다.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "time": "2026-04-13T09:43:21Z",
    "latitude": 37.5012,
    "longitude": 127.0396,
    "speed_kmh": 42.5,
    "battery_level_pct": 68.2,
    "battery_voltage_v": 72.4,
    "battery_temp_celsius": 28.1,
    "engine_rpm": 3200,
    "odometer_km": 12453.7
  },
  "meta": null
}
```

---

## 5. REST API — 알림(Alert)

**Base Path**: `/alerts`  
**인증 필요**: `Bearer`  
**페이지네이션**: Cursor-based (time + id 복합 커서)

---

### `GET /alerts` ✅

> 알림 목록 조회. 최신순 정렬.

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `limit` | `integer` | `30` | 반환 건수 (최대 100) |
| `cursor` | `string` | — | 복합 커서 (time+id) |
| `vehicle_id` | `UUID` | — | 특정 차량 필터 |
| `severity` | `string[]` | — | 심각도 필터 (`INFO`, `WARNING`, `DANGER`) |
| `alert_type` | `string[]` | — | 알림 유형 필터 |
| `is_acknowledged` | `boolean` | — | 확인 여부 필터 (`false` = 미확인만) |
| `from` | `ISO8601` | — | 조회 시작 시각 |
| `to` | `ISO8601` | — | 조회 종료 시각 |

**커서 기반 쿼리 로직 (time + id 복합)**

```python
# chalicelib/repositories/alert_repository.py
# 동일 시각에 여러 알림이 생성될 수 있으므로 id를 함께 사용합니다.
def list_alerts(self, cursor: str | None, limit: int) -> list[Alert]:
    stmt = select(Alert).order_by(Alert.triggered_at.desc(), Alert.id.desc()).limit(limit + 1)

    if cursor:
        payload = decode_cursor(cursor)
        cursor_time = datetime.fromisoformat(payload["time"])
        cursor_id   = UUID(payload["id"])
        # (triggered_at, id) < (cursor_time, cursor_id) — 복합 비교
        stmt = stmt.where(
            or_(
                Alert.triggered_at < cursor_time,
                and_(
                    Alert.triggered_at == cursor_time,
                    Alert.id < cursor_id,
                ),
            )
        )
    return self.session.exec(stmt).all()
```

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "f1a2b3c4-...",
      "vehicle": {
        "id": "a1b2c3d4-...",
        "plate_number": "서울12가3456"
      },
      "triggered_at": "2026-04-13T09:40:00Z",
      "alert_type": "OVERSPEED",
      "severity": "DANGER",
      "title": "과속 감지 — 92km/h (제한 60km/h)",
      "description": "제한속도 53% 초과. 즉각 주의 요망.",
      "speed_at_trigger": 92.3,
      "battery_at_trigger": 65.0,
      "location_lat": 37.5015,
      "location_lng": 127.0401,
      "is_acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null,
      "created_at": "2026-04-13T09:40:01Z"
    }
  ],
  "meta": {
    "next_cursor": "eyJ0aW1lIjogIjIwMjYtMDQtMTNUMDk6NDA6MDBaIiwgImlkIjogImYxYTJiM2M0LSJ9",
    "has_next": true,
    "limit": 30
  }
}
```

---

### `POST /alerts` ✅

> 시뮬레이터(`simulator.py`) 또는 이벤트 감지기가 알림을 직접 생성합니다.  
> **권한**: `DRIVER`, `MANAGER`, `ADMIN`

**Request Body**
```json
{
  "vehicle_id": "a1b2c3d4-...",
  "alert_type": "OVERSPEED",
  "severity": "DANGER",
  "title": "과속 감지 — 92km/h",
  "description": "제한속도 초과 감지",
  "speed_at_trigger": 92.3,
  "battery_at_trigger": 65.0,
  "location_lat": 37.5015,
  "location_lng": 127.0401
}
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `vehicle_id` | `UUID` | ✅ | 알림 대상 차량 ID |
| `alert_type` | `string` | ✅ | `OVERSPEED`, `BATTERY_LOW`, `BATTERY_CRITICAL`, `GEOFENCE_EXIT`, `SUDDEN_ACCEL`, `SUDDEN_BRAKE`, `ACCIDENT_SUSPECTED`, `MAINTENANCE_DUE`, `COMMUNICATION_LOST` |
| `severity` | `string` | ✅ | `DANGER`, `WARNING`, `INFO` |
| `title` | `string` | ✅ | 알림 제목 |
| `description` | `string` | — | 상세 설명 |
| `speed_at_trigger` | `float` | — | 발생 시 속도 (km/h) |
| `battery_at_trigger` | `float` | — | 발생 시 배터리 잔량 (%) |
| `location_lat` | `float` | — | 발생 위치 위도 |
| `location_lng` | `float` | — | 발생 위치 경도 |

**Response `201 Created`**: 생성된 알림 상세 (목록 아이템과 동일 구조)

**Error Cases**

| HTTP | `error.code` | 상황 |
|---|---|---|
| 404 | `NOT_FOUND` | 차량 없음 |
| 400 | `VALIDATION_ERROR` | 필수 필드 누락 또는 enum 값 오류 |

---

### `GET /alerts/{alert_id}` ⚠️ 미구현

> 알림 단건 상세 조회.

**Response `200 OK`**: 목록 아이템과 동일 구조

---

### `PATCH /alerts/{alert_id}/acknowledge` ✅

> 알림 확인 처리. 처리한 관제사 정보와 시각이 기록됩니다.  
> **권한**: `ADMIN`, `MANAGER`

**Request Body**: 없음 (현재 로그인 사용자가 확인자로 자동 기록)

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "id": "f1a2b3c4-...",
    "is_acknowledged": true,
    "acknowledged_by": {
      "id": "550e8400-...",
      "full_name": "홍길동"
    },
    "acknowledged_at": "2026-04-13T09:45:00Z"
  },
  "meta": null
}
```

---

### `POST /alerts/acknowledge-bulk`

> 다수 알림 일괄 확인 처리.  
> **권한**: `ADMIN`, `MANAGER`

**Request Body**
```json
{
  "alert_ids": [
    "f1a2b3c4-...",
    "g2b3c4d5-..."
  ]
}
```

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "acknowledged_count": 2,
    "failed_ids": []
  },
  "meta": null
}
```

---

## 6. REST API — 운행 기록(Trip)

**Base Path**: `/trips` 및 `/vehicles/{vehicle_id}/trips`  
**인증 필요**: `Bearer`  
**페이지네이션**: Offset-based

---

### `GET /trips` ✅

> 전체 운행 기록 목록.  
> **권한**: `MANAGER`, `ADMIN`

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `page` | `integer` | `1` | 페이지 번호 |
| `page_size` | `integer` | `20` | 페이지당 건수 |
| `vehicle_id` | `UUID` | — | 특정 차량 필터 |
| `driver_id` | `UUID` | — | 특정 기사 필터 |
| `from` | `ISO8601` | — | 운행 시작일 이후 |
| `to` | `ISO8601` | — | 운행 시작일 이전 |
| `status` | `string` | — | `active`(진행 중) / `completed` |

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "t1r2i3p4-...",
      "vehicle": {
        "id": "a1b2c3d4-...",
        "plate_number": "서울12가3456"
      },
      "driver": {
        "id": "d1e2f3...",
        "user_full_name": "김철수"
      },
      "started_at": "2026-04-13T08:00:00Z",
      "ended_at": "2026-04-13T09:30:00Z",
      "start_address": "서울시 강남구 테헤란로 123",
      "end_address": "서울시 송파구 잠실동 456",
      "distance_km": 18.4,
      "avg_speed_kmh": 36.2,
      "max_speed_kmh": 72.1,
      "battery_start_pct": 85.0,
      "battery_end_pct": 52.3,
      "alert_count": 1
    }
  ],
  "meta": {
    "total": 342,
    "page": 1,
    "page_size": 20,
    "total_pages": 18
  }
}
```

---

### `GET /vehicles/{vehicle_id}/trips`

> 특정 차량의 운행 기록 목록.

**Query Parameters**: `GET /trips`와 동일 (`vehicle_id` 제외)

**Response**: `GET /trips`와 동일 구조

---

### `GET /trips/{trip_id}`

> 운행 기록 단건 상세 조회. 해당 운행 구간 중 발생한 알림 목록 포함.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "id": "t1r2i3p4-...",
    "vehicle": { "id": "...", "plate_number": "서울12가3456" },
    "driver": { "id": "...", "user_full_name": "김철수" },
    "started_at": "2026-04-13T08:00:00Z",
    "ended_at": "2026-04-13T09:30:00Z",
    "start_address": "서울시 강남구 테헤란로 123",
    "end_address": "서울시 송파구 잠실동 456",
    "distance_km": 18.4,
    "avg_speed_kmh": 36.2,
    "max_speed_kmh": 72.1,
    "battery_start_pct": 85.0,
    "battery_end_pct": 52.3,
    "alert_count": 1,
    "alerts": [
      {
        "id": "f1a2b3c4-...",
        "triggered_at": "2026-04-13T08:45:00Z",
        "alert_type": "OVERSPEED",
        "severity": "WARNING",
        "title": "과속 감지 — 72km/h",
        "speed_at_trigger": 72.1
      }
    ]
  },
  "meta": null
}
```

---

## 7. REST API — 충전소

**Base Path**: `/charging-stations`  
**인증 필요**: `Bearer`

---

### `GET /charging-stations`

> 충전소 목록 조회. 현재 위치 기준 반경 내 충전소를 가까운 순으로 반환합니다.

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `lat` | `float` | — | 현재 위치 위도 (위치 기반 정렬 시 필수) |
| `lng` | `float` | — | 현재 위치 경도 |
| `radius_km` | `float` | `5.0` | 검색 반경 (km) |
| `only_available` | `boolean` | `false` | `true` = 빈 슬롯 있는 충전소만 |
| `page` | `integer` | `1` | 페이지 번호 |
| `page_size` | `integer` | `20` | 페이지당 건수 |

**거리 계산 쿼리 (Haversine 공식)**

```python
# chalicelib/repositories/charging_station_repository.py
from sqlalchemy import func, text

def find_nearby(self, lat: float, lng: float, radius_km: float) -> list:
    # PostgreSQL의 Haversine 공식 (PostGIS 없이 사용 가능)
    distance_expr = text("""
        6371 * acos(
            cos(radians(:lat)) * cos(radians(latitude))
            * cos(radians(longitude) - radians(:lng))
            + sin(radians(:lat)) * sin(radians(latitude))
        )
    """).bindparams(lat=lat, lng=lng)

    return (
        self.session.exec(
            select(ChargingStation, distance_expr.label("distance_km"))
            .where(ChargingStation.is_active == True)
            .having(text("distance_km <= :r").bindparams(r=radius_km))
            .order_by("distance_km")
        ).all()
    )
```

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "cs001...",
      "name": "강남 FMS 충전소 1호점",
      "address": "서울시 강남구 테헤란로 500",
      "latitude": 37.5030,
      "longitude": 127.0480,
      "distance_km": 0.87,
      "total_slots": 10,
      "available_slots": 3,
      "operator_name": "FMS 충전 네트워크",
      "contact_phone": "02-1234-5678",
      "is_active": true
    }
  ],
  "meta": {
    "total": 4,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

---

### `GET /charging-stations/{station_id}`

> 충전소 단건 상세 조회.

**Response**: 목록 아이템과 동일 구조 (`distance_km` 제외 가능)

---

### `PATCH /charging-stations/{station_id}/slots`

> 충전소 슬롯 가용 수 업데이트.  
> **권한**: `ADMIN`, `MANAGER`

**Request Body**
```json
{
  "available_slots": 5
}
```

**Response `200 OK`**: 수정된 충전소 상세 응답

---

## 8. REST API — 사용자 및 운전자

**Base Path**: `/users`  
**인증 필요**: `Bearer`  
**권한**: 대부분 `ADMIN` 전용

---

### `GET /users`

> 사용자 목록 조회.  
> **권한**: `ADMIN`

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `page` | `integer` | `1` | 페이지 번호 |
| `page_size` | `integer` | `20` | 페이지당 건수 |
| `role` | `string[]` | — | 역할 필터 (`ADMIN`, `MANAGER`, `DRIVER`) |
| `is_active` | `boolean` | — | 활성 여부 필터 |
| `q` | `string` | — | 이름 또는 이메일 검색 |

**Response `200 OK`**
```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-...",
      "email": "driver01@fms.io",
      "full_name": "김철수",
      "role": "DRIVER",
      "is_active": true,
      "driver_profile": {
        "id": "d1e2f3...",
        "license_number": "12-34-567890-01",
        "license_expiry": "2028-06-30",
        "phone": "010-1234-5678"
      },
      "created_at": "2025-03-01T00:00:00Z"
    }
  ],
  "meta": {
    "total": 52,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

---

### `POST /users`

> 신규 사용자 등록.  
> **권한**: `ADMIN`

**Request Body**
```json
{
  "email": "newdriver@fms.io",
  "password": "TempP@ss123!",
  "full_name": "이영희",
  "role": "DRIVER"
}
```

**Response `201 Created`**: 생성된 사용자 단건 응답

**Error Cases**

| HTTP | `error.code` | 상황 |
|---|---|---|
| 409 | `DUPLICATE_EMAIL` | 이메일 중복 |

---

### `PUT /users/{user_id}`

> 사용자 정보 수정.  
> **권한**: `ADMIN` (전체 수정) / 본인 (이름·비밀번호만 수정 가능)

**Request Body** (부분 업데이트)
```json
{
  "full_name": "이영희",
  "is_active": false
}
```

---

### `DELETE /users/{user_id}`

> 사용자 Soft Delete.  
> **권한**: `ADMIN`

**Response `204 No Content`**

---

### `GET /users/{user_id}/driver-profile`

> 특정 사용자(DRIVER)의 운전자 프로필 조회.

**Response `200 OK`**
```json
{
  "success": true,
  "data": {
    "id": "d1e2f3...",
    "user_id": "550e8400-...",
    "license_number": "12-34-567890-01",
    "license_expiry": "2028-06-30",
    "phone": "010-1234-5678",
    "emergency_contact": "010-9876-5432"
  },
  "meta": null
}
```

---

### `POST /users/{user_id}/driver-profile`

> 운전자 프로필 등록 또는 수정 (Upsert).  
> **권한**: `ADMIN`

**Request Body**
```json
{
  "license_number": "12-34-567890-01",
  "license_expiry": "2028-06-30",
  "phone": "010-1234-5678",
  "emergency_contact": "010-9876-5432"
}
```

**Response `201 Created`** (신규) / **`200 OK`** (수정)

---

## 9. MQTT — 단말기 → 서버

**브로커**: EMQX  
**프로토콜**: MQTT v3.1.1  
**QoS**: Level 1 (At Least Once) — 네트워크 불안정 환경에서 데이터 유실 방지

---

### Topic 구조

```
fms/
├── vehicle/
│   ├── {vehicle_id}/
│   │   ├── telemetry     ← 주기적 센서 데이터 (1초 간격)
│   │   ├── event         ← 이벤트 발생 시 즉시 전송 (충돌, 급가속 등)
│   │   └── status        ← 차량 상태 변경 (온라인/오프라인/충전시작 등)
│   └── +/telemetry       ← 와일드카드 (모든 차량 구독 시)
└── server/
    └── command/{vehicle_id}  ← 서버 → 단말기 (명령 전송)
```

---

### Topic: `fms/vehicle/{vehicle_id}/telemetry`

> 1초 간격 주기적 센서 데이터 전송.

**Payload (JSON)**
```json
{
  "ts": "2026-04-13T09:43:21.123Z",
  "vid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "gps": {
    "lat": 37.5012,
    "lng": 127.0396,
    "alt": 45.2,
    "hdg": 135.0,
    "fix": true
  },
  "obd": {
    "spd": 42.5,
    "rpm": 3200,
    "odo": 12453.7,
    "thr": 45.2,
    "brk": false
  },
  "bms": {
    "lvl": 68.2,
    "vol": 72.4,
    "cur": -1.2,
    "tmp": 28.1
  },
  "net": {
    "sig": -78,
    "typ": "LTE"
  }
}
```

**필드 명세**

| 경로 | 타입 | 단위 | 설명 |
|---|---|---|---|
| `ts` | `string` | ISO8601 | 측정 시각 (UTC, 밀리초 포함) |
| `vid` | `string` | UUID | 차량 ID |
| `gps.lat` | `float` | ° | 위도 (WGS84) |
| `gps.lng` | `float` | ° | 경도 |
| `gps.alt` | `float` | m | 해발 고도 |
| `gps.hdg` | `float` | ° | 진행 방향 (0=북, 90=동) |
| `gps.fix` | `boolean` | — | GPS 신호 확보 여부 |
| `obd.spd` | `float` | km/h | 현재 속도 |
| `obd.rpm` | `integer` | RPM | 엔진 회전수 |
| `obd.odo` | `float` | km | 누적 주행 거리 |
| `obd.thr` | `float` | % | 스로틀 개도율 |
| `obd.brk` | `boolean` | — | 브레이크 작동 여부 |
| `bms.lvl` | `float` | % | 배터리 잔량 |
| `bms.vol` | `float` | V | 배터리 전압 |
| `bms.cur` | `float` | A | 전류 (음수=충전, 양수=방전) |
| `bms.tmp` | `float` | °C | 배터리 셀 온도 |
| `net.sig` | `integer` | dBm | 신호 강도 |
| `net.typ` | `string` | — | 통신 방식 (`LTE`, `5G`) |

---

### Topic: `fms/vehicle/{vehicle_id}/event`

> 임계값 초과 또는 이상 감지 즉시 전송. QoS 1 보장.

**Payload (JSON)**
```json
{
  "ts": "2026-04-13T09:40:00.000Z",
  "vid": "a1b2c3d4-...",
  "type": "SUDDEN_BRAKE",
  "data": {
    "spd_before": 72.1,
    "spd_after": 15.3,
    "decel_g": 0.72,
    "lat": 37.5015,
    "lng": 127.0401
  }
}
```

**이벤트 타입 목록**

| `type` | 설명 | `data` 핵심 필드 |
|---|---|---|
| `SUDDEN_ACCEL` | 급가속 | `accel_g`, `spd_after` |
| `SUDDEN_BRAKE` | 급감속/급정거 | `decel_g`, `spd_before` |
| `IMPACT_DETECTED` | 충격 감지 (사고 의심) | `impact_g`, `lat`, `lng` |
| `OVERSPEED` | 과속 | `spd`, `limit` |
| `BATTERY_CRITICAL` | 배터리 위험 | `lvl` |
| `GPS_LOST` | GPS 신호 소실 | `last_known_lat`, `last_known_lng` |
| `ENGINE_FAULT` | 엔진 고장 코드 | `fault_code` |

---

### Topic: `fms/vehicle/{vehicle_id}/status`

> 차량 온라인/오프라인 상태 변경 알림 (LWT, Last Will and Testament 포함).

**Payload (JSON)**
```json
{
  "ts": "2026-04-13T09:00:00.000Z",
  "vid": "a1b2c3d4-...",
  "status": "ONLINE",
  "firmware_version": "1.4.2"
}
```

| `status` 값 | 트리거 조건 |
|---|---|
| `ONLINE` | 단말기 부팅 및 MQTT 연결 완료 |
| `OFFLINE` | MQTT LWT 메시지 (비정상 연결 끊김) |
| `CHARGING_START` | BMS 충전 전류 감지 시작 |
| `CHARGING_END` | 충전 전류 종료 |
| `SHUTDOWN` | 정상 전원 차단 |

---

### Topic: `fms/server/command/{vehicle_id}`

> 서버 → 단말기 원격 명령. QoS 1.

**Payload (JSON)**
```json
{
  "cmd_id": "cmd_20260413_001",
  "ts": "2026-04-13T10:00:00Z",
  "action": "SET_REPORT_INTERVAL",
  "params": {
    "interval_sec": 5
  }
}
```

| `action` | 설명 | `params` |
|---|---|---|
| `SET_REPORT_INTERVAL` | 전송 주기 변경 | `interval_sec` |
| `REBOOT` | 단말기 재부팅 | — |
| `GET_DIAGNOSTICS` | 진단 정보 즉시 전송 요청 | — |
| `UPDATE_FIRMWARE` | OTA 펌웨어 업데이트 | `url`, `version`, `checksum` |

---

## 10. WebSocket — 서버 → 클라이언트

**라이브러리**: Socket.IO  
**인증**: 연결 시 `auth: { token: "<access_token>" }` 핸드셰이크  
**네임스페이스**: `/realtime`

---

### 연결 및 구독

```typescript
// 클라이언트 (Vue3 Pinia Store)
import { io } from "socket.io-client"

const socket = io("/realtime", {
  auth: { token: accessToken },
  transports: ["websocket"],
})

// 관심 차량 구독
socket.emit("SUBSCRIBE", {
  vehicle_ids: ["a1b2c3d4-...", "b2c3d4e5-..."]
})

// 구독 해제
socket.emit("UNSUBSCRIBE", {
  vehicle_ids: ["a1b2c3d4-..."]
})
```

---

### Event: `VEHICLE_LOCATION_UPDATE`

> MQTT telemetry 수신 후 집계·필터링하여 약 2초 간격으로 Push.  
> (1초 MQTT 데이터를 그대로 전달하면 프론트엔드 렌더링 부하 발생)

**Payload**
```json
{
  "event": "VEHICLE_LOCATION_UPDATE",
  "data": {
    "vehicle_id": "a1b2c3d4-...",
    "timestamp": "2026-04-13T09:43:21Z",
    "latitude": 37.5012,
    "longitude": 127.0396,
    "heading_deg": 135.0,
    "speed_kmh": 42.5,
    "battery_level_pct": 68.2,
    "status": "RUNNING"
  }
}
```

---

### Event: `ALERT_TRIGGERED`

> AI 분석 엔진 또는 룰 엔진이 경고를 생성했을 때 즉시 Push.  
> 알림이 발생한 차량을 구독 중인 클라이언트 및 ADMIN/MANAGER 역할 전체에 전송.

**Payload**
```json
{
  "event": "ALERT_TRIGGERED",
  "data": {
    "alert_id": "f1a2b3c4-...",
    "vehicle_id": "a1b2c3d4-...",
    "plate_number": "서울12가3456",
    "triggered_at": "2026-04-13T09:40:00Z",
    "alert_type": "OVERSPEED",
    "severity": "DANGER",
    "title": "과속 감지 — 92km/h (제한 60km/h)",
    "location_lat": 37.5015,
    "location_lng": 127.0401,
    "speed_at_trigger": 92.3
  }
}
```

---

### Event: `VEHICLE_STATUS_CHANGED`

> 차량 상태가 변경될 때 Push (OFFLINE → RUNNING 등).

**Payload**
```json
{
  "event": "VEHICLE_STATUS_CHANGED",
  "data": {
    "vehicle_id": "a1b2c3d4-...",
    "plate_number": "서울12가3456",
    "previous_status": "OFFLINE",
    "current_status": "RUNNING",
    "changed_at": "2026-04-13T09:00:00Z"
  }
}
```

---

### Event: `BATTERY_REPLACE_REQUIRED`

> AI 엔진이 배터리 잔량과 소모 추세를 분석하여 교체 권고 판단 시 Push.  
> 기사 앱(DRIVER 역할)과 관제 대시보드(ADMIN/MANAGER) 동시 전송.

**Payload**
```json
{
  "event": "BATTERY_REPLACE_REQUIRED",
  "data": {
    "vehicle_id": "a1b2c3d4-...",
    "plate_number": "서울12가3456",
    "driver_id": "d1e2f3...",
    "current_battery_pct": 22.4,
    "estimated_depletion_min": 35,
    "recommended_action": "CHARGE_IMMEDIATELY",
    "nearest_stations": [
      {
        "id": "cs001...",
        "name": "강남 FMS 충전소 1호점",
        "distance_km": 0.87,
        "available_slots": 3
      }
    ],
    "triggered_at": "2026-04-13T09:43:00Z"
  }
}
```

---

### Event: `TRIP_STARTED` / `TRIP_ENDED`

> 운행 구간 자동 감지 시 Push.

**`TRIP_STARTED` Payload**
```json
{
  "event": "TRIP_STARTED",
  "data": {
    "trip_id": "t1r2i3p4-...",
    "vehicle_id": "a1b2c3d4-...",
    "plate_number": "서울12가3456",
    "driver_full_name": "김철수",
    "started_at": "2026-04-13T08:00:00Z",
    "start_location": { "lat": 37.4979, "lng": 127.0276 }
  }
}
```

**`TRIP_ENDED` Payload**
```json
{
  "event": "TRIP_ENDED",
  "data": {
    "trip_id": "t1r2i3p4-...",
    "vehicle_id": "a1b2c3d4-...",
    "ended_at": "2026-04-13T09:30:00Z",
    "distance_km": 18.4,
    "duration_min": 90,
    "battery_consumed_pct": 32.7,
    "alert_count": 1
  }
}
```

---

### 에러 이벤트

```json
{
  "event": "error",
  "data": {
    "code": "TOKEN_EXPIRED",
    "message": "인증 토큰이 만료되었습니다. 재연결이 필요합니다."
  }
}
```

---

## 11. 권한 매트릭스

| 엔드포인트 | ADMIN | MANAGER | DRIVER |
|---|:---:|:---:|:---:|
| `GET /vehicles` | ✅ | ✅ | ✅ (본인 차량만) |
| `POST /vehicles` | ✅ | ✅ | ❌ |
| `PUT /vehicles/{id}` | ✅ | ✅ | ❌ |
| `DELETE /vehicles/{id}` | ✅ | ❌ | ❌ |
| `GET /vehicles/{id}/sensors` | ✅ | ✅ | ✅ (본인 차량만) |
| `GET /alerts` | ✅ | ✅ | ✅ (본인 차량만) |
| `PATCH /alerts/{id}/acknowledge` | ✅ | ✅ | ❌ |
| `POST /alerts/acknowledge-bulk` | ✅ | ✅ | ❌ |
| `GET /trips` | ✅ | ✅ | ✅ (본인 운행만) |
| `GET /charging-stations` | ✅ | ✅ | ✅ |
| `PATCH /charging-stations/{id}/slots` | ✅ | ✅ | ❌ |
| `GET /users` | ✅ | ❌ | ❌ |
| `POST /users` | ✅ | ❌ | ❌ |
| `PUT /users/{id}` | ✅ | ❌ | ✅ (본인만) |
| `DELETE /users/{id}` | ✅ | ❌ | ❌ |
| `GET /auth/me` | ✅ | ✅ | ✅ |
| WebSocket 구독 | ✅ (전체) | ✅ (전체) | ✅ (본인 차량만) |

---

> **개정 이력**  
> - v1.0 (2026-04-13): 초안 작성 — REST 8개 도메인, MQTT 4개 토픽, WebSocket 6개 이벤트, 에러 코드 전체 정의
