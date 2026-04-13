# 시스템 시퀀스 다이어그램 (System Sequence Diagram)

**프로젝트**: 지능형 오토바이 FMS (Fleet Management System)  
**버전**: v1.0  
**작성일**: 2026-04-13  

---

## 시나리오 1: 위험 운행(과속) 감지 및 알림

### 개요

오토바이 단말기(ION)가 주기적으로 GPS/OBD 데이터를 MQTT로 전송하면, 서버의 AI 분석 엔진이 실시간으로 과속 여부를 판단하고 WebSocket을 통해 관제 대시보드에 즉시 경고를 푸시하는 시나리오입니다.

### 참여자

| 참여자 | 설명 |
|---|---|
| `ION 단말기` | 오토바이에 장착된 데이터 수집 노드 |
| `MQTT 브로커` | 단말기 수신 메시지 처리 (Mosquitto/EMQX) |
| `메시지 큐` | 비동기 처리 버퍼 (Apache Kafka) |
| `AI 분석 엔진` | 과속/급가속 판정 서비스 |
| `Redis` | 실시간 상태 캐시 |
| `TimescaleDB` | 시계열 이력 데이터 저장 |
| `Alert 서비스` | 알림 생성 및 발송 서비스 |
| `WebSocket 서버` | 대시보드/앱 실시간 푸시 |
| `관제 대시보드` | 운영자 웹 클라이언트 (Vue3) |

### 시퀀스 다이어그램

```mermaid
sequenceDiagram
    autonumber

    participant ION as ION 단말기
    participant MQTT as MQTT 브로커
    participant MQ as 메시지 큐 (Kafka)
    participant AI as AI 분석 엔진
    participant Redis as Redis 캐시
    participant TSDB as TimescaleDB
    participant AlertSvc as Alert 서비스
    participant WS as WebSocket 서버
    participant Dashboard as 관제 대시보드

    Note over ION, Dashboard: [주기 데이터 수신 Phase - 5초 간격]

    ION ->> MQTT: PUBLISH bikefms/v1/{imei}/gps<br/>{ spd: 78.5, lat: 37.52, lng: 127.01 }
    ION ->> MQTT: PUBLISH bikefms/v1/{imei}/obd<br/>{ rpm: 5200, thr: 88.0 }

    MQTT ->> MQ: 토픽 메시지 → Kafka Topic: raw-telemetry

    par 병렬 처리
        MQ ->> Redis: vehicle:{id}:state 업데이트<br/>(최신 위치/속도 스냅샷, TTL 60s)
        MQ ->> TSDB: telemetry_gps, telemetry_obd INSERT
        MQ ->> AI: 실시간 분석 스트림 전달
    end

    Note over AI: 과속 판정 로직 실행<br/>현재 속도(78.5) > 속도 제한(60) + 임계값(5) → 과속 확정

    AI ->> AI: 과속 판정 (현재 78.5km/h, 제한 60km/h)
    AI ->> AlertSvc: 과속 알림 생성 요청<br/>{ vehicleId, speed: 78.5, limit: 60, location }

    AlertSvc ->> TSDB: alerts 테이블 INSERT<br/>{ type: OVERSPEED, severity: WARNING }
    AlertSvc ->> Redis: alert:active:{vehicleId} SET 추가
    AlertSvc ->> WS: 구독 차량 대상 이벤트 발행<br/>ALERT_OVERSPEED payload

    WS ->> Dashboard: WebSocket Push<br/>{ event: "ALERT_OVERSPEED", speedKmh: 78.5, plateNumber: "12가 3456" }

    Note over Dashboard: 경고 배너 표출<br/>지도 상 해당 차량 마커 빨간색 전환<br/>알림 사운드 재생

    Dashboard -->> AlertSvc: PATCH /alerts/{alertId}/acknowledge<br/>(운영자 알림 확인 처리)
    AlertSvc -->> Dashboard: 200 OK { isResolved: false, acknowledgedAt }

    Note over ION, Dashboard: [지속 모니터링 - 과속 해소 감지]

    ION ->> MQTT: PUBLISH gps { spd: 42.0 } (속도 정상화)
    MQTT ->> MQ: raw-telemetry 전달
    MQ ->> AI: 스트림 분석 계속
    AI ->> AlertSvc: 과속 종료 통보 { vehicleId, duration: 45s }
    AlertSvc ->> WS: ALERT_RESOLVED 이벤트 발행
    WS ->> Dashboard: WebSocket Push<br/>{ event: "ALERT_RESOLVED", alertId }
    Dashboard -->> Dashboard: 경고 마커 해제, 알림 닫기
```

### 단계별 설명

