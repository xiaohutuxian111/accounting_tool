# -*- coding: utf-8 -*-
from __future__ import annotations

from app.core.config import AppConfig
from app.modules.invoice.application.dto import InvoiceOCRResult
from app.modules.invoice.domain.invoice_parser import InvoiceParser
from app.modules.invoice.domain.validator import InvoiceValidator
from app.modules.invoice.infrastructure.image_preprocess import ImagePreprocessor
from app.modules.invoice.infrastructure.ocr_engine import LocalOCREngine


class InvoiceOCRService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.ocr_engine = LocalOCREngine(
            lang=config.get("ocr.lang", "ch"),
            use_gpu=config.get("ocr.use_gpu", False),
        )
        self.preprocessor = ImagePreprocessor(
            save_debug_image=config.get("ocr.save_debug_image", True),
            debug_dir=config.get("storage.debug_dir", "data/debug"),
        )
        self.parser = InvoiceParser()

    def process(self, image_path: str) -> InvoiceOCRResult:
        preprocessed_image = self.preprocessor.process(image_path)
        ocr_result = self.ocr_engine.recognize(preprocessed_image)
        result = self.parser.parse(ocr_result)
        result.source_file = image_path
        result.errors = InvoiceValidator.validate(result)
        return result

    def process_batch(self, image_paths: list[str]) -> list[InvoiceOCRResult]:
        return [self.process(path) for path in image_paths]
