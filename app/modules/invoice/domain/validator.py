# -*- coding: utf-8 -*-
from __future__ import annotations

from app.modules.invoice.application.dto import InvoiceOCRResult


class InvoiceValidator:
    @staticmethod
    def validate(result: InvoiceOCRResult) -> list[str]:
        errors: list[str] = []

        if not result.invoice_code:
            errors.append("发票代码缺失")
        if not result.invoice_number:
            errors.append("发票号码缺失")

        if result.amount_without_tax is not None and result.amount_without_tax <= 0:
            errors.append("不含税金额无效")
        if result.tax_amount is not None and result.tax_amount <= 0:
            errors.append("税额无效")
        if result.amount_with_tax is not None and result.amount_with_tax <= 0:
            errors.append("价税合计无效")

        return errors
