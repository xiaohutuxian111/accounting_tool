# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:35
# @Author : stone


from __future__ import annotations

from app.core.config import AppConfig
from app.db.repositories.invoice_repo import InvoiceRepository
from app.db.sqlite_manager import SQLiteManager
from app.models.invoice import InvoiceRecord


class InvoiceLedgerService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.db = SQLiteManager(config)
        self.db.init_db()
        self.repo = InvoiceRepository(self.db)

    def save_invoice_result(self, result: dict, source_file: str) -> tuple[bool, str, int | None]:
        invoice_code = result.get("invoice_code")
        invoice_number = result.get("invoice_number")

        if self.repo.exists_by_code_number(invoice_code, invoice_number):
            return False, "该发票已存在，未重复入库", None

        verify_status = "已校验" if not result.get("errors") else "待复核"

        record = InvoiceRecord(
            invoice_type=result.get("invoice_type"),
            invoice_code=invoice_code,
            invoice_number=invoice_number,
            invoice_date=result.get("invoice_date"),
            buyer_name=result.get("buyer_name"),
            seller_name=result.get("seller_name"),
            amount_without_tax=self._to_float(result.get("amount_without_tax")),
            tax_amount=self._to_float(result.get("tax_amount")),
            amount_with_tax=self._to_float(result.get("amount_with_tax")),
            check_code=result.get("check_code"),
            confidence=self._to_float(result.get("confidence")),
            verify_status=verify_status,
            source_file=source_file,
            raw_text="\n".join(result.get("raw_texts", [])),
        )

        row_id = self.repo.insert(record)
        return True, "保存成功", row_id

    def list_all(self) -> list[InvoiceRecord]:
        return self.repo.list_all()

    def search(
        self,
        keyword: str = "",
        verify_status: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> list[InvoiceRecord]:
        return self.repo.search(keyword, verify_status, start_date, end_date)

    def delete_by_id(self, invoice_id: int) -> None:
        self.repo.delete_by_id(invoice_id)

    @staticmethod
    def _to_float(value):
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except Exception:
            return None