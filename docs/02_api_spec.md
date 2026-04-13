# API 및 인터페이스 명세서 (API Specification)

**프로젝트**: 지능형 오토바이 FMS (Fleet Management System)  
**버전**: v1.0  
**작성일**: 2026-04-13  
**Base URL**: `https://api.bikefms.io/v1`

---

## 1. 공통 규격

### 1.1 인증

모든 REST API 요청은 `Authorization` 헤더에 JWT Bearer 토큰을 포함해야 합니다.

```
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

### 1.2 공통 응답 포맷

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "timestamp": "2026-04-13T09:00:00Z",
    "requestId": "req_abc123"
  }
}
```

**에러 응답**:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VEHICLE_NOT_FOUND",
    "message": "요청한 차량을 찾을 수 없습니다.",
    "status": 404
  }
}
```

### 1.3 공통 HTTP 상태 코드

| 코드 | 의미 |
|---|---|
| `200 OK` | 성공 |
| `201 Created` | 리소스 생성 성공 |
| `400 Bad Request` | 잘못된 요청 파라미터 |
| `401 Unauthorized` | 인증 실패 |
| `403 Forbidden` | 권한 없음 |
| `404 Not Found` | 리소스 없음 |
| `429 Too Many Requests` | Rate Limit 초과 |
| `500 Internal Server Error` | 서버 오류 |

---

## 2. REST API 명세

### 2.1 인증 (Authentication)

#### `POST /auth/login` — 로그인

**Request**:
```json
{
  "username": "admin01",
  "password": "P@ssw0rd!"
}
```

**Response** `200`:
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR...",
    "expiresIn": 3600,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "admin01",
      "role": "ADMIN"
    }
  }
}
```

---

### 2.2 차량 (Vehicles)

#### `GET /vehicles` — 차량 목록 조회

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `status` | `string` | N | ACTIVE / INACTIVE / MAINTENANCE |
| `driverId` | `UUID` | N | 특정 운전자 배정 차량 필터 |
| `page` | `integer` | N | 페이지 번호 (default: 1) |
| `limit` | `integer` | N | 페이지 크기 (default: 20, max: 100) |

**Request Example**:
```
GET /vehicles?status=ACTIVE&page=1&limit=20
```

**Response** `200`:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "plateNumber": "12가 3456",
        "modelName": "Honda PCX 125e",
        "imei": "358000000000001",
        "status": "ACTIVE",
        "odometerKm": 12450,
        "assignedDriver": {
          "id": "550e8400-e29b-41d4-a716-446655440010",
          "username": "driver01",
          "phone": "010-1234-5678"
        },
        "lastState": {
          "latitude": 37.5665,
          "longitude": 126.9780,
          "speedKmh": 45.2,
          "socPct": 78.5,
          "engineTempC": 85.3,
          "updatedAt": "2026-04-13T09:00:00Z"
        }
      }
    ],
    "pagination": {
      "total": 150,
      "page": 1,
      "limit": 20,
      "totalPages": 8
    }
  }
}
```

---

#### `GET /vehicles/{vehicleId}` — 차량 단건 조회

**Path Parameters**:
- `vehicleId` (UUID, 필수)

**Response** `200`:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "plateNumber": "12가 3456",
    "modelName": "Honda PCX 125e",
    "vin": "JH2PC44CXMM000001",
    "imei": "358000000000001",
    "status": "ACTIVE",
    "odometerKm": 12450,
    "registeredAt": "2025-01-15T10:00:00Z",
    "assignedDriver": { ... },
    "currentTrip": {
      "id": "trip-uuid",
      "startedAt": "2026-04-13T08:00:00Z",
      "distanceKm": 25.3
    }
  }
}
```

---

### 2.3 운행 이력 (Trips)

#### `GET /vehicles/{vehicleId}/trips` — 과거 운행 이력 조회

**Path Parameters**:
- `vehicleId` (UUID, 필수)

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `startDate` | `ISO8601` | Y | 조회 시작 일시 |
| `endDate` | `ISO8601` | Y | 조회 종료 일시 |
| `status` | `string` | N | COMPLETED / IN_PROGRESS / INTERRUPTED |
| `page` | `integer` | N | default: 1 |
| `limit` | `integer` | N | default: 20 |

**Request Example**:
```
GET /vehicles/550e.../trips?startDate=2026-04-01T00:00:00Z&endDate=2026-04-13T23:59:59Z&status=COMPLETED
```

