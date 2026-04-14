# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:50
# @Author : stone


from __future__ import annotations

from app.services.ocr.image_preprocess import ImagePreprocessor
from app.services.ocr.ocr_engine import LocalOCREngine
from app.services.ocr.invoice_parser import InvoiceParser
from app.services.ocr.validator import InvoiceValidator


class InvoiceOCRService:
    def __init__(self):
        # 初始化 OCR 引擎、图像预处理、发票解析器和验证器
        self.ocr_engine = LocalOCREngine()
        self.preprocessor = ImagePreprocessor()
        self.parser = InvoiceParser()

    def process(self, image_path: str) -> dict:
        """
        处理发票图片，进行 OCR 识别并返回结果
        """
        # 图像预处理（如调整大小、去噪、裁剪等）
        preprocessed_image = self.preprocessor.process(image_path)

        # 调用 OCR 引擎进行识别
        ocr_result = self.ocr_engine.recognize(preprocessed_image)

        # 解析 OCR 结果
        parsed_result = self.parser.parse(ocr_result)

        # 校验识别结果
        errors = InvoiceValidator.validate(parsed_result)

        # 将识别的发票数据和错误信息打包成字典返回
        result = parsed_result.model_dump()  # 这里假设你有一个 model_dump 方法返回字典
        result["errors"] = errors
        return result