# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InvoiceRecord:
    id: int | None = None
    invoice_type: str | None = None
    invoice_code: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    buyer_name: str | None = None
    seller_name: str | None = None
    amount_without_tax: float | None = None
    tax_amount: float | None = None
    amount_with_tax: float | None = None
    check_code: str | None = None
    confidence: float | None = None
    verify_status: str | None = None
    source_file: str | None = None
    raw_text: str | None = None
    created_at: str | None = None