**Response** `200`:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "trip-uuid-001",
        "startedAt": "2026-04-13T08:00:00Z",
        "endedAt": "2026-04-13T09:30:00Z",
        "durationMinutes": 90,
        "distanceKm": 45.2,
        "avgSpeedKmh": 30.1,
        "maxSpeedKmh": 68.5,
        "energyConsumedWh": 850.3,
        "alertCount": 2,
        "startLocation": {
          "latitude": 37.5665,
          "longitude": 126.9780,
          "address": "서울 중구 명동"
        },
        "endLocation": {
          "latitude": 37.4979,
          "longitude": 127.0276,
          "address": "서울 강남구 역삼동"
        },
        "status": "COMPLETED"
      }
    ],
    "summary": {
      "totalTrips": 12,
      "totalDistanceKm": 420.5,
      "totalDurationMinutes": 780,
      "avgScoreRating": 85.2
    },
    "pagination": { "total": 12, "page": 1, "limit": 20 }
  }
}
```

---

#### `GET /vehicles/{vehicleId}/trips/{tripId}/telemetry` — 운행 경로 상세 조회

**Response** `200`:
```json
{
  "success": true,
  "data": {
    "tripId": "trip-uuid-001",
    "gpsTrack": [
      {
        "time": "2026-04-13T08:00:00Z",
        "lat": 37.5665,
        "lng": 126.9780,
        "speedKmh": 0
      },
      {
        "time": "2026-04-13T08:00:05Z",
        "lat": 37.5666,
        "lng": 126.9782,
        "speedKmh": 12.3
      }
    ],
    "alertMarkers": [
      {
        "time": "2026-04-13T08:45:00Z",
        "lat": 37.5200,
        "lng": 127.0100,
        "type": "OVERSPEED",
        "speedKmh": 78.5
      }
    ]
  }
}
```

---

### 2.4 충전소 (Charging Stations)

#### `GET /charging-stations` — 충전소 목록 조회

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `lat` | `float` | N | 기준 위도 (근거리 검색 시) |
| `lng` | `float` | N | 기준 경도 (근거리 검색 시) |
| `radius` | `integer` | N | 검색 반경 (미터, default: 5000) |
| `status` | `string` | N | OPEN / FULL / CLOSED |
| `limit` | `integer` | N | default: 10, max: 50 |

**Request Example**:
```
GET /charging-stations?lat=37.5665&lng=126.9780&radius=3000&status=OPEN
```

**Response** `200`:
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
        "distanceM": 450,
        "totalSlots": 10,
        "availableSlots": 4,
        "status": "OPEN",
        "updatedAt": "2026-04-13T09:00:00Z"
      }
    ],
    "total": 5
  }
}
```

---

### 2.5 알림 (Alerts)

#### `GET /alerts` — 알림 목록 조회

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `vehicleId` | `UUID` | N | 특정 차량 필터 |
| `type` | `string` | N | 알림 유형 필터 |
| `severity` | `string` | N | INFO / WARNING / CRITICAL |
| `isResolved` | `boolean` | N | 처리 여부 |
| `startDate` | `ISO8601` | N | |
| `endDate` | `ISO8601` | N | |

