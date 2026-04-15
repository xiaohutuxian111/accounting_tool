# -*- coding: utf-8 -*-
from __future__ import annotations

from app.db.sqlite_manager import SQLiteManager
from app.modules.invoice.domain.entities import InvoiceRecord


class InvoiceRepository:
    def __init__(self, db: SQLiteManager):
        self.db = db

    def insert(self, record: InvoiceRecord) -> int:
        sql = """
        INSERT INTO invoices (
            invoice_type,
            invoice_code,
            invoice_number,
            invoice_date,
            buyer_name,
            seller_name,
            amount_without_tax,
            tax_amount,
            amount_with_tax,
            check_code,
            confidence,
            verify_status,
            source_file,
            raw_text,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record.invoice_type,
            record.invoice_code,
            record.invoice_number,
            record.invoice_date,
            record.buyer_name,
            record.seller_name,
            record.amount_without_tax,
            record.tax_amount,
            record.amount_with_tax,
            record.check_code,
            record.confidence,
            record.verify_status,
            record.source_file,
            record.raw_text,
            record.created_at,
        )
        return self.db.execute(sql, params)

    def exists_by_code_number(self, invoice_code: str | None, invoice_number: str | None) -> bool:
        if not invoice_number:
            return False

        if invoice_code:
            row = self.db.fetch_one(
                "SELECT id FROM invoices WHERE invoice_code = ? AND invoice_number = ? LIMIT 1",
                (invoice_code, invoice_number),
            )
        else:
            row = self.db.fetch_one(
                "SELECT id FROM invoices WHERE invoice_number = ? LIMIT 1",
                (invoice_number,),
            )
        return row is not None

    def list_all(self) -> list[InvoiceRecord]:
        rows = self.db.fetch_all("SELECT * FROM invoices ORDER BY created_at DESC")
        return [self._row_to_entity(row) for row in rows]

    def search(self, keyword: str, verify_status: str, start_date: str, end_date: str) -> list[InvoiceRecord]:
        sql = """
        SELECT * FROM invoices
        WHERE invoice_code LIKE ? OR invoice_number LIKE ?
        """
        params = [f"%{keyword}%", f"%{keyword}%"]
        if verify_status:
            sql += " AND verify_status = ?"
            params.append(verify_status)
        if start_date:
            sql += " AND invoice_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND invoice_date <= ?"
            params.append(end_date)

        rows = self.db.fetch_all(sql, tuple(params))
        return [self._row_to_entity(row) for row in rows]

    def get_by_id(self, invoice_id: int) -> InvoiceRecord | None:
        row = self.db.fetch_one("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        if not row:
            return None
        return self._row_to_entity(row)

    def delete_by_id(self, invoice_id: int) -> None:
        self.db.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))

    @staticmethod
    def _row_to_entity(row) -> InvoiceRecord:
        return InvoiceRecord(
            id=row["id"],
            invoice_type=row["invoice_type"],
            invoice_code=row["invoice_code"],
            invoice_number=row["invoice_number"],
            invoice_date=row["invoice_date"],
            buyer_name=row["buyer_name"],
            seller_name=row["seller_name"],
            amount_without_tax=row["amount_without_tax"],
            tax_amount=row["tax_amount"],
            amount_with_tax=row["amount_with_tax"],
            check_code=row["check_code"],
            confidence=row["confidence"],
            verify_status=row["verify_status"],
            source_file=row["source_file"],
            raw_text=row["raw_text"],
            created_at=row["created_at"],
        )
