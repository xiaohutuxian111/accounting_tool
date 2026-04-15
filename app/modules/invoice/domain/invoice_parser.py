# -*- coding: utf-8 -*-
from __future__ import annotations

import re

from app.modules.invoice.application.dto import InvoiceOCRResult


class InvoiceParser:
    INVOICE = "\u53d1\u7968"
    INVOICE_NUMBER = "\u53d1\u7968\u53f7\u7801"
    INVOICE_DATE = "\u5f00\u7968\u65e5\u671f"
    BUYER = "\u8d2d\u4e70\u65b9"
    SELLER = "\u9500\u552e\u65b9"
    AMOUNT_WITHOUT_TAX = "\u4e0d\u542b\u7a0e\u91d1\u989d"
    TAX_AMOUNT = "\u7a0e\u989d"
    AMOUNT_WITH_TAX = "\u4ef7\u7a0e\u5408\u8ba1"
    CHECK_CODE = "\u6821\u9a8c\u7801"

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
            self._apply_text_line(result, text)

        if confidences:
            result.confidence = sum(confidences) / len(confidences)

        return result

    def parse_text_lines(self, text_lines: list[str]) -> InvoiceOCRResult:
        result = InvoiceOCRResult()
        cleaned_lines = [line.strip() for line in text_lines if line and line.strip()]
        result.raw_texts.extend(cleaned_lines)

        for line in cleaned_lines:
            self._apply_text_line(result, line)

        if cleaned_lines:
            result.confidence = 1.0

        return result

    def _apply_text_line(self, result: InvoiceOCRResult, text: str) -> None:
        if not result.invoice_type and self.INVOICE in text:
            result.invoice_type = text

        if self.INVOICE_NUMBER in text:
            result.invoice_number = self._extract_value(text)
        elif self.INVOICE_DATE in text:
            result.invoice_date = self._extract_value(text)
        elif self.BUYER in text:
            result.buyer_name = self._extract_value(text)
        elif self.SELLER in text:
            result.seller_name = self._extract_value(text)
        elif self.AMOUNT_WITHOUT_TAX in text:
            result.amount_without_tax = self._extract_amount(text)
        elif text.startswith(self.TAX_AMOUNT) or self.TAX_AMOUNT in text:
            result.tax_amount = self._extract_amount(text)
        elif self.AMOUNT_WITH_TAX in text:
            result.amount_with_tax = self._extract_amount(text)
        elif self.CHECK_CODE in text:
            result.check_code = self._extract_value(text)

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
