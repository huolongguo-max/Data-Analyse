from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app import models  # noqa: F401
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import auth, dashboard, exports, health, imports, users

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_ASSETS_DIR = STATIC_DIR / "assets"

SUPER_ADMINS = (
    {"username": "huolong1", "password": "1610499658"},
    {"username": "admin2", "password": "codemao1234"},
)


def _seed_super_admins(db: Session) -> None:
    from app.common.security import hash_password
    from app.models.user import User

    allowed_usernames = tuple(admin["username"] for admin in SUPER_ADMINS)

    for admin in SUPER_ADMINS:
        user = db.query(User).filter(User.username == admin["username"]).first()
        if user is None:
            db.add(User(
                username=admin["username"],
                hashed_password=hash_password(admin["password"]),
                role="super_admin",
                is_active=True,
            ))
            continue

        user.role = "super_admin"
        user.is_active = True

    legacy_super_admins = (
        db.query(User)
        .filter(User.role == "super_admin", ~User.username.in_(allowed_usernames))
        .all()
    )
    for user in legacy_super_admins:
        user.is_active = False

    db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.is_sqlite:
        Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_super_admins(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="本地数据分析工具",
    description="企业内网本地数据分析平台 API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": f"服务器内部错误：{type(exc).__name__}: {exc}", "data": None},
    )


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(imports.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(exports.router, prefix="/api")

if STATIC_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_ASSETS_DIR), name="assets")
elif STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/", include_in_schema=False)
def frontend_index():
    return FileResponse(STATIC_DIR / "index.html")
