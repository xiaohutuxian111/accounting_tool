# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:33
# @Author : stone



from __future__ import annotations

import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_dir: str, level: str = "INFO") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        enqueue=False,
    )
    logger.add(
        str(Path(log_dir) / "app.log"),
        level=level,
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
        enqueue=False,
    )
