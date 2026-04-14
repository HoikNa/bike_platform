from chalice import Blueprint, Response
from chalicelib.core.database import get_session
from chalicelib.core.cors import cors_config
from chalicelib.services.vehicle_service import VehicleService
from chalicelib.core.exceptions import APIException, NotFoundException
from chalicelib.middlewares.auth import require_role
import math

vehicle_bp = Blueprint(__name__)


@vehicle_bp.route('/vehicles', methods=['GET'], cors=cors_config)
def get_vehicles():
    request = vehicle_bp.current_request
    try:
        require_role(request, ["DRIVER", "MANAGER", "ADMIN"])
        qp = request.query_params or {}
        page_size = int(qp.get("page_size", 50))
        page      = max(1, int(qp.get("page", 1)))
        offset    = (page - 1) * page_size
        q         = qp.get("q") or None
        status_raw = qp.get("status") or None
        status_filter = status_raw.split(",") if status_raw else None

        with get_session() as session:
            data, total = VehicleService.list_vehicles(
                session, limit=page_size, offset=offset,
                status_filter=status_filter, q=q,
            )
            return Response(
                body={
                    "success": True,
                    "data": [v.model_dump(mode="json") for v in data],
                    "meta": {
                        "total": total,
                        "page": page,
                        "page_size": page_size,
                        "total_pages": math.ceil(total / page_size) if page_size else 1,
                    },
                },
                status_code=200,
            )
    except APIException as e:
        return Response(body={"success": False, "error": {"code": e.code, "message": e.message}}, status_code=e.status_code)
    except Exception as e:
        return Response(body={"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}, status_code=500)


@vehicle_bp.route('/vehicles/{vehicle_id}/telemetry', methods=['PUT'], cors=cors_config)
def update_telemetry(vehicle_id):
    """IoT 단말기 / 시뮬레이터 → 실시간 센서 데이터 수신.

    Body:
        latitude           (float)  위도
        longitude          (float)  경도
        speed_kmh          (float)  속도 km/h
        battery_level_pct  (float)  배터리 잔량 %
        engine_temp_celsius(float)  엔진 온도 °C
    """
    request = vehicle_bp.current_request
    try:
        require_role(request, ["DRIVER", "MANAGER", "ADMIN"])
        body = request.json_body or {}

        with get_session() as session:
            result = VehicleService.update_telemetry(session, vehicle_id, body)
            return Response(body={"success": True, "data": result}, status_code=200)
    except NotFoundException as e:
        return Response(body={"success": False, "error": {"code": "NOT_FOUND", "message": str(e)}}, status_code=404)
    except APIException as e:
        return Response(body={"success": False, "error": {"code": e.code, "message": e.message}}, status_code=e.status_code)
    except Exception as e:
        return Response(body={"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}, status_code=500)


@vehicle_bp.route('/vehicles/{vehicle_id}', methods=['GET'], cors=cors_config)
def get_vehicle(vehicle_id):
    request = vehicle_bp.current_request
    try:
        require_role(request, ["DRIVER", "MANAGER", "ADMIN"])

        with get_session() as session:
            vehicle = VehicleService.get_vehicle_detail(session, vehicle_id)
            if not vehicle:
                return Response(
                    body={"success": False, "error": {"code": "NOT_FOUND", "message": "Vehicle not found"}},
                    status_code=404,
                )
            return Response(
                body={"success": True, "data": vehicle.model_dump(mode="json")},
                status_code=200,
            )
    except APIException as e:
        return Response(body={"success": False, "error": {"code": e.code, "message": e.message}}, status_code=e.status_code)
    except Exception as e:
        return Response(body={"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}, status_code=500)
