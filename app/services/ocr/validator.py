# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:52
# @Author : stone


from __future__ import annotations


class InvoiceValidator:
    @staticmethod
    def validate(invoice_data: dict) -> list:
        """
        校验发票数据是否合法，返回错误列表。
        """
        errors = []

        # 校验发票代码和发票号码是否存在
        if not invoice_data.get("invoice_code"):
            errors.append("发票代码缺失")
        if not invoice_data.get("invoice_number"):
            errors.append("发票号码缺失")

        # 校验金额是否有效
        if invoice_data.get("amount_without_tax") <= 0:
            errors.append("不含税金额无效")
        if invoice_data.get("tax_amount") <= 0:
            errors.append("税额无效")
        if invoice_data.get("amount_with_tax") <= 0:
            errors.append("价税合计无效")

        return errors