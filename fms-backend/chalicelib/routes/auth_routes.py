from chalice import Blueprint, Response
from chalicelib.core.database import get_session
from chalicelib.services.auth_service import AuthService
from chalicelib.core.exceptions import APIException
from pydantic import ValidationError
from chalicelib.schemas.auth import LoginRequest

auth_bp = Blueprint(__name__)

@auth_bp.route('/auth/login', methods=['POST'], cors=True)
def login():
    request = auth_bp.current_request
    try:
        body = LoginRequest(**request.json_body)
        with get_session() as session:
            result = AuthService.authenticate_user(session, body.email, body.password)
            return Response(body={"success": True, "data": result}, status_code=200)
    except APIException as e:
        return Response(body={"success": False, "error": {"code": e.code, "message": e.message}}, status_code=e.status_code)
    except ValidationError as e:
        return Response(body={"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}}, status_code=400)
    except Exception as e:
        return Response(body={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}, status_code=500)

@auth_bp.route('/auth/me', methods=['GET'], cors=True)
def get_me():
    request = auth_bp.current_request
    from chalicelib.middlewares.auth import require_role
    try:
        user_payload = require_role(request, ["ADMIN", "MANAGER", "DRIVER"])
        return Response(body={"success": True, "data": user_payload}, status_code=200)
    except APIException as e:
        return Response(body={"success": False, "error": {"code": e.code, "message": e.message}}, status_code=e.status_code)
    except Exception as e:
        return Response(body={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}, status_code=500)

