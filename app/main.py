# -*- coding: utf-8 -*-
# @Time : 2026/4/14 09:33
# @Author : stone


from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from app.bootstrap import bootstrap
from app.cli import build_parser
from app.gui.app_window import AppWindow
from app.services.theme_service import load_theme_qss


def main():
    parser = build_parser()
    args = parser.parse_args()

    config = bootstrap(args)

    # CLI 模式
    if args.command == "invoice-ocr":
        from app.services.invoice_ocr_service import InvoiceOCRService
        service = InvoiceOCRService()
        result = service.process(args.file)
        print(result)
        return

    # GUI 模式
    app = QApplication(sys.argv)
    app.setStyleSheet(load_theme_qss(config.get("app.theme", "dark")))

    window = AppWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()