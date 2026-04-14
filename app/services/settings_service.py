# -*- coding: utf-8 -*-
# @Time : 2026/4/14 10:01
# @Author : stone


from __future__ import annotations

from pathlib import Path


class SettingsService:
    def __init__(self, config):
        self.config = config

    def save(self, path: str = "config/config.yaml") -> None:
        """保存当前配置到配置文件"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.config.save(path)

    def get_theme(self) -> str:
        return self.config.get("app.theme", "dark")

    def set_theme(self, theme: str) -> None:
        self.config.config.setdefault("app", {})["theme"] = theme

    def get_language(self) -> str:
        return self.config.get("app.language", "zh-CN")

    def set_language(self, language: str) -> None:
        self.config.config.setdefault("app", {})["language"] = language

    def get_use_gpu(self) -> bool:
        return self.config.get("ocr.use_gpu", False)

    def set_use_gpu(self, use_gpu: bool) -> None:
        self.config.config.setdefault("ocr", {})["use_gpu"] = use_gpu

    def get_save_debug_image(self) -> bool:
        return self.config.get("ocr.save_debug_image", True)

    def set_save_debug_image(self, value: bool) -> None:
        self.config.config.setdefault("ocr", {})["save_debug_image"] = value

    def get_auto_validate(self) -> bool:
        return self.config.get("invoice.auto_validate", True)

    def set_auto_validate(self, value: bool) -> None:
        self.config.config.setdefault("invoice", {})["auto_validate"] = value