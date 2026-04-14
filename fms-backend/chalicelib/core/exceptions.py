class APIException(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(self.message)

class NotFoundException(APIException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(404, "NOT_FOUND", message)

class UnauthorizedException(APIException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(401, "UNAUTHORIZED", message)

class ForbiddenException(APIException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(403, "FORBIDDEN", message)

class BadRequestException(APIException):
    def __init__(self, message: str = "Bad Request"):
        super().__init__(400, "BAD_REQUEST", message)
