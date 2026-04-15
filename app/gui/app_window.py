# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys

from PySide6.QtGui import QCloseEvent, QGuiApplication, QIcon
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import FluentWindow, NavigationItemPosition, Theme, setTheme, setThemeColor

from app.gui.pages.settings_page import SettingsPage
from app.modules.invoice.ui.invoice_ocr_page import InvoiceOCRPage
from app.services.settings_service import SettingsService


class AppWindow(FluentWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.settings_service = SettingsService(config)
        self.app_icon = self._load_app_icon()

        self.setWindowTitle(config.get("app.name", "会计助手"))
        self.setWindowIcon(self.app_icon)
        self._apply_initial_window_size()
        self.setMinimumWidth(700)

        self.invoiceInterface = InvoiceOCRPage(config)
        self.invoiceInterface.setWindowTitle(config.get("app.name", "会计助手"))

        self.settingsInterface = SettingsPage(config, self)
        self.settingsInterface.setWindowTitle("设置")

        self._init_navigation()
        self.apply_theme(config.get("app.theme", "dark"))
        self.apply_theme_color(config.get("app.theme_color", "#2dd36f"))

        self.settingsInterface.theme_changed.connect(self.apply_theme)
        self.settingsInterface.theme_color_changed.connect(self.apply_theme_color)

    @staticmethod
    def _load_app_icon() -> QIcon:
        if getattr(sys, "frozen", False):
            base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        else:
            base_path = Path(__file__).resolve().parents[1]
        icon_path = base_path / "assets" / "app_icon.png"
        if icon_path.exists():
            return QIcon(str(icon_path))
        return FIF.DOCUMENT.icon()

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

    def _apply_initial_window_size(self) -> None:
        requested_width = int(self.config.get("app.window_width", 1050) or 1050)
        requested_height = int(self.config.get("app.window_height", 800) or 800)

        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(requested_width, requested_height)
            return

        available = screen.availableGeometry()
        safe_width = max(900, min(requested_width, available.width() - 80))
        safe_height = max(700, min(requested_height, available.height() - 80))
        self.resize(safe_width, safe_height)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.config.get("app.remember_window_size", True):
            self.config.config.setdefault("app", {})["window_width"] = self.width()
            self.config.config.setdefault("app", {})["window_height"] = self.height()
            self.settings_service.save()

        super().closeEvent(event)
