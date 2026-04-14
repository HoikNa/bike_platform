from chalice import Blueprint, Response
from chalicelib.core.database import get_session
from chalicelib.core.cors import cors_config
from chalicelib.services.alert_service import AlertService
from chalicelib.core.exceptions import APIException
from chalicelib.middlewares.auth import require_role, get_current_user_from_request

alert_bp = Blueprint(__name__)


@alert_bp.route('/alerts', methods=['GET'], cors=cors_config)
def get_alerts():
    request = alert_bp.current_request
    try:
        require_role(request, ["MANAGER", "ADMIN"])
        qp = request.query_params or {}

        limit      = int(qp.get("limit", 30))
        cursor     = qp.get("cursor") or None
        vehicle_id = qp.get("vehicle_id") or None
        sev_raw    = qp.get("severity") or None
        severity   = sev_raw.split(",") if sev_raw else None

        is_ack = None
        if "is_acknowledged" in qp:
            is_ack = qp["is_acknowledged"].lower() == "true"

        with get_session() as session:
            data, next_cursor, has_next = AlertService.list_alerts(
                session,
                limit=limit,
                cursor=cursor,
                vehicle_id=vehicle_id,
                severity=severity,
                is_acknowledged=is_ack,
            )
            return Response(
                body={
                    "success": True,
                    "data": [a.model_dump(mode="json") for a in data],
                    "meta": {
                        "has_next": has_next,
                        "next_cursor": next_cursor,
                    },
                },
                status_code=200,
            )
    except APIException as e:
        return Response(body={"success": False, "error": {"code": e.code, "message": e.message}}, status_code=e.status_code)
    except Exception as e:
        return Response(body={"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}, status_code=500)


@alert_bp.route('/alerts', methods=['POST'], cors=cors_config)
def create_alert():
    """시뮬레이터 / 내부 이벤트 감지기 → 알림 직접 생성.

    Body:
        vehicle_id          (str UUID)  차량 ID
        alert_type          (str)       AlertType enum 값
        severity            (str)       AlertSeverity enum 값
        title               (str)       알림 제목
        description         (str?)      상세 설명
        speed_at_trigger    (float?)    발생 시 속도
        battery_at_trigger  (float?)    발생 시 배터리
        location_lat        (float?)    발생 위치 위도
        location_lng        (float?)    발생 위치 경도
    """
    request = alert_bp.current_request
    try:
        require_role(request, ["DRIVER", "MANAGER", "ADMIN"])
        body = request.json_body or {}

        with get_session() as session:
            alert = AlertService.create_alert(session, body)
            return Response(
                body={"success": True, "data": alert.model_dump(mode="json")},
                status_code=201,
            )
    except APIException as e:
        return Response(body={"success": False, "error": {"code": e.code, "message": e.message}}, status_code=e.status_code)
    except Exception as e:
        return Response(body={"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}, status_code=500)


@alert_bp.route('/alerts/{alert_id}/acknowledge', methods=['PATCH'], cors=cors_config)
def acknowledge_alert(alert_id):
    request = alert_bp.current_request
    try:
        user = require_role(request, ["MANAGER", "ADMIN"])

        with get_session() as session:
            updated = AlertService.acknowledge(session, alert_id, user["sub"])
            return Response(
                body={"success": True, "data": updated.model_dump(mode="json")},
                status_code=200,
            )
    except APIException as e:
        return Response(body={"success": False, "error": {"code": e.code, "message": e.message}}, status_code=e.status_code)
    except Exception as e:
        return Response(body={"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}, status_code=500)
