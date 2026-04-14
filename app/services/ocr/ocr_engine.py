# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:52
# @Author : stone


from __future__ import annotations

from paddleocr import PaddleOCR


class LocalOCREngine:
    def __init__(self, lang="ch"):
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang)

    def recognize(self, image: str) -> list:
        """
        使用 OCR 引擎识别图像中的文本。
        """
        result = self.ocr.ocr(image, cls=True)

        # 只保留文本识别的结果
        return result