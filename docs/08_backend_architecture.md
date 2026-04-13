# 백엔드 아키텍처 정의서 (Backend Architecture)

**프로젝트**: 지능형 오토바이 FMS  
**버전**: v1.0 | **작성일**: 2026-04-13  
**기술 스택**: AWS Chalice 1.31, SQLModel 0.0.21, Python 3.12, PostgreSQL/TimescaleDB, Redis

---

## 1. 아키텍처 원칙

| 원칙 | 내용 |
|---|---|
| **계층 분리** | Route → Service → Repository → DB. 계층 간 의존 방향은 단방향 |
| **의존성 역전** | Service는 Repository 인터페이스(Protocol)에 의존, 구현체는 주입 |
| **단일 책임** | 각 모듈은 하나의 도메인만 담당 (vehicles, alerts, trips, ...) |
| **Stateless** | Lambda/Chalice 인스턴스는 무상태. 세션·캐시는 외부(Redis)로 분리 |
| **명시적 에러** | 비즈니스 예외는 커스텀 Exception 클래스로 정의, Handler에서 일괄 변환 |

---

## 2. 디렉터리 구조

```
bikeplatform-api/
├── app.py                          # Chalice 진입점 — 라우팅 등록만 담당
├── .chalice/
│   └── config.json                 # 환경별 Lambda 설정
├── chalicelib/                     # Chalice가 자동 패키징하는 소스 루트
│   ├── __init__.py
│   │
│   ├── config.py                   # 환경 변수 로드 (pydantic-settings)
│   ├── exceptions.py               # 커스텀 비즈니스 예외 클래스
│   │
│   ├── middlewares/                # 공통 횡단 관심사
│   │   ├── __init__.py
│   │   ├── auth.py                 # JWT 인증/인가 데코레이터
│   │   ├── error_handler.py        # 전역 예외 → HTTP 응답 변환
│   │   └── db_session.py           # SQLModel 세션 컨텍스트 관리
│   │
│   ├── helpers/                    # 재사용 유틸리티
│   │   ├── __init__.py
│   │   ├── response.py             # 공통 응답 빌더
│   │   ├── pagination.py           # Cursor / Offset 페이지 헬퍼
│   │   ├── password.py             # bcrypt 해시/검증
│   │   ├── jwt_helper.py           # JWT 생성/검증 (RS256)
│   │   └── redis_client.py         # Redis 연결 풀 관리
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── engine.py               # SQLModel Engine / Session Factory
│   │
│   ├── models/                     # SQLModel 테이블 정의 (05_database_model.md)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── vehicle.py
│   │   ├── sensor.py
│   │   ├── alert.py
│   │   ├── trip.py
│   │   └── charging_station.py
│   │
│   ├── schemas/                    # Pydantic Request/Response DTO
│   │   ├── __init__.py
│   │   ├── common.py               # PaginationMeta, SuccessResponse, ErrorResponse
│   │   ├── auth.py
│   │   ├── vehicle.py
│   │   ├── sensor.py
│   │   ├── alert.py
│   │   ├── trip.py
│   │   └── charging_station.py
│   │
│   ├── repositories/               # DB 접근 계층 (쿼리 전담)
│   │   ├── __init__.py
│   │   ├── base_repository.py      # 공통 CRUD 제네릭
│   │   ├── user_repository.py      # ← 추가 (auth_service가 User 조회에 필요)
│   │   ├── vehicle_repository.py
│   │   ├── sensor_repository.py
│   │   ├── alert_repository.py
│   │   ├── trip_repository.py
│   │   └── charging_station_repository.py
│   │
│   ├── services/                   # 비즈니스 로직 계층
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── vehicle_service.py
│   │   ├── sensor_service.py
│   │   ├── alert_service.py
│   │   ├── trip_service.py
│   │   └── charging_station_service.py
│   │
│   └── routes/                     # 도메인별 라우트 블루프린트
│       ├── __init__.py
│       ├── auth_routes.py
│       ├── vehicle_routes.py
│       ├── sensor_routes.py
│       ├── alert_routes.py
│       ├── trip_routes.py
│       └── charging_station_routes.py
│
├── alembic/                        # DB 마이그레이션
│   ├── env.py
│   └── versions/
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── Makefile
```

---

## 3. 계층별 역할 및 코드 예시

### 3.1 진입점 — `app.py`

