# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:58
# @Author : stone


from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("统计分析")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # 这里你可以添加你需要展示的数据
        # 比如统计图表、发票数据的分析图表等
        stats_label = QLabel("这里显示统计数据或分析图表")
        stats_label.setObjectName("StatsLabel")
        layout.addWidget(stats_label)

        layout.addStretch()