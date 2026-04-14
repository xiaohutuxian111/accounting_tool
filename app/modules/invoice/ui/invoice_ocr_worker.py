# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from app.modules.invoice.application.invoice_ocr_service import InvoiceOCRService


class InvoiceOCRWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)
    progress = Signal(int, str)

    def __init__(self, image_paths: list[str], config):
        super().__init__()
        self.image_paths = image_paths
        self.service = InvoiceOCRService(config)

    @Slot()
    def run(self):
        try:
            results = []
            total = len(self.image_paths)
            for index, image_path in enumerate(self.image_paths, start=1):
                self.progress.emit(index, f"正在识别 {index}/{total}: {image_path}")
                results.append(self.service.process(image_path))
            self.finished.emit(results)
        except Exception as exc:
            self.failed.emit(str(exc))
