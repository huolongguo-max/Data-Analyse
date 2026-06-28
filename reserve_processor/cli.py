# reserve_processor/cli.py

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import process_xlsx_to_xlsx


def main():
    parser = argparse.ArgumentParser(description="储备表 xlsx 自动计算脚本")
    parser.add_argument("--input", required=True, help="输入 xlsx 路径")
    parser.add_argument(
        "--output",
        help="输出 xlsx 路径；不传时默认在原文件同目录生成“原文件名-补全.xlsx”",
    )

    args = parser.parse_args()

    result = process_xlsx_to_xlsx(
        input_path=Path(args.input),
        output_path=Path(args.output) if args.output else None,
    )

    print("处理完成")
    print(f"输出文件: {result.output_path}")
    print(f"文件名: {result.meta.filename}")
    print(f"年份: {result.meta.year}")
    print(f"月期: {result.meta.month}")
    print(f"版本: {result.meta.version}")
    print(f"日期编码: {result.meta.file_date_code}")

    if result.warnings:
        print("warnings:")
        for warning in result.warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