| 단계 | 설명 |
|---|---|
| **1~2** | ION 단말기가 5초 주기로 GPS(위치/속도) 및 OBD(RPM/스로틀) 데이터를 TLS 암호화된 MQTT 채널로 발행합니다. |
| **3** | MQTT 브로커는 수신한 메시지를 Kafka `raw-telemetry` 토픽으로 즉시 포워딩합니다. |
| **4~6** | Kafka 컨슈머 그룹이 메시지를 병렬 처리합니다: Redis에 최신 상태 캐싱, TimescaleDB에 이력 저장, AI 엔진으로 분석 스트림 전달. |
| **7** | AI 분석 엔진은 현재 속도가 도로 제한 속도 + 임계값(기본 5km/h)을 초과하면 과속으로 판정합니다. |
| **8~10** | Alert 서비스가 DB에 알림을 기록하고, Redis에 활성 알림 마킹 후, WebSocket 서버로 이벤트를 전달합니다. |
| **11** | WebSocket 서버는 해당 차량을 구독 중인 모든 대시보드 클라이언트에게 즉시 푸시합니다. |
| **12~13** | 대시보드에서 경고 배너 및 빨간 마커가 표출되며, 운영자가 확인 처리(ACK)합니다. |
| **14~18** | 이후 속도가 정상화되면 동일 파이프라인을 통해 알림 해제 이벤트가 전파됩니다. |

---

## 시나리오 2: 배터리 교체 권고 및 충전소 안내

### 개요

ION 단말기의 BMS 데이터를 AI가 분석하여 배터리 잔량 부족 또는 수명 도래를 감지하면, 관제 대시보드와 운전자 모바일 앱에 동시에 알림을 발송하고 근처 충전소 탐색 및 네비게이션 연동까지 안내하는 시나리오입니다.

### 참여자

| 참여자 | 설명 |
|---|---|
| `ION 단말기` | BMS 데이터 수집 및 전송 |
| `MQTT 브로커` | 메시지 수신 |
| `메시지 큐` | 비동기 처리 버퍼 |
| `AI 분석 엔진` | 배터리 수명 예측 모델 |
| `Alert 서비스` | 알림 생성, FCM/APNs 발송 |
| `GIS API` | 근처 충전소 좌표 기반 탐색 |
| `WebSocket 서버` | 대시보드 실시간 푸시 |
| `관제 대시보드` | 운영자 웹 클라이언트 |
| `모바일 앱` | 운전자 앱 (React Native / Flutter) |
| `네비게이션 앱` | 외부 지도 앱 (카카오맵/T맵) |

### 시퀀스 다이어그램

