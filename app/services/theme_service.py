# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:53
# @Author : stone





from __future__ import annotations

from pathlib import Path


def load_theme_qss(theme_name: str) -> str:
    """
    基于当前文件绝对路径加载主题文件，避免受运行目录影响。
    """
    # 当前文件: app/services/theme_service.py
    # 向上到 app/ 目录
    app_dir = Path(__file__).resolve().parent.parent
    qss_path = app_dir / "resources" / "qss" / f"{theme_name}.qss"

    print(f"[theme_service] loading theme from: {qss_path}")  # 调试用

    if not qss_path.exists():
        raise FileNotFoundError(f"主题文件 {theme_name}.qss 未找到: {qss_path}")

    return qss_path.read_text(encoding="utf-8")