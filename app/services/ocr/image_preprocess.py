# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:51
# @Author : stone


from __future__ import annotations

import cv2
import numpy as np


class ImagePreprocessor:
    def __init__(self):
        pass

    def process(self, image_path: str) -> np.ndarray:
        """
        处理图像，包括灰度化、去噪、调整大小等。
        """
        # 读取图像
        image = cv2.imread(image_path)

        # 转为灰度图
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 去噪声：使用中值滤波去除噪点
        denoised_image = cv2.medianBlur(gray_image, 3)

        # 二值化图像：以 Otsu 方法自动选择阈值
        _, binary_image = cv2.threshold(denoised_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary_image