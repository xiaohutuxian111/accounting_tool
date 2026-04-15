# -*- coding: utf-8 -*-
from __future__ import annotations

from app.modules.invoice.application.dto import InvoiceOCRResult


class InvoiceValidator:
    @staticmethod
    def validate(result: InvoiceOCRResult) -> list[str]:
        errors: list[str] = []
        if not result.invoice_number:
            errors.append("\u53d1\u7968\u53f7\u7801\u7f3a\u5931")

        if result.amount_without_tax is not None and result.amount_without_tax <= 0:
            errors.append("\u4e0d\u542b\u7a0e\u91d1\u989d\u65e0\u6548")
        if result.tax_amount is not None and result.tax_amount <= 0:
            errors.append("\u7a0e\u989d\u65e0\u6548")
        if result.amount_with_tax is not None and result.amount_with_tax <= 0:
            errors.append("\u4ef7\u7a0e\u5408\u8ba1\u65e0\u6548")

        return errors
