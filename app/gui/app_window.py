# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtGui import QCloseEvent
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import FluentWindow, NavigationItemPosition, Theme, setTheme, setThemeColor

from app.modules.invoice.ui.invoice_ocr_page import InvoiceOCRPage
from app.gui.pages.settings_page import SettingsPage
from app.services.settings_service import SettingsService


class AppWindow(FluentWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.settings_service = SettingsService(config)

        self.setWindowTitle(config.get("app.name", "发票识别助手"))
        self.resize(
            config.get("app.window_width", 1050),
            config.get("app.window_height", 800),
        )
        self.setMinimumWidth(700)

        self.invoiceInterface = InvoiceOCRPage(config)
        self.invoiceInterface.setWindowTitle("发票识别")

        self.settingsInterface = SettingsPage(config, self)
        self.settingsInterface.setWindowTitle("设置")

        self._init_navigation()
        self.apply_theme(config.get("app.theme", "dark"))
        self.apply_theme_color(config.get("app.theme_color", "#2dd36f"))

        self.settingsInterface.theme_changed.connect(self.apply_theme)
        self.settingsInterface.theme_color_changed.connect(self.apply_theme_color)

    def _init_navigation(self):
        self.addSubInterface(self.invoiceInterface, FIF.DOCUMENT, "发票识别")
        self.navigationInterface.addSeparator()
        self.addSubInterface(
            self.settingsInterface,
            FIF.SETTING,
            "设置",
            NavigationItemPosition.BOTTOM,
        )
        self.switchTo(self.invoiceInterface)

    def apply_theme(self, theme_name: str) -> None:
        theme_map = {
            "dark": Theme.DARK,
            "light": Theme.LIGHT,
            "auto": Theme.AUTO,
        }
        setTheme(theme_map.get(theme_name, Theme.DARK))

    def apply_theme_color(self, color: str) -> None:
        setThemeColor(color or "#2dd36f")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.config.get("app.remember_window_size", True):
            self.config.config.setdefault("app", {})["window_width"] = self.width()
            self.config.config.setdefault("app", {})["window_height"] = self.height()
            self.settings_service.save()

        super().closeEvent(event)
