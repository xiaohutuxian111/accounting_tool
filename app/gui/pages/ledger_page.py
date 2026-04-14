# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:37
# @Author : stone



from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from app.services.invoice_ledger_service import InvoiceLedgerService


class LedgerPage(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.ledger_service = InvoiceLedgerService(config)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("发票台账")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        toolbar = QHBoxLayout()

        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("搜索发票代码 / 发票号码 / 购买方 / 销售方")

        self.status_combo = QComboBox()
        self.status_combo.addItems(["全部状态", "已校验", "待复核"])

        self.btn_search = QPushButton("查询")
        self.btn_refresh = QPushButton("刷新")
        self.btn_delete = QPushButton("删除选中")

        toolbar.addWidget(self.keyword_input, 1)
        toolbar.addWidget(self.status_combo)
        toolbar.addWidget(self.btn_search)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addWidget(self.btn_delete)

        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 13)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "发票类型",
            "发票代码",
            "发票号码",
            "开票日期",
            "购买方",
            "销售方",
            "不含税金额",
            "税额",
            "价税合计",
            "校验状态",
            "置信度",
            "创建时间",
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.table)

        self.btn_search.clicked.connect(self.search_data)
        self.btn_refresh.clicked.connect(self.load_data)
        self.btn_delete.clicked.connect(self.delete_selected)

    def load_data(self):
        rows = self.ledger_service.list_all()
        self._fill_table(rows)

    def search_data(self):
        keyword = self.keyword_input.text().strip()
        status_text = self.status_combo.currentText()
        verify_status = "" if status_text == "全部状态" else status_text

        rows = self.ledger_service.search(
            keyword=keyword,
            verify_status=verify_status,
        )
        self._fill_table(rows)

    def delete_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "提示", "请先选择要删除的记录")
            return

        row_index = selected[0].row()
        invoice_id_item = self.table.item(row_index, 0)
        if not invoice_id_item:
            return

        invoice_id = int(invoice_id_item.text())

        confirm = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除记录 ID={invoice_id} 吗？",
        )
        if confirm != QMessageBox.Yes:
            return

        self.ledger_service.delete_by_id(invoice_id)
        QMessageBox.information(self, "成功", "删除成功")
        self.load_data()

    def _fill_table(self, rows):
        self.table.setRowCount(len(rows))

        for row_idx, item in enumerate(rows):
            values = [
                item.id,
                item.invoice_type,
                item.invoice_code,
                item.invoice_number,
                item.invoice_date,
                item.buyer_name,
                item.seller_name,
                item.amount_without_tax,
                item.tax_amount,
                item.amount_with_tax,
                item.verify_status,
                item.confidence,
                item.created_at,
            ]

            for col_idx, value in enumerate(values):
                self.table.setItem(
                    row_idx,
                    col_idx,
                    QTableWidgetItem("" if value is None else str(value)),
                )