```mermaid
sequenceDiagram
    autonumber

    participant ION as ION 단말기
    participant MQTT as MQTT 브로커
    participant MQ as 메시지 큐 (Kafka)
    participant AI as AI 분석 엔진
    participant TSDB as TimescaleDB
    participant AlertSvc as Alert 서비스
    participant GIS as GIS / 지도 API
    participant WS as WebSocket 서버
    participant FCM as FCM / APNs
    participant Dashboard as 관제 대시보드
    participant App as 운전자 모바일 앱
    participant NavApp as 네비게이션 앱

    Note over ION, Dashboard: [BMS 데이터 수신 Phase - 10초 간격]

    ION ->> MQTT: PUBLISH bikefms/v1/{imei}/bms<br/>{ soc: 18.5, soh: 65.2, rng: 8.3, cyc: 520, tmp: 38.1 }
    MQTT ->> MQ: Kafka Topic: raw-telemetry (bms)

    par 병렬 처리
        MQ ->> TSDB: telemetry_bms INSERT
        MQ ->> AI: BMS 스트림 분석 요청
    end

    Note over AI: 배터리 상태 복합 판정<br/>SOC(18.5%) ≤ 20% → 즉시 교체 필요<br/>SOH(65.2%) ≤ 70% → 수명 도래<br/>잔여거리(8.3km) ≤ 10km → 위험

    AI ->> AI: 배터리 교체 권고 판정<br/>(SOC + SOH + 잔여거리 복합 조건)
    AI ->> AlertSvc: 배터리 교체 알림 생성 요청<br/>{ vehicleId, soc: 18.5, soh: 65.2, rng: 8.3, lat, lng }

    AlertSvc ->> TSDB: alerts INSERT (BATTERY_REPLACE, CRITICAL)

    AlertSvc ->> GIS: 근처 충전소 탐색 요청<br/>GET /charging-stations?lat=37.5665&lng=126.9780&radius=3000&status=OPEN
    GIS -->> AlertSvc: 충전소 목록 반환<br/>[{ id, name, dist: 450m, slots: 4, lat, lng }, ...]

    AlertSvc ->> AlertSvc: 알림 페이로드 조합<br/>(배터리 정보 + 충전소 목록)

    par 동시 발송
        AlertSvc ->> WS: ALERT_BATTERY_REPLACE 이벤트 발행
        AlertSvc ->> FCM: Push 알림 발송<br/>{ title: "배터리 교체 권고", body: "잔량 18%, 근처 충전소 확인" }
    end

    WS ->> Dashboard: WebSocket Push<br/>{ event: "ALERT_BATTERY_REPLACE", nearestStations: [...] }
    FCM ->> App: Push 알림 수신

    Note over Dashboard: 배터리 위험 배너 표출<br/>지도에 충전소 핀(핀 아이콘) 오버레이<br/>차량 → 최근접 충전소 경로 표시

    Dashboard ->> Dashboard: 근접 충전소 지도 오버레이<br/>차량 → 충전소 경로 표시

    Note over App: Push 알림 탭 → 앱 실행

    App ->> App: 딥링크 실행<br/>bikefms://charging-station/nearest?vehicleId=...

    App ->> AlertSvc: GET /charging-stations?lat={현재위치}&radius=3000
    AlertSvc -->> App: 충전소 목록 + 상세 정보

    App ->> App: 충전소 목록 화면 표시<br/>(거리, 잔여 슬롯, 지도 미니뷰)

    Note over App: 운전자가 충전소 선택 → 네비게이션 연동

    App ->> NavApp: 외부 앱 실행<br/>카카오맵: kakaomap://route?ep={충전소lat},{충전소lng}<br/>T맵: tmap://route?goalx={lng}&goaly={lat}

    NavApp -->> App: 경로 안내 시작

    App ->> AlertSvc: PATCH /alerts/{alertId}/acknowledge<br/>{ acknowledgedBy: "DRIVER", driverAction: "NAVIGATING" }
    AlertSvc -->> App: 200 OK

    AlertSvc ->> WS: ALERT_DRIVER_NAVIGATING 이벤트
    WS ->> Dashboard: WebSocket Push<br/>{ event: "ALERT_DRIVER_NAVIGATING", driverName: "홍길동", stationName: "명동 충전소" }

    Note over Dashboard: 운전자 충전소 이동 중 상태로 업데이트

    Note over ION, NavApp: [충전 완료 후]

    ION ->> MQTT: PUBLISH bms { soc: 95.0, cur: 0.0 } (충전 완료)
    MQTT ->> MQ: bms 데이터 전달
    MQ ->> AI: BMS 분석 (충전 완료 감지)
    AI ->> AlertSvc: 충전 완료 통보
    AlertSvc ->> TSDB: alert 상태 → RESOLVED 업데이트
    AlertSvc ->> WS: ALERT_RESOLVED + VEHICLE_CHARGING_COMPLETE
    WS ->> Dashboard: 상태 업데이트 Push
```

### 단계별 설명

| 단계 | 설명 |
|---|---|
| **1~2** | ION 단말기가 10초 주기로 BMS 데이터(SOC, SOH, 온도, 잔여거리, 사이클수)를 전송합니다. |
| **3~4** | Kafka를 통해 TimescaleDB 저장과 AI 분석이 병렬로 수행됩니다. |
| **5** | AI 분석 엔진은 SOC ≤ 20%, SOH ≤ 70%, 잔여거리 ≤ 10km 세 가지 복합 조건을 평가하여 교체 권고를 결정합니다. |
| **6~8** | Alert 서비스가 DB에 기록 후 GIS API를 호출하여 현재 차량 위치 기준 반경 3km 내 이용 가능한 충전소 목록을 실시간으로 조회합니다. |
| **9~10** | WebSocket(대시보드용)과 FCM/APNs(운전자 앱용)로 동시에 알림을 발송합니다. |
| **11~13** | 관제 대시보드는 지도에 충전소 핀과 최적 경로를 즉시 오버레이합니다. |
| **14~16** | 운전자가 Push 알림을 탭하면 앱이 딥링크로 열리고, 서버에서 충전소 목록을 재조회하여 화면에 표시합니다. |
| **17~18** | 운전자가 충전소를 선택하면 카카오맵/T맵 외부 앱으로 경로 안내가 시작됩니다. |
| **19~20** | 앱이 Alert 서비스에 운전자 행동(이동 중)을 보고하고, 대시보드에서 이 상태가 실시간으로 반영됩니다. |
| **21~25** | 충전 완료 시 BMS 데이터가 정상화되고, 동일 파이프라인을 통해 알림이 자동 해제됩니다. |
