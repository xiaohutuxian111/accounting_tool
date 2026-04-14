# -*- coding: utf-8 -*-
from __future__ import annotations

from paddleocr import PaddleOCR


class LocalOCREngine:
    def __init__(self, lang: str = "ch", use_gpu: bool = False):
        device = "gpu:0" if use_gpu else "cpu"
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, device=device)

    def recognize(self, image) -> list:
        return self.ocr.ocr(image, cls=True)
