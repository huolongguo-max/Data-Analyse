from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reserve_processor.excel_io import read_xlsx, write_rounded_export_copy  # noqa: E402
from reserve_processor.filename_parser import parse_filename  # noqa: E402
from reserve_processor.pipeline import process_xlsx_to_xlsx  # noqa: E402
from reserve_processor.utils import build_completed_output_path  # noqa: E402

__all__ = [
    "build_completed_output_path",
    "parse_filename",
    "process_xlsx_to_xlsx",
    "read_xlsx",
    "write_rounded_export_copy",
]
