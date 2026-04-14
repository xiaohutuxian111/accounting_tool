# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:40
# @Author : stone


from __future__ import annotations

from PySide6.QtWidgets import QLabel, QGridLayout, QVBoxLayout, QWidget
from app.gui.widgets.stat_card import StatCard


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        title = QLabel("首页工作台")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(16)

        # 这里的数字可以动态绑定为数据库里的统计数据
        grid.addWidget(StatCard("今日识别", "18"), 0, 0)
        grid.addWidget(StatCard("本月发票金额", "¥ 12,850.00"), 0, 1)
        grid.addWidget(StatCard("本月税额", "¥ 1,245.00"), 0, 2)
        grid.addWidget(StatCard("待校验票据", "6"), 0, 3)

        layout.addLayout(grid)
        layout.addStretch()