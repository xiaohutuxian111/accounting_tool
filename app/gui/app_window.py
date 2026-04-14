# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:46
# @Author : stone


from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget
from app.gui.navigation.sidebar import Sidebar
from app.gui.pages.dashboard_page import DashboardPage
from app.gui.pages.invoice_ocr_page import InvoiceOCRPage
from app.gui.pages.ledger_page import LedgerPage
from app.gui.pages.analytics_page import AnalyticsPage
from app.gui.pages.settings_page import SettingsPage
from app.gui.pages.log_page import LogPage


class AppWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle(config.get("app.name"))
        self.resize(1360, 860)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.stack = QStackedWidget()

        # Page Initialization
        self.dashboard_page = DashboardPage()
        self.invoice_ocr_page = InvoiceOCRPage(config)
        self.ledger_page = LedgerPage(config)
        self.analytics_page = AnalyticsPage()
        self.settings_page = SettingsPage(config)
        self.log_page = LogPage(config)

        # Add pages to the stacked widget
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.invoice_ocr_page)
        self.stack.addWidget(self.ledger_page)
        self.stack.addWidget(self.analytics_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.log_page)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)

        # Signal to change pages
        self.sidebar.page_changed.connect(self.stack.setCurrentIndex)
        self.settings_page.theme_changed.connect(self.apply_theme)

    def apply_theme(self, theme_name: str) -> None:
        from app.services.theme_service import load_theme_qss
        self.setStyleSheet(load_theme_qss(theme_name))