```python
# app.py
from chalice import Chalice
from chalicelib.routes.vehicle_routes import vehicle_bp
from chalicelib.routes.alert_routes    import alert_bp
from chalicelib.routes.sensor_routes   import sensor_bp
from chalicelib.routes.auth_routes     import auth_bp
from chalicelib.routes.trip_routes     import trip_bp
from chalicelib.routes.charging_station_routes import station_bp
from chalicelib.middlewares.error_handler import register_error_handlers

app = Chalice(app_name="bikefms-api")
app.debug = False  # 프로덕션에서 반드시 False

# ── 블루프린트 등록 ─────────────────────────────────────────────────
app.register_blueprint(auth_bp,    url_prefix="/v1/auth")
app.register_blueprint(vehicle_bp, url_prefix="/v1/vehicles")
app.register_blueprint(sensor_bp,  url_prefix="/v1/vehicles")
app.register_blueprint(alert_bp,   url_prefix="/v1/alerts")
app.register_blueprint(trip_bp,    url_prefix="/v1/vehicles")
app.register_blueprint(station_bp, url_prefix="/v1/charging-stations")

# ── 전역 에러 핸들러 등록 ────────────────────────────────────────────
register_error_handlers(app)
```

---

### 3.2 Route 계층 — `routes/vehicle_routes.py`

Route는 **HTTP 파라미터 추출 + 권한 검사 + Service 호출 + 응답 직렬화**만 담당합니다.  
비즈니스 로직은 절대 포함하지 않습니다.

> **Chalice 인증 패턴 주의사항**  
> Chalice에는 Flask의 `current_app`이 없습니다. 인증은 **헬퍼 함수** 방식으로 구현합니다.  
> Blueprint에서 `current_request`는 `blueprint_instance.current_request`로 접근합니다.  
> 다중 값 쿼리 파라미터(`status=A&status=B`)는 `request.multi_query_params`를 사용합니다.

```python
# chalicelib/routes/vehicle_routes.py
from chalice import Blueprint
from chalicelib.middlewares.auth import get_current_user, require_role_check
from chalicelib.middlewares.db_session import get_session
from chalicelib.helpers.response import ok, created
from chalicelib.schemas.vehicle import VehicleCreate, VehicleUpdate
from chalicelib.services.vehicle_service import VehicleService

vehicle_bp = Blueprint(__name__)


@vehicle_bp.route("/", methods=["GET"])
def list_vehicles():
    """GET /v1/vehicles"""
    req = vehicle_bp.current_request
    user = get_current_user(req)           # ← 헬퍼 함수로 JWT 검증

    # Chalice multi_query_params: 반복 키 → list 반환
    # ?status=ACTIVE&status=CHARGING → {"status": ["ACTIVE", "CHARGING"]}
    multi = req.multi_query_params or {}
    params = req.query_params or {}

    with get_session() as session:
        service = VehicleService(session)
        result = service.list_vehicles(
            status=multi.get("status") or [],   # ← getlist() 대신 multi_query_params
            driver_id=params.get("driver_id"),
            q=params.get("q"),
            page=int(params.get("page", 1)),
            limit=int(params.get("limit", 20)),
            sort_by=params.get("sort_by", "created_at"),
            order=params.get("order", "desc"),
            current_user=user,              # 역할 기반 필터링 위해 전달
        )
    return ok(result)


@vehicle_bp.route("/", methods=["POST"])
def create_vehicle():
    """POST /v1/vehicles"""
    req = vehicle_bp.current_request
    user = get_current_user(req)
    require_role_check(user, "ADMIN", "MANAGER")

    body = VehicleCreate(**req.json_body)
    with get_session() as session:
        service = VehicleService(session)
        vehicle = service.create_vehicle(body)
    return created(vehicle)


@vehicle_bp.route("/{vehicle_id}", methods=["GET"])
def get_vehicle(vehicle_id: str):
    """GET /v1/vehicles/{vehicle_id}"""
    user = get_current_user(vehicle_bp.current_request)
    with get_session() as session:
        service = VehicleService(session)
        vehicle = service.get_vehicle_by_id(vehicle_id, current_user=user)
    return ok(vehicle)


@vehicle_bp.route("/{vehicle_id}", methods=["PUT"])
def update_vehicle(vehicle_id: str):
    req = vehicle_bp.current_request
    user = get_current_user(req)
    require_role_check(user, "ADMIN", "MANAGER")

    body = VehicleUpdate(**req.json_body)
    with get_session() as session:
        service = VehicleService(session)
        vehicle = service.update_vehicle(vehicle_id, body)
    return ok(vehicle)


@vehicle_bp.route("/{vehicle_id}", methods=["DELETE"])
def delete_vehicle(vehicle_id: str):
    req = vehicle_bp.current_request
    user = get_current_user(req)
    require_role_check(user, "ADMIN")

    with get_session() as session:
        service = VehicleService(session)
        result = service.soft_delete_vehicle(vehicle_id)
    return ok(result)
```

