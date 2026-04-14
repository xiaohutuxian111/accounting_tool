# -*- coding: utf-8 -*-
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme, setThemeColor

from app.bootstrap import bootstrap
from app.cli import build_parser
from app.gui.app_window import AppWindow


def main():
    parser = build_parser()
    args = parser.parse_args()

    config = bootstrap(args)

    if args.command == "invoice-ocr":
        from app.modules.invoice.application.invoice_ocr_service import InvoiceOCRService

        service = InvoiceOCRService(config)
        result = service.process(args.file)
        print(result)
        return

    app = QApplication(sys.argv)

    theme_name = config.get("app.theme", "dark")
    theme_map = {
        "dark": Theme.DARK,
        "light": Theme.LIGHT,
        "auto": Theme.AUTO,
    }
    setTheme(theme_map.get(theme_name, Theme.DARK))
    setThemeColor(config.get("app.theme_color", "#2dd36f"))

    window = AppWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
