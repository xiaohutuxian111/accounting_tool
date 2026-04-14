# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from app.core.logging import setup_logger


class SettingsService:
    def __init__(self, config):
        self.config = config

    def save(self, path: str = "config/config.yaml") -> None:
        """保存当前配置，并立即刷新目录与日志配置。"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.config.save(path)

        for key in [
            "storage.export_dir",
            "storage.debug_dir",
            "storage.temp_dir",
            "log.dir",
        ]:
            Path(self.config.get(key)).mkdir(parents=True, exist_ok=True)

        setup_logger(
            log_dir=self.config.get("log.dir", "logs"),
            level=self.config.get("log.level", "INFO"),
        )

    def get_theme(self) -> str:
        return self.config.get("app.theme", "dark")

    def set_theme(self, theme: str) -> None:
        self.config.config.setdefault("app", {})["theme"] = theme

    def get_theme_color(self) -> str:
        return self.config.get("app.theme_color", "#2dd36f")

    def set_theme_color(self, color: str) -> None:
        self.config.config.setdefault("app", {})["theme_color"] = color

    def get_language(self) -> str:
        return self.config.get("app.language", "zh-CN")

    def set_language(self, language: str) -> None:
        self.config.config.setdefault("app", {})["language"] = language

    def get_remember_window_size(self) -> bool:
        return self.config.get("app.remember_window_size", True)

    def set_remember_window_size(self, remember: bool) -> None:
        self.config.config.setdefault("app", {})["remember_window_size"] = remember

    def get_use_gpu(self) -> bool:
        return self.config.get("ocr.use_gpu", False)

    def set_use_gpu(self, use_gpu: bool) -> None:
        self.config.config.setdefault("ocr", {})["use_gpu"] = use_gpu

    def get_save_debug_image(self) -> bool:
        return self.config.get("ocr.save_debug_image", True)

    def set_save_debug_image(self, value: bool) -> None:
        self.config.config.setdefault("ocr", {})["save_debug_image"] = value
