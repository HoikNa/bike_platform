from chalice import Blueprint, Response
from chalicelib.core.database import get_session
from chalicelib.core.cors import cors_config
from chalicelib.services.trip_service import TripService
from chalicelib.core.exceptions import APIException
from chalicelib.middlewares.auth import require_role

trip_bp = Blueprint(__name__)


@trip_bp.route('/trips', methods=['GET'], cors=cors_config)
def get_trips():
    request = trip_bp.current_request
    try:
        require_role(request, ["MANAGER", "ADMIN"])
        qp = request.query_params or {}

        page       = int(qp.get("page", 1))
        page_size  = int(qp.get("page_size", 20))
        vehicle_id = qp.get("vehicle_id") or None
        driver_id  = qp.get("driver_id") or None

        with get_session() as session:
            data, meta = TripService.list_trips(
                session,
                page=page,
                page_size=page_size,
                vehicle_id=vehicle_id,
                driver_id=driver_id,
            )
            return Response(
                body={
                    "success": True,
                    "data": [t.model_dump(mode="json") for t in data],
                    "meta": meta,
                },
                status_code=200,
            )
    except APIException as e:
        return Response(body={"success": False, "error": {"code": e.code, "message": e.message}}, status_code=e.status_code)
    except Exception as e:
        return Response(body={"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}, status_code=500)