---

### 3.3 Service 계층 — `services/vehicle_service.py`

Service는 **비즈니스 규칙, 유효성 검사, 트랜잭션 조율**을 담당합니다.

```python
# chalicelib/services/vehicle_service.py
from uuid import UUID
from sqlmodel import Session
from chalicelib.repositories.vehicle_repository import VehicleRepository
from chalicelib.helpers.redis_client import get_redis
from chalicelib.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleListResponse
from chalicelib.exceptions import NotFoundError, ConflictError
from chalicelib.helpers.pagination import build_offset_pagination


class VehicleService:

    def __init__(self, session: Session):
        self.repo  = VehicleRepository(session)
        self.redis = get_redis()

    # ── 목록 조회 ────────────────────────────────────────────────────
    def list_vehicles(self, *, status, driver_id, q, page, limit,
                      sort_by, order) -> VehicleListResponse:
        items, total = self.repo.find_all(
            status=status, driver_id=driver_id, q=q,
            page=page, limit=limit, sort_by=sort_by, order=order,
        )
        # 각 차량의 최신 상태를 Redis에서 병합
        for item in items:
            cached = self.redis.hgetall(f"vehicle:{item.id}:state")
            if cached:
                item.last_state = cached

        return VehicleListResponse(
            items=items,
            pagination=build_offset_pagination(total=total, page=page, limit=limit),
        )

    # ── 생성 ─────────────────────────────────────────────────────────
    def create_vehicle(self, data: VehicleCreate):
        # 중복 검사
        if self.repo.exists_by_plate(data.plate_number):
            raise ConflictError("이미 등록된 차량번호입니다.")
        if self.repo.exists_by_imei(data.imei):
            raise ConflictError("이미 등록된 IMEI입니다.")
        return self.repo.create(data)

    # ── 단건 조회 ────────────────────────────────────────────────────
    def get_vehicle_by_id(self, vehicle_id: str):
        vehicle = self.repo.find_by_id(UUID(vehicle_id))
        if not vehicle:
            raise NotFoundError("차량을 찾을 수 없습니다.")
        return vehicle

    # ── 수정 ─────────────────────────────────────────────────────────
    def update_vehicle(self, vehicle_id: str, data: VehicleUpdate):
        vehicle = self.get_vehicle_by_id(vehicle_id)
        return self.repo.update(vehicle, data)

    # ── 논리 삭제 ────────────────────────────────────────────────────
    def soft_delete_vehicle(self, vehicle_id: str):
        vehicle = self.get_vehicle_by_id(vehicle_id)
        result = self.repo.soft_delete(vehicle)
        # Redis 캐시 제거
        self.redis.delete(f"vehicle:{vehicle_id}:state")
        return result
```

---

### 3.4 Repository 계층 — `repositories/vehicle_repository.py`

Repository는 **SQLModel 쿼리 작성만** 담당합니다. 비즈니스 판단은 없습니다.

