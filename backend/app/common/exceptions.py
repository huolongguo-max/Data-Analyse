from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(self, status_code: int = 400, message: str = "请求错误", data: dict | None = None):
        super().__init__(status_code=status_code, detail={"code": status_code, "message": message, "data": data})


class NotFoundError(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(status_code=404, message=message)


class ForbiddenError(AppException):
    def __init__(self, message: str = "无操作权限"):
        super().__init__(status_code=403, message=message)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "未登录或 Token 已过期"):
        super().__init__(status_code=401, message=message)


class ValidationError(AppException):
    def __init__(self, message: str = "数据校验失败"):
        super().__init__(status_code=422, message=message)


class ConflictError(AppException):
    def __init__(self, message: str = "数据冲突"):
        super().__init__(status_code=409, message=message)
