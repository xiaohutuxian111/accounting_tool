# -*- coding: utf-8 -*-
from __future__ import annotations

from app.core.config import AppConfig
from app.db.sqlite_manager import SQLiteManager
from app.modules.invoice.application.dto import InvoiceOCRResult
from app.modules.invoice.domain.entities import InvoiceRecord
from app.modules.invoice.infrastructure.invoice_repo import InvoiceRepository


class InvoiceLedgerService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.db = SQLiteManager(config)
        self.db.init_db()
        self.repo = InvoiceRepository(self.db)

    def save_invoice_result(self, result: InvoiceOCRResult, source_file: str) -> tuple[bool, str, int | None]:
        if self.repo.exists_by_code_number(result.invoice_code, result.invoice_number):
            return False, "该发票已存在，未重复入库", None

        verify_status = "已校验" if not result.errors else "待复核"
        record = InvoiceRecord(
            invoice_type=result.invoice_type,
            invoice_code=result.invoice_code,
            invoice_number=result.invoice_number,
            invoice_date=result.invoice_date,
            buyer_name=result.buyer_name,
            seller_name=result.seller_name,
            amount_without_tax=result.amount_without_tax,
            tax_amount=result.tax_amount,
            amount_with_tax=result.amount_with_tax,
            check_code=result.check_code,
            confidence=result.confidence,
            verify_status=verify_status,
            source_file=source_file,
            raw_text="\n".join(result.raw_texts),
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
