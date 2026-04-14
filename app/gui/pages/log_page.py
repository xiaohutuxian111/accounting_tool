# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:59
# @Author : stone


from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QMessageBox,
)


class LogPage(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.log_file = Path(config.get("log.dir", "logs")) / "app.log"

        self._build_ui()
        self.load_logs()

        # 自动刷新（每3秒）
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_logs)
        self.timer.start(3000)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 标题
        title = QLabel("日志中心")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # 工具栏
        toolbar = QHBoxLayout()

        self.btn_refresh = QPushButton("刷新")
        self.btn_clear = QPushButton("清空日志")

        toolbar.addWidget(self.btn_refresh)
        toolbar.addWidget(self.btn_clear)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # 日志显示区
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlaceholderText("暂无日志")
        layout.addWidget(self.text)

        # 绑定事件
        self.btn_refresh.clicked.connect(self.load_logs)
        self.btn_clear.clicked.connect(self.clear_logs)

    def load_logs(self):
        """加载日志文件"""
        try:
            if self.log_file.exists():
                content = self.log_file.read_text(encoding="utf-8", errors="ignore")
                self.text.setPlainText(content)

                # 滚动到底部（最新日志）
                self.text.verticalScrollBar().setValue(
                    self.text.verticalScrollBar().maximum()
                )
            else:
                self.text.setPlainText("暂无日志文件")
        except Exception as e:
            self.text.setPlainText(f"读取日志失败: {e}")

    def clear_logs(self):
        """清空日志"""
        if not self.log_file.exists():
            return

        confirm = QMessageBox.question(
            self,
            "确认",
            "确定清空日志吗？",
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            self.log_file.write_text("", encoding="utf-8")
            self.text.clear()
            QMessageBox.information(self, "成功", "日志已清空")
        except Exception as e:
            QMessageBox.critical(self, "失败", str(e))