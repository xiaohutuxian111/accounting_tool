# -*- coding: utf-8 -*-
from __future__ import annotations

import re

from app.modules.invoice.application.dto import InvoiceOCRResult


class InvoiceParser:
    def parse(self, ocr_result: list) -> InvoiceOCRResult:
        result = InvoiceOCRResult()
        if not ocr_result or not ocr_result[0]:
            return result

        confidences: list[float] = []
        for line in ocr_result[0]:
            text = line[1][0].strip()
            confidence = float(line[1][1]) if len(line[1]) > 1 else None
            result.raw_texts.append(text)
            if confidence is not None:
                confidences.append(confidence)

            if not result.invoice_type and "发票" in text:
                result.invoice_type = text

            if "发票代码" in text:
                result.invoice_code = self._extract_value(text)
            elif "发票号码" in text:
                result.invoice_number = self._extract_value(text)
            elif "开票日期" in text:
                result.invoice_date = self._extract_value(text)
            elif "购买方" in text:
                result.buyer_name = self._extract_value(text)
            elif "销售方" in text:
                result.seller_name = self._extract_value(text)
            elif "不含税金额" in text:
                result.amount_without_tax = self._extract_amount(text)
            elif text.startswith("税额") or "税额" in text:
                result.tax_amount = self._extract_amount(text)
            elif "价税合计" in text:
                result.amount_with_tax = self._extract_amount(text)
            elif "校验码" in text:
                result.check_code = self._extract_value(text)

        if confidences:
            result.confidence = sum(confidences) / len(confidences)

        return result

    @staticmethod
    def _extract_value(text: str) -> str:
        parts = re.split(r"[:：]", text, maxsplit=1)
        return parts[-1].strip() if parts else text.strip()

    @staticmethod
    def _extract_amount(text: str) -> float | None:
        match = re.search(r"[\d,]+(?:\.\d{1,2})?", text)
        if not match:
            return None
        return float(match.group(0).replace(",", ""))
