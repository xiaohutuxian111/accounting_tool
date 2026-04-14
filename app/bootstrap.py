# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:34
# @Author : stone




from __future__ import annotations

from pathlib import Path

from app.core.config import AppConfig
from app.core.logging import setup_logger
from app.db.sqlite_manager import SQLiteManager


def bootstrap(cli_args=None) -> AppConfig:
    config = AppConfig(cli_args)

    for key in [
        "storage.export_dir",
        "storage.debug_dir",
        "storage.temp_dir",
        "log.dir",
    ]:
        Path(config.get(key)).mkdir(parents=True, exist_ok=True)

    setup_logger(
        log_dir=config.get("log.dir"),
        level=config.get("log.level", "INFO"),
    )

    db = SQLiteManager(config)
    db.init_db()

    return config