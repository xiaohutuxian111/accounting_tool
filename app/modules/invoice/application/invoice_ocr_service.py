# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from app.core.config import AppConfig
from app.modules.invoice.application.dto import InvoiceOCRResult
from app.modules.invoice.domain.invoice_parser import InvoiceParser
from app.modules.invoice.domain.validator import InvoiceValidator
from app.modules.invoice.infrastructure.image_preprocess import ImagePreprocessor
from app.modules.invoice.infrastructure.ocr_engine import LocalOCREngine
from app.modules.invoice.infrastructure.pdf_invoice_renderer import PDFInvoiceRenderer
from app.modules.invoice.infrastructure.standard_pdf_invoice_extractor import StandardPDFInvoiceExtractor


class InvoiceOCRService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.ocr_engine: LocalOCREngine | None = None
        self.preprocessor = ImagePreprocessor(
            save_debug_image=config.get("ocr.save_debug_image", True),
            debug_dir=config.get("storage.debug_dir", "data/debug"),
            temp_dir=config.get("storage.temp_dir", "data/temp"),
        )
        self.pdf_renderer = PDFInvoiceRenderer(
            temp_dir=config.get("storage.temp_dir", "data/temp"),
        )
        self.pdf_extractor = StandardPDFInvoiceExtractor()
        self.parser = InvoiceParser()

    def process(self, image_path: str) -> InvoiceOCRResult:
        if Path(image_path).suffix.lower() == ".pdf":
            result = self._process_pdf(image_path)
        else:
            result = self._process_image(image_path)

        result.source_file = image_path
        result.errors = InvoiceValidator.validate(result)
        return result

    def _process_image(self, image_path: str) -> InvoiceOCRResult:
        if self.ocr_engine is None:
            self.ocr_engine = LocalOCREngine(
                lang=self.config.get("ocr.lang", "ch"),
                use_gpu=self.config.get("ocr.use_gpu", False),
            )
        preprocessed_image = self.preprocessor.process(image_path)
        ocr_result = self.ocr_engine.recognize(preprocessed_image)
        return self.parser.parse(ocr_result)

    def _process_pdf(self, pdf_path: str) -> InvoiceOCRResult:
        result = self.pdf_extractor.extract(pdf_path)
        if result.invoice_number or result.buyer_name or result.seller_name:
            return result

        text_lines = self.pdf_renderer.extract_text_lines(pdf_path)
        return self.parser.parse_text_lines(text_lines)

    def process_batch(self, image_paths: list[str]) -> list[InvoiceOCRResult]:
        return [self.process(path) for path in image_paths]
