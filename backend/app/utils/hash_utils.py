from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    file_hash = hashlib.sha256()

    with Path(path).open("rb") as file_obj:
        while chunk := file_obj.read(chunk_size):
            file_hash.update(chunk)

    return file_hash.hexdigest()
