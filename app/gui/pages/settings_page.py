# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QWidget
from qfluentwidgets import (
    ExpandLayout,
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
    PrimaryPushSettingCard,
    ScrollArea,
    SettingCardGroup,
    SwitchSettingCard,
)

from app.gui.components.fluent_setting_cards import (
    ColorSettingCard,
    ComboBoxSettingCard,
    EditComboBoxSettingCard,
    LineEditSettingCard,
)
from app.services.settings_service import SettingsService


class SettingsPage(ScrollArea):
    theme_changed = Signal(str)
    theme_color_changed = Signal(str)
    THEME_LABEL_TO_VALUE = {
        "深色": "dark",
        "浅色": "light",
        "跟随系统": "auto",
    }
    THEME_VALUE_TO_LABEL = {value: label for label, value in THEME_LABEL_TO_VALUE.items()}

    def __init__(self, config, parent=None):
        super().__init__(parent=parent)
        self.config = config
        self.settings_service = SettingsService(config)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.settingLabel = QLabel("设置", self)

        self._init_groups()
        self._init_cards()
        self._init_widget()
        self._init_layout()
        self._connect_signals()

    def _init_groups(self):
        self.ocrGroup = SettingCardGroup("识别配置", self.scrollWidget)
        self.saveGroup = SettingCardGroup("保存配置", self.scrollWidget)
        self.personalGroup = SettingCardGroup("个性化", self.scrollWidget)

    def _init_cards(self):
        self.ocrEngineCard = EditComboBoxSettingCard(
            FIF.MICROPHONE,
            "识别引擎",
            "选择当前发票识别使用的 OCR 引擎",
            ["paddleocr"],
            self.ocrGroup,
        )
        self.ocrEngineCard.setValue(self.config.get("ocr.engine", "paddleocr"))

        self.ocrLanguageCard = EditComboBoxSettingCard(
            FIF.LANGUAGE,
            "识别语言",
            "设置识别引擎处理票据时使用的语言",
            ["ch", "en"],
            self.ocrGroup,
        )
        self.ocrLanguageCard.setValue(self.config.get("ocr.lang", "ch"))

        self.useGpuCard = SwitchSettingCard(
            FIF.DEVELOPER_TOOLS,
            "启用 GPU 加速",
            "保存后在下一次 OCR 初始化时尝试使用 GPU",
            parent=self.ocrGroup,
        )
        self.useGpuCard.setChecked(self.config.get("ocr.use_gpu", False))

        self.saveDebugCard = SwitchSettingCard(
            FIF.SAVE_AS,
            "保存调试图片",
            "预处理完成后将调试图写入调试目录",
            parent=self.ocrGroup,
        )
        self.saveDebugCard.setChecked(self.config.get("ocr.save_debug_image", True))

        self.exportDirCard = LineEditSettingCard(
            FIF.FOLDER,
            "导出目录",
            "识别结果和 JSON 默认导出到这里",
            "data/export",
            self.saveGroup,
        )
        self.exportDirCard.setValue(self.config.get("storage.export_dir", "data/export"))

        self.debugDirCard = LineEditSettingCard(
            FIF.FOLDER_ADD,
            "调试目录",
            "预处理调试图默认写入的目录",
            "data/debug",
            self.saveGroup,
        )
        self.debugDirCard.setValue(self.config.get("storage.debug_dir", "data/debug"))

        self.tempDirCard = LineEditSettingCard(
            FIF.FOLDER,
            "临时目录",
            "识别流程中间文件默认使用的目录",
            "data/temp",
            self.saveGroup,
        )
        self.tempDirCard.setValue(self.config.get("storage.temp_dir", "data/temp"))

        self.logLevelCard = ComboBoxSettingCard(
            FIF.HISTORY,
            "日志级别",
            "保存后立即刷新日志输出级别",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            self.saveGroup,
        )
        self.logLevelCard.setValue(self.config.get("log.level", "INFO"))

        self.themeCard = ComboBoxSettingCard(
            FIF.BRUSH,
            "应用主题",
            "参考 VideoCaptioner 的个性化入口，支持深色、浅色和跟随系统",
            ["深色", "浅色", "跟随系统"],
            self.personalGroup,
        )
        self.themeCard.setValue(
            self.THEME_VALUE_TO_LABEL.get(self.config.get("app.theme", "dark"), "深色")
        )

        self.themeColorCard = ColorSettingCard(
            FIF.PALETTE,
            "主题色",
            "保存后立即应用到 Fluent 导航和主要强调色",
            self.config.get("app.theme_color", "#2dd36f"),
            self.personalGroup,
        )

        self.rememberWindowCard = SwitchSettingCard(
            FIF.PIN,
            "记住窗口大小",
            "关闭窗口时记录当前尺寸，下次启动恢复",
            parent=self.personalGroup,
        )
        self.rememberWindowCard.setChecked(self.config.get("app.remember_window_size", True))

        self.saveActionCard = PrimaryPushSettingCard(
            "保存配置",
            FIF.SAVE,
            "应用并写入配置文件",
            "主题、主题色、目录和日志级别会立即生效；OCR 配置在下一次识别时生效",
            self.personalGroup,
        )

    def _init_widget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 76, 0, 18)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("settingInterface")

        self.scrollWidget.setObjectName("scrollWidget")
        self.settingLabel.setObjectName("settingLabel")
        self.setStyleSheet(
            """
            SettingInterface, #scrollWidget {
                background-color: transparent;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QLabel#settingLabel {
                font: 32px 'Microsoft YaHei UI';
                background-color: transparent;
            }
            """
        )

    def _init_layout(self):
        self.settingLabel.move(36, 28)

        for card in [
            self.ocrEngineCard,
            self.ocrLanguageCard,
            self.useGpuCard,
            self.saveDebugCard,
        ]:
            self.ocrGroup.addSettingCard(card)

        for card in [
            self.exportDirCard,
            self.debugDirCard,
            self.tempDirCard,
            self.logLevelCard,
        ]:
            self.saveGroup.addSettingCard(card)

        for card in [
            self.themeCard,
            self.themeColorCard,
            self.rememberWindowCard,
            self.saveActionCard,
        ]:
            self.personalGroup.addSettingCard(card)

        self.expandLayout.setSpacing(26)
        self.expandLayout.setContentsMargins(36, 8, 36, 0)
        self.expandLayout.addWidget(self.ocrGroup)
        self.expandLayout.addWidget(self.saveGroup)
        self.expandLayout.addWidget(self.personalGroup)

    def _connect_signals(self):
        self.saveActionCard.clicked.connect(self.save_settings)

    def save_settings(self):
        theme = self.THEME_LABEL_TO_VALUE.get(self.themeCard.value(), "dark")
        theme_color = self.themeColorCard.value()

        self.config.config.setdefault("app", {})["theme"] = theme
        self.config.config.setdefault("app", {})["theme_color"] = theme_color
        self.config.config.setdefault("app", {})["language"] = "zh-CN"
        self.config.config.setdefault("app", {})["remember_window_size"] = self.rememberWindowCard.isChecked()

        self.config.config.setdefault("ocr", {})["engine"] = self.ocrEngineCard.value()
        self.config.config.setdefault("ocr", {})["lang"] = self.ocrLanguageCard.value()
        self.config.config.setdefault("ocr", {})["use_gpu"] = self.useGpuCard.isChecked()
        self.config.config.setdefault("ocr", {})["save_debug_image"] = self.saveDebugCard.isChecked()

        self.config.config.setdefault("storage", {})["export_dir"] = self.exportDirCard.value()
        self.config.config.setdefault("storage", {})["debug_dir"] = self.debugDirCard.value()
        self.config.config.setdefault("storage", {})["temp_dir"] = self.tempDirCard.value()

        self.config.config.setdefault("log", {})["level"] = self.logLevelCard.value()

        self.settings_service.save()
        self.theme_changed.emit(theme)
        self.theme_color_changed.emit(theme_color)

        InfoBar.success(
            "配置已保存",
            "主题、主题色、目录和日志级别已立即生效；新的 OCR 配置将在下一次识别时生效",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2800,
            parent=self.window(),
        )
