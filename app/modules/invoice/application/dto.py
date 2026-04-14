# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class InvoiceOCRResult:
    source_file: str | None = None
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
    raw_texts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def display_rows(self) -> list[tuple[str, str]]:
        return [
            ("来源文件", self.source_file or ""),
            ("发票类型", self.invoice_type or ""),
            ("发票代码", self.invoice_code or ""),
            ("发票号码", self.invoice_number or ""),
            ("开票日期", self.invoice_date or ""),
            ("购买方", self.buyer_name or ""),
            ("销售方", self.seller_name or ""),
            ("不含税金额", "" if self.amount_without_tax is None else str(self.amount_without_tax)),
            ("税额", "" if self.tax_amount is None else str(self.tax_amount)),
            ("价税合计", "" if self.amount_with_tax is None else str(self.amount_with_tax)),
            ("校验码", self.check_code or ""),
            ("置信度", "" if self.confidence is None else f"{self.confidence:.4f}"),
            ("错误信息", "；".join(self.errors)),
        ]
