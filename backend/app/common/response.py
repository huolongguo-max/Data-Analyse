from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def ok(data: Any = None, message: str = "success") -> JSONResponse:
    return JSONResponse(content=jsonable_encoder({"code": 200, "message": message, "data": data}))


def created(data: Any = None, message: str = "created") -> JSONResponse:
    return JSONResponse(status_code=201, content=jsonable_encoder({"code": 201, "message": message, "data": data}))


def paginated(items: list, total: int, page: int, page_size: int) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder({
        "code": 200,
        "message": "success",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }))