```python
# chalicelib/repositories/vehicle_repository.py
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID
from sqlmodel import Session, select, func, col
from chalicelib.models.vehicle import Vehicle, VehicleStatus


class VehicleRepository:

    def __init__(self, session: Session):
        self.session = session

    def find_all(
        self, *, status: List[str], driver_id: Optional[str],
        q: Optional[str], page: int, limit: int,
        sort_by: str, order: str,
    ) -> Tuple[List[Vehicle], int]:
        query = (
            select(Vehicle)
            .where(Vehicle.deleted_at.is_(None))  # 논리 삭제 제외
        )
        if status:
            query = query.where(col(Vehicle.status).in_(status))
        if driver_id:
            query = query.where(Vehicle.assigned_driver_id == UUID(driver_id))
        if q:
            query = query.where(
                col(Vehicle.plate_number).ilike(f"%{q}%")
                | col(Vehicle.model_name).ilike(f"%{q}%")
            )

        # 전체 카운트
        count_query = select(func.count()).select_from(query.subquery())
        total = self.session.exec(count_query).one()

        # 정렬 + 페이징
        sort_col = getattr(Vehicle, sort_by, Vehicle.created_at)
        sort_col = sort_col.desc() if order == "desc" else sort_col.asc()
        query = query.order_by(sort_col).offset((page - 1) * limit).limit(limit)

        items = self.session.exec(query).all()
        return items, total

    def find_by_id(self, vehicle_id: UUID) -> Optional[Vehicle]:
        return self.session.get(Vehicle, vehicle_id)

    def exists_by_plate(self, plate_number: str) -> bool:
        result = self.session.exec(
            select(Vehicle).where(Vehicle.plate_number == plate_number)
        ).first()
        return result is not None

    def exists_by_imei(self, imei: str) -> bool:
        result = self.session.exec(
            select(Vehicle).where(Vehicle.imei == imei)
        ).first()
        return result is not None

    def create(self, data) -> Vehicle:
        vehicle = Vehicle(**data.dict())
        self.session.add(vehicle)
        self.session.commit()
        self.session.refresh(vehicle)
        return vehicle

    def update(self, vehicle: Vehicle, data) -> Vehicle:
        for field, value in data.dict(exclude_unset=True).items():
            setattr(vehicle, field, value)
        vehicle.updated_at = datetime.now(timezone.utc)
        self.session.add(vehicle)
        self.session.commit()
        self.session.refresh(vehicle)
        return vehicle

    def soft_delete(self, vehicle: Vehicle) -> Vehicle:
        vehicle.deleted_at = datetime.now(timezone.utc)
        self.session.add(vehicle)
        self.session.commit()
        self.session.refresh(vehicle)
        return vehicle
```

---

## 4. Middleware & Helper 정의

### 4.1 인증 헬퍼 — `middlewares/auth.py`

> **설계 결정**: Chalice는 Flask의 `current_app`을 제공하지 않습니다.  
> 데코레이터 패턴 대신 **헬퍼 함수 패턴**을 사용합니다.  
> 각 Route에서 명시적으로 `get_current_user(req)` → `require_role_check(user, ...)` 순서로 호출합니다.  
> 이 방식이 Chalice Blueprint 환경에서 가장 명확하고 안전합니다.

```python
# chalicelib/middlewares/auth.py
from typing import Any
from chalice import Request
from chalicelib.helpers.jwt_helper import decode_jwt
from chalicelib.exceptions import UnauthorizedError, ForbiddenError


def get_current_user(request: Any) -> dict:
    """
    Request에서 JWT를 추출하고 검증 후 payload dict를 반환합니다.
    실패 시 UnauthorizedError를 raise합니다.

    사용법 (Route에서):
        user = get_current_user(vehicle_bp.current_request)
    """
    headers = request.headers or {}
    auth_header = headers.get("authorization", "")

    if not auth_header.startswith("Bearer "):
        raise UnauthorizedError("인증 토큰이 없습니다.")

    token = auth_header.split(" ", 1)[1]
    # decode_jwt 내부에서 만료 시 UnauthorizedError, 서명 불일치 시 UnauthorizedError 발생
    return decode_jwt(token)


def require_role_check(user: dict, *roles: str) -> None:
    """
    사용자 역할을 검사합니다. 권한 없으면 ForbiddenError를 raise합니다.
    반드시 get_current_user() 이후에 호출해야 합니다.

    사용법:
        user = get_current_user(req)
        require_role_check(user, "ADMIN", "MANAGER")
    """
    if user.get("role") not in roles:
        raise ForbiddenError(
            f"이 작업은 {', '.join(roles)} 권한이 필요합니다. "
            f"현재 역할: {user.get('role')}"
        )
```

---

### 4.2 전역 에러 핸들러 — `middlewares/error_handler.py`

> `@app.middleware("http")`는 Chalice 1.26+ 에서 지원합니다.  
> 이 미들웨어 내에서 커스텀 예외를 잡아 일관된 JSON 응답으로 변환합니다.

