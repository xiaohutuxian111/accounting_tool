# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:36
# @Author : stone



from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
)

from app.gui.workers.invoice_ocr_worker import InvoiceOCRWorker
from app.services.invoice_ledger_service import InvoiceLedgerService


class InvoiceOCRPage(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.current_image_path: str | None = None
        self.thread: QThread | None = None
        self.worker: InvoiceOCRWorker | None = None
        self.last_result: dict | None = None
        self.ledger_service = InvoiceLedgerService(config)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("发票识别")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self.btn_open = QPushButton("选择图片")
        self.btn_run = QPushButton("开始识别")
        self.btn_save_ledger = QPushButton("保存到台账")
        self.btn_export = QPushButton("导出 JSON")

        self.btn_run.setEnabled(False)
        self.btn_save_ledger.setEnabled(False)
        self.btn_export.setEnabled(False)

        toolbar.addWidget(self.btn_open)
        toolbar.addWidget(self.btn_run)
        toolbar.addWidget(self.btn_save_ledger)
        toolbar.addWidget(self.btn_export)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        splitter = QSplitter()

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.image_label = QLabel("请先选择发票图片")
        self.image_label.setObjectName("PreviewPanel")
        self.image_label.setMinimumWidth(440)
        self.image_label.setMinimumHeight(620)
        self.image_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.image_label)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.result_table = QTableWidget(0, 2)
        self.result_table.setHorizontalHeaderLabels(["字段", "值"])

        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setPlaceholderText("OCR 原始文本")

        right_layout.addWidget(self.result_table, 2)
        right_layout.addWidget(self.raw_text, 1)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([520, 700])

        layout.addWidget(splitter)

        self.btn_open.clicked.connect(self.open_image)
        self.btn_run.clicked.connect(self.run_ocr)
        self.btn_export.clicked.connect(self.export_json)
        self.btn_save_ledger.clicked.connect(self.save_to_ledger)

    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择发票图片",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not file_path:
            return

        self.current_image_path = file_path
        self.btn_run.setEnabled(True)
        self.btn_save_ledger.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.last_result = None
        self.result_table.setRowCount(0)
        self.raw_text.clear()

        pixmap = QPixmap(file_path)
        scaled = pixmap.scaled(480, 620, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)

    def run_ocr(self):
        if not self.current_image_path:
            QMessageBox.warning(self, "提示", "请先选择图片")
            return

        self.thread = QThread()
        self.worker = InvoiceOCRWorker(self.current_image_path)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)

        self.btn_run.setEnabled(False)
        self.thread.start()

    def on_finished(self, result: dict):
        self.last_result = result
        self.btn_run.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.btn_save_ledger.setEnabled(True)

        pairs = [
            ("发票类型", result.get("invoice_type")),
            ("发票代码", result.get("invoice_code")),
            ("发票号码", result.get("invoice_number")),
            ("开票日期", result.get("invoice_date")),
            ("购买方", result.get("buyer_name")),
            ("销售方", result.get("seller_name")),
            ("不含税金额", result.get("amount_without_tax")),
            ("税额", result.get("tax_amount")),
            ("价税合计", result.get("amount_with_tax")),
            ("校验码", result.get("check_code")),
            ("置信度", result.get("confidence")),
            ("错误信息", "；".join(result.get("errors", [])) if result.get("errors") else ""),
        ]

        self.result_table.setRowCount(len(pairs))
        for row, (k, v) in enumerate(pairs):
            self.result_table.setItem(row, 0, QTableWidgetItem(str(k)))
            self.result_table.setItem(row, 1, QTableWidgetItem("" if v is None else str(v)))

        self.raw_text.setPlainText("\n".join(result.get("raw_texts", [])))

    def on_failed(self, message: str):
        self.btn_run.setEnabled(True)
        QMessageBox.critical(self, "识别失败", message)

    def export_json(self):
        if not self.last_result or not self.current_image_path:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 JSON",
            str(Path(self.current_image_path).with_suffix(".json")),
            "JSON Files (*.json)",
        )
        if not save_path:
            return

        Path(save_path).write_text(
            json.dumps(self.last_result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        QMessageBox.information(self, "成功", f"JSON 已导出到：\n{save_path}")

    def save_to_ledger(self):
        if not self.last_result or not self.current_image_path:
            QMessageBox.warning(self, "提示", "请先完成识别")
            return

        ok, message, row_id = self.ledger_service.save_invoice_result(
            self.last_result,
            self.current_image_path,
        )

        if ok:
            QMessageBox.information(self, "保存成功", f"{message}\n记录 ID: {row_id}")
        else:
            QMessageBox.warning(self, "保存提示", message)