# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class InvoiceOCRResult:
    source_file: str | None = None
    invoice_type: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    buyer_name: str | None = None
    buyer_tax_id: str | None = None
    seller_name: str | None = None
    seller_tax_id: str | None = None
    item_name: str | None = None
    unit: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    tax_rate: str | None = None
    amount_without_tax: float | None = None
    tax_amount: float | None = None
    amount_with_tax: float | None = None
    amount_with_tax_cn: str | None = None
    issuer: str | None = None
    remark: str | None = None
    check_code: str | None = None
    confidence: float | None = None
    raw_texts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def display_rows(self) -> list[tuple[str, str]]:
        return [
            ("\u6765\u6e90\u6587\u4ef6", self.source_file or ""),
            ("\u53d1\u7968\u7c7b\u578b", self.invoice_type or ""),
            ("\u53d1\u7968\u53f7\u7801", self.invoice_number or ""),
            ("\u5f00\u7968\u65e5\u671f", self.invoice_date or ""),
            ("\u8d2d\u4e70\u65b9", self.buyer_name or ""),
            ("\u8d2d\u4e70\u65b9\u7a0e\u53f7", self.buyer_tax_id or ""),
            ("\u9500\u552e\u65b9", self.seller_name or ""),
            ("\u9500\u552e\u65b9\u7a0e\u53f7", self.seller_tax_id or ""),
            ("\u9879\u76ee\u540d\u79f0", self.item_name or ""),
            ("\u5355\u4f4d", self.unit or ""),
            ("\u6570\u91cf", "" if self.quantity is None else str(self.quantity)),
            ("\u5355\u4ef7", "" if self.unit_price is None else str(self.unit_price)),
            ("\u7a0e\u7387/\u5f81\u6536\u7387", self.tax_rate or ""),
            ("\u4e0d\u542b\u7a0e\u91d1\u989d", "" if self.amount_without_tax is None else str(self.amount_without_tax)),
            ("\u7a0e\u989d", "" if self.tax_amount is None else str(self.tax_amount)),
            ("\u4ef7\u7a0e\u5408\u8ba1", "" if self.amount_with_tax is None else str(self.amount_with_tax)),
            ("\u4ef7\u7a0e\u5408\u8ba1\u5927\u5199", self.amount_with_tax_cn or ""),
            ("\u5f00\u7968\u4eba", self.issuer or ""),
            ("\u5907\u6ce8", self.remark or ""),
            ("\u6821\u9a8c\u7801", self.check_code or ""),
            ("\u7f6e\u4fe1\u5ea6", "" if self.confidence is None else f"{self.confidence:.4f}"),
            ("\u9519\u8bef\u4fe1\u606f", "\uff1b".join(self.errors)),
        ]
