# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:40
# @Author : stone


from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):
    def __init__(self, title: str, value: str):
        super().__init__()
        self.setObjectName("StatCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("StatCardTitle")

        value_label = QLabel(value)
        value_label.setObjectName("StatCardValue")

        layout.addWidget(title_label)
        layout.addWidget(value_label)