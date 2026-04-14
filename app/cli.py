# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="accounting-tool",
        description="会计工具合集",
    )

    parser.add_argument("--theme", choices=["dark", "light", "auto"], help="应用主题")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="日志级别")
    parser.add_argument("--use-gpu", action="store_true", help="启用 GPU OCR")

    subparsers = parser.add_subparsers(dest="command")

    ocr_parser = subparsers.add_parser("invoice-ocr", help="发票识别")
    ocr_parser.add_argument("file", help="图片路径")

    return parser
