from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.utils.hash_utils import sha256_file


@dataclass(frozen=True)
class StoredLocalFile:
    path: Path
    sha256: str
    size_bytes: int


def sanitize_filename(filename: str | None, fallback: str = "uploaded.xlsx") -> str:
    if not filename:
        return fallback
    return Path(filename).name or fallback


def build_batch_storage_dir(base_dir: Path, period_code: str, upload_seq: int, role: str) -> Path:
    return base_dir / period_code / f"upload_{upload_seq:03d}" / role


def store_upload_file(upload_file: UploadFile, destination: str | Path) -> StoredLocalFile:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    upload_file.file.seek(0)
    with destination.open("wb") as output:
        shutil.copyfileobj(upload_file.file, output)

    return StoredLocalFile(
        path=destination,
        sha256=sha256_file(destination),
        size_bytes=destination.stat().st_size,
    )


def describe_local_file(path: str | Path) -> StoredLocalFile:
    path = Path(path)
    return StoredLocalFile(
        path=path,
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
    )


def build_original_workbook_path(period_code: str, upload_seq: int, filename: str) -> Path:
    safe_name = sanitize_filename(filename)
    return build_batch_storage_dir(settings.UPLOAD_DIR, period_code, upload_seq, "original") / safe_name


def build_completed_workbook_dir(period_code: str, upload_seq: int) -> Path:
    return build_batch_storage_dir(settings.EXPORT_DIR, period_code, upload_seq, "completed")
