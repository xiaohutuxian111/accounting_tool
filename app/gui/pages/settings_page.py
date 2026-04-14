# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:39
# @Author : stone

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.settings_service import SettingsService


class SettingsPage(QWidget):
    theme_changed = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.settings_service = SettingsService(config)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("设置中心")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        form = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.config.get("app.theme", "dark"))

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["zh-CN", "en-US"])
        self.lang_combo.setCurrentText(self.config.get("app.language", "zh-CN"))

        self.use_gpu = QCheckBox("启用 GPU OCR")
        self.use_gpu.setChecked(self.config.get("ocr.use_gpu", False))

        self.save_debug = QCheckBox("保存调试图片")
        self.save_debug.setChecked(self.config.get("ocr.save_debug_image", True))

        self.auto_validate = QCheckBox("自动校验发票")
        self.auto_validate.setChecked(self.config.get("invoice.auto_validate", True))

        form.addRow("主题", self.theme_combo)
        form.addRow("语言", self.lang_combo)
        form.addRow("", self.use_gpu)
        form.addRow("", self.save_debug)
        form.addRow("", self.auto_validate)

        layout.addLayout(form)

        self.btn_save = QPushButton("保存配置")
        self.btn_save.clicked.connect(self.save_settings)
        layout.addWidget(self.btn_save)

        layout.addStretch()

    def save_settings(self):
        theme = self.theme_combo.currentText()

        self.config.config.setdefault("app", {})["theme"] = theme
        self.config.config.setdefault("app", {})["language"] = self.lang_combo.currentText()
        self.config.config.setdefault("ocr", {})["use_gpu"] = self.use_gpu.isChecked()
        self.config.config.setdefault("ocr", {})["save_debug_image"] = self.save_debug.isChecked()
        self.config.config.setdefault("invoice", {})["auto_validate"] = self.auto_validate.isChecked()

        self.settings_service.save()

        # 发射主题切换信号
        self.theme_changed.emit(theme)

        QMessageBox.information(self, "配置已保存", "设置已保存成功")
