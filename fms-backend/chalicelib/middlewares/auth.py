from chalice import UnauthorizedError, ForbiddenError
from chalicelib.core.jwt_helper import decode_access_token

def get_current_user_from_request(current_request):
    auth_header = current_request.headers.get('authorization', '')
    if not auth_header.startswith('Bearer '):
        raise UnauthorizedError("Missing or invalid token")
    
    token = auth_header.split(' ')[1]
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedError("Token is invalid or expired")
    
    return payload

def require_role(current_request, required_roles: list):
    user = get_current_user_from_request(current_request)
    if user.get("role") not in required_roles:
        raise ForbiddenError("You do not have permission to perform this action")
    return user
