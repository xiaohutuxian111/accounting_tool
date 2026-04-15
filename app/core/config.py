# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "app": {
        "name": "会计助手",
        "theme": "dark",
        "theme_color": "#2dd36f",
        "language": "zh-CN",
        "remember_window_size": True,
        "window_width": 1050,
        "window_height": 800,
    },
    "ocr": {
        "engine": "paddleocr",
        "lang": "ch",
        "use_gpu": False,
        "save_debug_image": True,
    },
    "storage": {
        "db_path": "data/db/accounting.db",
        "export_dir": "data/export",
        "debug_dir": "data/debug",
        "temp_dir": "data/temp",
    },
    "log": {
        "level": "INFO",
        "dir": "logs",
    },
}


def deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class AppConfig:
    def __init__(self, cli_args: argparse.Namespace | None = None) -> None:
        self.config = dict(DEFAULT_CONFIG)
        self.runtime_root = self._resolve_runtime_root()

        config_path = self.runtime_root / "config" / "config.yaml"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as file:
                file_config = yaml.safe_load(file) or {}
            self.config = deep_merge(self.config, file_config)

        env_config = self._load_from_env()
        self.config = deep_merge(self.config, env_config)

        if cli_args:
            cli_config = self._load_from_cli(cli_args)
            self.config = deep_merge(self.config, cli_config)

        self._normalize_runtime_paths()

    @staticmethod
    def _resolve_runtime_root() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path.cwd().resolve()

    def _normalize_runtime_paths(self) -> None:
        for section, key in [
            ("storage", "db_path"),
            ("storage", "export_dir"),
            ("storage", "debug_dir"),
            ("storage", "temp_dir"),
            ("log", "dir"),
        ]:
            value = self.config.get(section, {}).get(key)
            if not value:
                continue
            path = Path(value)
            if not path.is_absolute():
                self.config.setdefault(section, {})[key] = str((self.runtime_root / path).resolve())

    def _load_from_env(self) -> dict[str, Any]:
        env: dict[str, Any] = {}

        theme = os.getenv("ACCOUNTING_TOOL_APP_THEME")
        if theme:
            env.setdefault("app", {})["theme"] = theme

        theme_color = os.getenv("ACCOUNTING_TOOL_APP_THEME_COLOR")
        if theme_color:
            env.setdefault("app", {})["theme_color"] = theme_color

        log_level = os.getenv("ACCOUNTING_TOOL_LOG_LEVEL")
        if log_level:
            env.setdefault("log", {})["level"] = log_level

        use_gpu = os.getenv("ACCOUNTING_TOOL_OCR_USE_GPU")
        if use_gpu is not None:
            env.setdefault("ocr", {})["use_gpu"] = use_gpu.lower() == "true"

        return env

    def _load_from_cli(self, args: argparse.Namespace) -> dict[str, Any]:
        cli: dict[str, Any] = {}

        if getattr(args, "theme", None):
            cli.setdefault("app", {})["theme"] = args.theme

        if getattr(args, "log_level", None):
            cli.setdefault("log", {})["level"] = args.log_level

        if getattr(args, "use_gpu", None) is not None:
            cli.setdefault("ocr", {})["use_gpu"] = args.use_gpu

        return cli

    def get(self, dotted_key: str, default=None):
        current = self.config
        for part in dotted_key.split("."):
            if not isinstance(current, dict):
                return default
            current = current.get(part, default)
        return current

    def save(self, path: str = "config/config.yaml") -> None:
        save_path = Path(path)
        if not save_path.is_absolute():
            save_path = self.runtime_root / save_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as file:
            yaml.safe_dump(self.config, file, allow_unicode=True, sort_keys=False)