**Response** `200`:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "alert-uuid-001",
        "vehicleId": "vehicle-uuid",
        "plateNumber": "12가 3456",
        "type": "OVERSPEED",
        "severity": "WARNING",
        "payload": {
          "speedKmh": 78.5,
          "speedLimitKmh": 60,
          "latitude": 37.5200,
          "longitude": 127.0100
        },
        "isResolved": false,
        "createdAt": "2026-04-13T08:45:00Z"
      }
    ],
    "pagination": { "total": 45, "page": 1, "limit": 20 }
  }
}
```

---

## 3. MQTT 통신 명세 (Device → Server)

### 3.1 MQTT 브로커 설정

| 항목 | 값 |
|---|---|
| **Broker Host** | `mqtt.bikefms.io` |
| **Port** | `8883` (TLS) |
| **Protocol** | MQTT v5.0 |
| **QoS** | 1 (At Least Once) |
| **인증** | TLS 클라이언트 인증서 + Username/Password |
| **Client ID 규칙** | `ION-{IMEI}` |

### 3.2 Topic 구조

```
bikefms/{version}/{imei}/{data_type}
```

| 필드 | 설명 |
|---|---|
| `{version}` | API 버전 (고정값: `v1`) |
| `{imei}` | 단말기 고유 IMEI (15자리) |
| `{data_type}` | `gps` / `obd` / `bms` / `event` |

**예시**:
```
bikefms/v1/358000000000001/gps
bikefms/v1/358000000000001/obd
bikefms/v1/358000000000001/bms
bikefms/v1/358000000000001/event
```

---

### 3.3 GPS Payload

**Topic**: `bikefms/v1/{imei}/gps`  
**전송 주기**: 5초

```json
{
  "imei": "358000000000001",
  "ts": 1744534800000,
  "lat": 37.5665,
  "lng": 126.9780,
  "alt": 35.2,
  "spd": 45.3,
  "hdg": 180.5,
  "acc": 3
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `imei` | string | 단말기 식별자 |
| `ts` | int64 | Unix timestamp (ms) |
| `lat` | float | 위도 |
| `lng` | float | 경도 |
| `alt` | float | 고도 (m) |
| `spd` | float | 속도 (km/h) |
| `hdg` | float | 진행 방향 (0~360°) |
| `acc` | int | GPS 정확도 반경 (m) |

---

### 3.4 OBD Payload

**Topic**: `bikefms/v1/{imei}/obd`  
**전송 주기**: 5초

```json
{
  "imei": "358000000000001",
  "ts": 1744534800000,
  "rpm": 3500,
  "etmp": 88.5,
  "fuel": 65.2,
  "thr": 45.0,
  "brk": 12.5,
  "ax": 0.12,
  "ay": -0.05,
  "az": 0.98
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `rpm` | float | 엔진 RPM |
| `etmp` | float | 엔진 온도 (°C) |
| `fuel` | float | 연료 잔량 (%) |
| `thr` | float | 스로틀 개도 (%) |
| `brk` | float | 브레이크 압력 (bar) |
| `ax/ay/az` | float | 3축 가속도 (g) |

---

### 3.5 BMS Payload

**Topic**: `bikefms/v1/{imei}/bms`  
**전송 주기**: 10초

```json
{
  "imei": "358000000000001",
  "ts": 1744534800000,
  "vol": 48.6,
  "cur": -12.3,
  "soc": 72.5,
  "soh": 91.2,
  "tmp": 32.1,
  "rng": 38.5,
  "cyc": 142
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `vol` | float | 배터리 전압 (V) |
| `cur` | float | 전류 (A, 방전 시 음수) |
| `soc` | float | 충전 상태 (%) |
| `soh` | float | 배터리 건강도 (%) |
| `tmp` | float | 배터리 온도 (°C) |
| `rng` | float | AI 추정 잔여 주행 가능 거리 (km) |
| `cyc` | int | 충방전 사이클 수 |

---

### 3.6 Event Payload (단말기 이벤트)

**Topic**: `bikefms/v1/{imei}/event`  
**전송 조건**: 이벤트 발생 시 즉시

```json
{
  "imei": "358000000000001",
  "ts": 1744534800000,
  "type": "HARD_BRAKE",
  "severity": "WARNING",
  "data": {
    "ax": -0.85,
    "spd_before": 65.0,
    "spd_after": 20.0,
    "lat": 37.5665,
    "lng": 126.9780
  }
}
```

**이벤트 타입 목록**:

| type | 설명 | severity |
|---|---|---|
| `HARD_BRAKE` | 급제동 감지 | WARNING |
| `HARD_ACCEL` | 급가속 감지 | WARNING |
| `IMPACT` | 충격/사고 감지 | CRITICAL |
| `ENGINE_ON` | 시동 ON | INFO |
| `ENGINE_OFF` | 시동 OFF | INFO |
| `LOW_BATTERY` | 배터리 부족 (SOC ≤ 20%) | WARNING |
| `GEOFENCE_EXIT` | 지오펜스 이탈 | WARNING |

---

## 4. WebSocket 통신 명세 (Server → Client)

### 4.1 연결 정보

| 항목 | 값 |
|---|---|
| **Endpoint** | `wss://ws.bikefms.io/v1/realtime` |
| **Protocol** | WebSocket over TLS |
| **인증** | 연결 시 `?token={JWT_ACCESS_TOKEN}` 쿼리 파라미터 |
| **Heartbeat** | 30초마다 ping/pong |

### 4.2 구독 요청 (Client → Server)

연결 직후 클라이언트는 관심 차량 목록을 구독 등록합니다.

```json
{
  "action": "SUBSCRIBE",
  "payload": {
    "vehicleIds": [
      "550e8400-e29b-41d4-a716-446655440001",
      "550e8400-e29b-41d4-a716-446655440002"
    ]
  }
}
```

### 4.3 이벤트 스키마 (Server → Client Push)

모든 서버 푸시 메시지는 다음 공통 래퍼를 사용합니다.

```json
{
  "event": "<EVENT_TYPE>",
  "vehicleId": "<UUID>",
  "ts": "<ISO8601>",
  "payload": { ... }
}
```

---

#### 4.3.1 실시간 위치 업데이트

**Event**: `VEHICLE_LOCATION_UPDATE`  
**전송 주기**: 5초

```json
{
  "event": "VEHICLE_LOCATION_UPDATE",
  "vehicleId": "550e8400-e29b-41d4-a716-446655440001",
  "ts": "2026-04-13T09:00:05Z",
  "payload": {
    "lat": 37.5666,
    "lng": 126.9782,
    "speedKmh": 45.3,
    "headingDeg": 180.5,
    "socPct": 72.5,
    "engineTempC": 88.5
  }
}
```

---

#### 4.3.2 과속 알림

**Event**: `ALERT_OVERSPEED`  
**전송 조건**: AI 엔진이 과속 판정 시 즉시

```json
{
  "event": "ALERT_OVERSPEED",
  "vehicleId": "550e8400-e29b-41d4-a716-446655440001",
  "ts": "2026-04-13T09:15:32Z",
  "payload": {
    "alertId": "alert-uuid-001",
    "severity": "WARNING",
    "driverName": "홍길동",
    "plateNumber": "12가 3456",
    "currentSpeedKmh": 78.5,
    "speedLimitKmh": 60.0,
    "excessSpeedKmh": 18.5,
    "location": {
      "lat": 37.5200,
      "lng": 127.0100,
      "roadName": "강남대로"
    }
  }
}
```

---

#### 4.3.3 배터리 교체 권고

**Event**: `ALERT_BATTERY_REPLACE`  
**전송 조건**: SOH ≤ 70% 또는 잔여 주행거리 ≤ 10km 시

```json
{
  "event": "ALERT_BATTERY_REPLACE",
  "vehicleId": "550e8400-e29b-41d4-a716-446655440001",
  "ts": "2026-04-13T09:20:00Z",
  "payload": {
    "alertId": "alert-uuid-002",
    "severity": "WARNING",
    "driverName": "홍길동",
    "plateNumber": "12가 3456",
    "sohPct": 65.2,
    "socPct": 18.5,
    "remainingRangeKm": 8.3,
    "cycleCount": 520,
    "vehicleLocation": {
      "lat": 37.5665,
      "lng": 126.9780
    },
    "nearestStations": [
      {
        "id": "station-uuid-001",
        "name": "명동 충전소",
        "distanceM": 450,
        "availableSlots": 4,
        "lat": 37.5638,
        "lng": 126.9830
      }
    ]
  }
}
```

---

#### 4.3.4 급가속/급제동 알림

**Event**: `ALERT_HARD_DRIVING`

```json
{
  "event": "ALERT_HARD_DRIVING",
  "vehicleId": "550e8400-e29b-41d4-a716-446655440001",
  "ts": "2026-04-13T09:22:10Z",
  "payload": {
    "alertId": "alert-uuid-003",
    "severity": "WARNING",
    "subType": "HARD_ACCEL",
    "accelG": 0.72,
    "speedKmh": 55.0,
    "location": { "lat": 37.5300, "lng": 127.0050 }
  }
}
```

---

#### 4.3.5 배달 완료 상태 업데이트

**Event**: `VEHICLE_STATUS_UPDATE`

```json
{
  "event": "VEHICLE_STATUS_UPDATE",
  "vehicleId": "550e8400-e29b-41d4-a716-446655440001",
  "ts": "2026-04-13T09:30:00Z",
  "payload": {
    "prevStatus": "IN_PROGRESS",
    "newStatus": "DELIVERY_COMPLETED",
    "tripId": "trip-uuid-001",
    "location": { "lat": 37.4979, "lng": 127.0276 }
  }
}
```

---

## 5. 모바일 Push 알림 스키마 (FCM/APNs)

배터리 교체 권고 및 긴급 이벤트는 WebSocket 외 FCM/APNs를 통해 이중 발송합니다.

```json
{
  "to": "{FCM_DEVICE_TOKEN}",
  "notification": {
    "title": "배터리 교체 권고",
    "body": "차량 12가 3456의 배터리 잔량이 18%입니다. 근처 충전소를 확인하세요."
  },
  "data": {
    "type": "ALERT_BATTERY_REPLACE",
    "vehicleId": "550e8400-e29b-41d4-a716-446655440001",
    "alertId": "alert-uuid-002",
    "deepLink": "bikefms://charging-station/nearest?vehicleId=550e..."
  }
}
```
