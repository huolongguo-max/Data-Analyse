from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILES = (
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "backend" / ".env",
)
DEFAULT_DATABASE_URL = "sqlite:///data/local-dev.db"


def _resolve_storage_path(path_value: Path) -> Path:
    if path_value.is_absolute():
        return path_value
    return (PROJECT_ROOT / path_value).resolve()


def _resolve_database_url(database_url: str) -> str:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite":
        return database_url

    if not url.database or url.database == ":memory:":
        return database_url

    database_path = Path(url.database)
    if database_path.is_absolute():
        return database_url

    return str(url.set(database=(PROJECT_ROOT / database_path).resolve().as_posix()))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=tuple(str(path) for path in ENV_FILES),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = DEFAULT_DATABASE_URL

    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h

    UPLOAD_DIR: Path = Path("data/uploads")
    EXPORT_DIR: Path = Path("data/exports")
    BACKUP_DIR: Path = Path("data/backups")
    LOG_DIR: Path = Path("data/logs")

    MAX_UPLOAD_SIZE_MB: int = 100

    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    def normalize_paths(self) -> None:
        self.DATABASE_URL = _resolve_database_url(self.DATABASE_URL)
        self.UPLOAD_DIR = _resolve_storage_path(self.UPLOAD_DIR)
        self.EXPORT_DIR = _resolve_storage_path(self.EXPORT_DIR)
        self.BACKUP_DIR = _resolve_storage_path(self.BACKUP_DIR)
        self.LOG_DIR = _resolve_storage_path(self.LOG_DIR)

    def ensure_dirs(self) -> None:
        for path in (self.UPLOAD_DIR, self.EXPORT_DIR, self.BACKUP_DIR, self.LOG_DIR):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def cors_origins(self) -> list[str]:
        origins = [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]
        return origins or ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def cors_allow_credentials(self) -> bool:
        return "*" not in self.cors_origins

    @property
    def is_sqlite(self) -> bool:
        return make_url(self.DATABASE_URL).get_backend_name() == "sqlite"


settings = Settings()
settings.normalize_paths()
settings.ensure_dirs()
