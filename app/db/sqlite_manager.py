# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:33
# @Author : stone


from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.core.config import AppConfig


class SQLiteManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.db_path = Path(config.get("storage.db_path", "data/db/accounting.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_type TEXT,
                    invoice_code TEXT,
                    invoice_number TEXT,
                    invoice_date TEXT,
                    buyer_name TEXT,
                    seller_name TEXT,
                    amount_without_tax REAL,
                    tax_amount REAL,
                    amount_with_tax REAL,
                    check_code TEXT,
                    confidence REAL,
                    verify_status TEXT,
                    source_file TEXT,
                    raw_text TEXT,
                    created_at TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_invoices_code_number
                ON invoices(invoice_code, invoice_number)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_invoices_date
                ON invoices(invoice_date)
                """
            )

            conn.commit()

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
