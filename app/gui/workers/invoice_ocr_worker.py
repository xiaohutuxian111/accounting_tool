# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:49
# @Author : stone


from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot
from app.services.invoice_ocr_service import InvoiceOCRService


class InvoiceOCRWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path
        self.service = InvoiceOCRService()

    @Slot()
    def run(self):
        try:
            result = self.service.process(self.image_path)
            self.finished.emit(result)
        except Exception as e:
            self.failed.emit(str(e))