```python
# chalicelib/middlewares/error_handler.py
from chalice import Chalice, Response
from chalicelib.exceptions import (
    AppBaseError, NotFoundError, ConflictError,
    UnauthorizedError, ForbiddenError, ValidationError,
)
from chalicelib.helpers.response import error_response
import logging
import uuid

logger = logging.getLogger(__name__)


def register_error_handlers(app: Chalice) -> None:
    """
    Chalice app에 전역 HTTP 미들웨어를 등록합니다.
    모든 커스텀 비즈니스 예외를 표준 JSON 에러 응답으로 변환합니다.
    """
    @app.middleware("http")
    def global_error_middleware(event, get_response):
        request_id = str(uuid.uuid4())[:8]
        try:
            return get_response(event)
        except UnauthorizedError as e:
            code = "TOKEN_EXPIRED" if "만료" in str(e) or "expired" in str(e).lower() \
                   else "TOKEN_INVALID"
            return error_response(401, code, str(e), request_id)
        except ForbiddenError as e:
            return error_response(403, "PERMISSION_DENIED", str(e), request_id)
        except NotFoundError as e:
            return error_response(404, "NOT_FOUND", str(e), request_id)
        except ConflictError as e:
            return error_response(409, "CONFLICT", str(e), request_id)
        except ValidationError as e:
            return error_response(422, "UNPROCESSABLE", str(e), request_id)
        except AppBaseError as e:
            return error_response(400, "BAD_REQUEST", str(e), request_id)
        except Exception as e:
            logger.exception("[%s] Unhandled error: %s", request_id, e)
            return error_response(500, "INTERNAL_ERROR", "서버 오류가 발생했습니다.", request_id)
```

---

### 4.3 DB 세션 관리 — `middlewares/db_session.py`

```python
# chalicelib/middlewares/db_session.py
from contextlib import contextmanager
from sqlmodel import Session
from chalicelib.db.engine import engine


@contextmanager
def get_session():
    """
    SQLModel 세션 컨텍스트 매니저.
    Lambda 핸들러는 무상태이므로 요청마다 새 세션 생성/종료.
    예외 발생 시 자동 롤백.

    사용법:
        with get_session() as session:
            service = VehicleService(session)
            ...
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

---

### 4.4 DB 엔진 — `db/engine.py`

```python
# chalicelib/db/engine.py
from sqlmodel import create_engine
from chalicelib.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,           # Lambda 환경: 연결 수 최소화
    max_overflow=2,
    pool_pre_ping=True,    # 끊긴 연결 자동 감지
    pool_recycle=1800,     # 30분마다 연결 재생성
    echo=settings.DEBUG,   # 개발 환경에서만 SQL 로깅
)
```

---

### 4.5 공통 응답 헬퍼 — `helpers/response.py`

```python
# chalicelib/helpers/response.py
from datetime import datetime, timezone
from chalice import Response
import json
import uuid


