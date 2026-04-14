# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:52
# @Author : stone



from __future__ import annotations

import re


class InvoiceParser:
    def __init__(self):
        pass

    def parse(self, ocr_result: list) -> dict:
        """
        解析 OCR 结果，提取发票字段信息。
        """
        invoice_data = {}

        for line in ocr_result[0]:
            text = line[1][0]
            if "发票代码" in text:
                invoice_data["invoice_code"] = self._extract_value(text)
            elif "发票号码" in text:
                invoice_data["invoice_number"] = self._extract_value(text)
            elif "开票日期" in text:
                invoice_data["invoice_date"] = self._extract_value(text)
            elif "购买方" in text:
                invoice_data["buyer_name"] = self._extract_value(text)
            elif "销售方" in text:
                invoice_data["seller_name"] = self._extract_value(text)
            elif "不含税金额" in text:
                invoice_data["amount_without_tax"] = self._extract_amount(text)
            elif "税额" in text:
                invoice_data["tax_amount"] = self._extract_amount(text)
            elif "价税合计" in text:
                invoice_data["amount_with_tax"] = self._extract_amount(text)
            elif "校验码" in text:
                invoice_data["check_code"] = self._extract_value(text)

        return invoice_data

    def _extract_value(self, text: str) -> str:
        """
        从文本中提取值（例如：`发票代码：123456` 中提取 `123456`）。
        """
        return text.split("：")[-1].strip()

    def _extract_amount(self, text: str) -> float:
        """
        从文本中提取金额（例如：`不含税金额：¥1000.00` 中提取 `1000.00`）。
        """
        match = re.search(r"[\d,]+(?:\.\d{1,2})?", text)
        return float(match.group(0).replace(",", "")) if match else 0.0