# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:57
# @Author : stone


from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class InvoiceRecord:
    id: Optional[int] = None
    invoice_type: Optional[str] = None
    invoice_code: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    buyer_name: Optional[str] = None
    seller_name: Optional[str] = None
    amount_without_tax: Optional[float] = None
    tax_amount: Optional[float] = None
    amount_with_tax: Optional[float] = None
    check_code: Optional[str] = None
    confidence: Optional[float] = None
    verify_status: Optional[str] = None
    source_file: Optional[str] = None
    raw_text: Optional[str] = None
    created_at: Optional[str] = None