def _build(success: bool, data=None, error=None, status_code: int = 200,
           request_id: str = None) -> Response:
    body = {
        "success": success,
        "data": data,
        "error": error,
        "meta": {
            "request_id": request_id or str(uuid.uuid4())[:8],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
    return Response(
        body=json.dumps(body, default=str, ensure_ascii=False),
        status_code=status_code,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


def ok(data) -> Response:
    return _build(True, data=data, status_code=200)

def created(data) -> Response:
    return _build(True, data=data, status_code=201)

def error_response(status: int, code: str, message: str,
                   request_id: str = None) -> Response:
    return _build(False,
                  error={"code": code, "message": message},
                  status_code=status,
                  request_id=request_id)
```

---

### 4.6 페이지 헬퍼 — `helpers/pagination.py`

```python
# chalicelib/helpers/pagination.py
import base64, json
from datetime import datetime
from uuid import UUID
from math import ceil


def build_offset_pagination(*, total: int, page: int, limit: int) -> dict:
    total_pages = ceil(total / limit) if limit else 1
    return {
        "type": "offset",
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


def encode_cursor(time: datetime, record_id: UUID) -> str:
    raw = json.dumps({"time": time.isoformat(), "id": str(record_id)})
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> dict:
    raw = base64.urlsafe_b64decode(cursor.encode() + b"==").decode()
    return json.loads(raw)


def build_cursor_pagination(*, items: list, limit: int,
                             time_field: str = "time",
                             id_field: str = "vehicle_id") -> dict:
    has_next = len(items) == limit
    next_cursor = None
    if has_next and items:
        last = items[-1]
        next_cursor = encode_cursor(
            getattr(last, time_field),
            getattr(last, id_field),
        )
    return {
        "type": "cursor",
        "next_cursor": next_cursor,
        "has_next": has_next,
        "limit": limit,
    }
```

---

### 4.7 커스텀 예외 — `exceptions.py`

```python
# chalicelib/exceptions.py

class AppBaseError(Exception):
    """모든 비즈니스 예외의 기반 클래스"""
    pass

class NotFoundError(AppBaseError):
    pass

class ConflictError(AppBaseError):
    pass

class UnauthorizedError(AppBaseError):
    pass

class ForbiddenError(AppBaseError):
    pass

class ValidationError(AppBaseError):
    pass
```

---

### 4.8 설정 관리 — `config.py`

```python
# chalicelib/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DB
    DATABASE_URL     : str
    REDIS_URL        : str   = "redis://localhost:6379/0"

    # JWT
    JWT_PRIVATE_KEY  : str   # RS256 Private Key (PEM)
    JWT_PUBLIC_KEY   : str   # RS256 Public Key (PEM)
    JWT_EXPIRE_SEC   : int   = 3600

    # 환경
    ENV              : str   = "production"
    DEBUG            : bool  = False

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

### 4.9 제네릭 Base Repository — `repositories/base_repository.py`

```python
# chalicelib/repositories/base_repository.py
from typing import Generic, TypeVar, Type, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlmodel import SQLModel, Session, select

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseRepository(Generic[ModelT]):
    """
    공통 CRUD 제네릭 베이스.
    도메인 Repository는 이 클래스를 상속하여 특화 쿼리만 추가합니다.
    """
    model: Type[ModelT]

    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, record_id: UUID) -> Optional[ModelT]:
        return self.session.get(self.model, record_id)

    def create(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def save(self, instance: ModelT) -> ModelT:
        """수정된 인스턴스를 저장합니다."""
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def soft_delete(self, instance: ModelT) -> ModelT:
        """deleted_at을 설정하는 논리 삭제. SoftDeleteMixin이 있는 모델에만 사용."""
        instance.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
        return self.save(instance)
```

---

### 4.10 CORS 설정 — `app.py`

```python
# app.py에 CORS 미들웨어 추가
from chalice import Chalice, CORSConfig

app = Chalice(app_name="bikefms-api")

# ── CORS 설정 ─────────────────────────────────────────────────────────
# Chalice는 라우트별 CORSConfig 또는 전역 미들웨어로 CORS를 처리합니다.
# 전역 처리를 위해 @app.middleware 사용:

@app.middleware("http")
def cors_middleware(event, get_response):
    response = get_response(event)
    # 개발 환경에서는 모든 origin 허용, 프로덕션에서는 명시적 도메인만 허용
    allowed_origin = (
        "*" if get_settings().ENV == "development"
        else "https://dashboard.bikefms.io"
    )
    response.headers.update({
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
        "Access-Control-Allow-Credentials": "true",
    })
    return response
```

> **Preflight(OPTIONS) 처리**: API Gateway 레벨에서 OPTIONS 메서드를 활성화하거나,  
> `.chalice/config.json`에 `"cors": true` 설정으로 처리할 수 있습니다.

---

## 5. 계층 간 의존 흐름

```mermaid
graph LR
    A["HTTP Request<br/>(API Gateway)"] --> B["app.py<br/>(Chalice Route)"]
    B --> C["CORS Middleware<br/>+ Error Middleware"]
    C --> D["Route Blueprint<br/>get_current_user / require_role_check<br/>파라미터 추출 + 응답 직렬화"]
    D --> E["Service<br/>비즈니스 로직"]
    E --> F["Repository<br/>DB 쿼리"]
    E --> G["Redis Helper<br/>캐시 R/W"]
    F --> H[(PostgreSQL /<br/>TimescaleDB)]
    G --> I[(Redis)]
    D --> J["Response Helper<br/>Envelope 생성"]
    J --> K["HTTP Response"]

    style A fill:#1e293b,color:#94a3b8
    style K fill:#1e293b,color:#94a3b8
    style H fill:#166534,color:#bbf7d0
    style I fill:#7f1d1d,color:#fecaca
```

---

## 6. `.chalice/config.json` — 환경별 설정

```json
{
  "version": "2.0",
  "app_name": "bikefms-api",
  "stages": {
    "dev": {
      "api_gateway_stage": "dev",
      "environment_variables": {
        "ENV": "development",
        "DEBUG": "true",
        "DATABASE_URL": "postgresql+psycopg2://user:pass@dev-db:5432/bikefms"
      },
      "lambda_memory_size": 512,
      "lambda_timeout": 30
    },
    "prod": {
      "api_gateway_stage": "prod",
      "environment_variables": {
        "ENV": "production",
        "DEBUG": "false"
      },
      "lambda_memory_size": 1024,
      "lambda_timeout": 30,
      "reserved_concurrency": 50,
      "layers": [
        "arn:aws:lambda:ap-northeast-2:ACCOUNT_ID:layer:bikefms-deps:1"
      ]
    }
  }
}
```
