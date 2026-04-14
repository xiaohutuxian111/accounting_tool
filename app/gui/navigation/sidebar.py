# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:47
# @Author : stone
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QPushButton, QVBoxLayout, QLabel


class Sidebar(QFrame):
    page_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(10)

        title = QLabel("财税工作台")
        title.setObjectName("SidebarTitle")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title)

        self.buttons = []
        items = [
            ("首页工作台", 0),
            ("发票识别", 1),
            ("发票台账", 2),
            ("统计分析", 3),
            ("设置中心", 4),
            ("日志中心", 5),
        ]

        for text, idx in items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, i=idx: self._switch_page(i))
            layout.addWidget(btn)
            self.buttons.append(btn)

        self.buttons[0].setChecked(True)
        layout.addStretch()

    def _switch_page(self, index: int) -> None:
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
        self.page_changed.emit(index)