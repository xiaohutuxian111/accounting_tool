# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


class ImagePreprocessor:
    def __init__(self, save_debug_image: bool = False, debug_dir: str = "data/debug"):
        self.save_debug_image = save_debug_image
        self.debug_dir = Path(debug_dir)

    def process(self, image_path: str) -> np.ndarray:
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"无法读取图片: {image_path}")

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        denoised_image = cv2.medianBlur(gray_image, 3)
        _, binary_image = cv2.threshold(
            denoised_image,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )

        if self.save_debug_image:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = self.debug_dir / f"{Path(image_path).stem}_preprocessed.png"
            cv2.imwrite(str(debug_path), binary_image)

        return binary_image
