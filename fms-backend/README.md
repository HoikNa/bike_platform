# FMS Backend (Chalice + SQLModel)

지능형 오토바이 FMS 백엔드 서버입니다.

## 1) 로컬 실행

```bash
cd fms-backend
python3 -m venv .venv
.venv/bin/python -m ensurepip --upgrade
.venv/bin/pip install -r requirements.txt
.venv/bin/chalice local --host 0.0.0.0 --port 8000
```

기본 DB는 로컬 SQLite 파일(`fms_local_v2.db`)을 사용합니다.  
필요 시 `DATABASE_URL` 환경변수로 변경할 수 있습니다.

## 2) OpenAPI 문서

- 스펙 파일: `docs/openapi.yaml`

## 3) API 빠른 테스트 (curl)

### 차량 목록 조회 (페이징/정렬)

```bash
curl -sS "http://localhost:8000/vehicles?limit=5&offset=0&sort=id&order=asc"
```

### 차량 생성 (초기 SensorStatus 자동 생성)

```bash
curl -sS -X POST "http://localhost:8000/vehicles" \
  -H "Content-Type: application/json" \
  -d '{"plate_number":"99가9999","status":"IDLE","driver_name":"테스터"}'
```

### 차량 단건 조회 (최신 센서 상태 포함)

```bash
curl -sS "http://localhost:8000/vehicles/1"
```

### 알림 목록 조회 (페이징/정렬)

```bash
curl -sS "http://localhost:8000/alerts?limit=5&offset=0&sort=timestamp&order=desc"
```

### 알림 생성

```bash
curl -sS -X POST "http://localhost:8000/alerts" \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":1,"type":"DANGER","message":"급가속 감지"}'
```

## 4) 공통 응답 형식

- 성공: `{"status": 200, "data": ...}`
- 실패: `{"error": "...", "status": 400}`

목록 API의 `meta`에는 `limit`, `offset`, `total`, `total_pages`, `sort`, `order`가 포함됩니다.
