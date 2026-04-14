# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QThread, Qt
from PySide6.QtGui import QKeyEvent, QPixmap
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QSizePolicy, QStackedWidget, QTableWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    ElevatedCardWidget,
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PillPushButton,
    PrimaryPushButton,
    PushButton,
    SegmentedWidget,
    StrongBodyLabel,
    TableWidget,
    TextEdit,
    ToolButton,
)

from app.modules.invoice.application.dto import InvoiceOCRResult
from app.modules.invoice.application.invoice_ledger_service import InvoiceLedgerService
from app.modules.invoice.ui.invoice_ocr_worker import InvoiceOCRWorker


class InvoiceOCRPage(QWidget):
    SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setObjectName("invoiceOcrInterface")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAcceptDrops(True)

        self.config = config
        self.input_mode = "single"
        self.input_source: str | None = None
        self.image_paths: list[str] = []
        self.current_image_path: str | None = None
        self.thread: QThread | None = None
        self.worker: InvoiceOCRWorker | None = None
        self.batch_results: list[InvoiceOCRResult] = []
        self.current_result_index = 0
        self.ledger_service = InvoiceLedgerService(config)

        self.pivot = SegmentedWidget(self)
        self.pivot.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.fileInterface = QWidget(self)
        self.processInterface = QWidget(self)
        self.resultInterface = QWidget(self)

        self._init_ui()
        self._connect_signals()
        self._sync_process_summary()
        self._update_step_status()

    def _init_ui(self):
        self._build_file_interface()
        self._build_process_interface()
        self._build_result_interface()

        self.addSubInterface(self.fileInterface, "FileInterface", "获取发票文件")
        self.addSubInterface(self.processInterface, "ProcessInterface", "发票识别")
        self.addSubInterface(self.resultInterface, "ResultInterface", "识别结果分析导出")

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(30, 10, 30, 30)
        self.vBoxLayout.setSpacing(16)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.fileInterface)
        self.pivot.setCurrentItem("FileInterface")

    def _build_file_interface(self):
        layout = QVBoxLayout(self.fileInterface)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        self.entryCard = ElevatedCardWidget(self.fileInterface)
        self.entryCard.setStyleSheet(
            """
            QWidget {
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 22px;
                background-color: rgba(255, 255, 255, 0.015);
            }
            """
        )

        entry_layout = QVBoxLayout(self.entryCard)
        entry_layout.setContentsMargins(24, 22, 24, 22)
        entry_layout.setSpacing(14)

        self.dropHintLabel = CaptionLabel("拖拽发票图片或图片文件夹到这里，或者使用右侧按钮选择。", self.entryCard)
        self.dropHintLabel.setWordWrap(True)
        entry_layout.addWidget(self.dropHintLabel)

        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(12)

        self.sourceInput = LineEdit(self.entryCard)
        self.sourceInput.setReadOnly(True)
        self.sourceInput.setPlaceholderText("请选择单个发票文件，或选择一个包含发票图片的文件夹")
        self.sourceInput.setClearButtonEnabled(False)
        self.sourceInput.setFixedHeight(46)
        self.sourceInput.setStyleSheet(
            self.sourceInput.styleSheet()
            + """
            QLineEdit {
                border-radius: 20px;
                padding: 0 18px;
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            QLineEdit[readOnly="true"] {
                color: rgba(255, 255, 255, 0.92);
            }
            """
        )

        self.pickFileButton = ToolButton(self.entryCard)
        self.pickFileButton.setIcon(FIF.PHOTO)
        self.pickFileButton.setFixedSize(46, 46)
        self.pickFileButton.setToolTip("选择单个文件")

        self.pickFolderButton = ToolButton(self.entryCard)
        self.pickFolderButton.setIcon(FIF.FOLDER)
        self.pickFolderButton.setFixedSize(46, 46)
        self.pickFolderButton.setToolTip("选择文件夹")

        for button in [self.pickFileButton, self.pickFolderButton]:
            button.setStyleSheet(
                button.styleSheet()
                + """
                QToolButton {
                    border-radius: 23px;
                    background-color: #2F8D63;
                }
                QToolButton:hover {
                    background-color: #2A7E58;
                }
                QToolButton:pressed {
                    background-color: #236A4B;
                }
                """
            )

        self.btn_go_process = PrimaryPushButton(FIF.RIGHT_ARROW, "进入发票识别", self.entryCard)
        self.btn_go_process.setEnabled(False)
        self.btn_go_process.setFixedHeight(46)

        input_row.addWidget(self.sourceInput, 1)
        input_row.addWidget(self.pickFileButton)
        input_row.addWidget(self.pickFolderButton)
        input_row.addWidget(self.btn_go_process)
        entry_layout.addLayout(input_row)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(10)

        self.fileStatePill = PillPushButton("未加载", self.entryCard)
        self.fileModePill = PillPushButton("当前模式：单个文件", self.entryCard)
        self.fileCountPill = PillPushButton("文件数量：0", self.entryCard)
        for button in [self.fileStatePill, self.fileModePill, self.fileCountPill]:
            button.setCheckable(False)
            status_row.addWidget(button)
        status_row.addStretch(1)
        entry_layout.addLayout(status_row)
        layout.addWidget(self.entryCard)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        list_card = ElevatedCardWidget(self.fileInterface)
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(18, 18, 18, 18)
        list_layout.setSpacing(10)
        list_layout.addWidget(StrongBodyLabel("文件列表", list_card))

        self.filePathLabel = CaptionLabel("左侧展示当前输入范围内的全部图片文件。", list_card)
        self.filePathLabel.setWordWrap(True)
        list_layout.addWidget(self.filePathLabel)

        self.fileList = QListWidget(list_card)
        self.fileList.setMinimumWidth(340)
        self.fileList.setStyleSheet(
            """
            QListWidget {
                border: none;
                background: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 12px 14px;
                margin: 5px 0;
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid transparent;
            }
            QListWidget::item:hover {
                background: rgba(47, 141, 99, 0.12);
            }
            QListWidget::item:selected {
                background: rgba(47, 141, 99, 0.22);
                border: 1px solid rgba(47, 141, 99, 0.48);
                color: white;
                font-weight: 600;
            }
            """
        )
        list_layout.addWidget(self.fileList, 1)

        preview_card = ElevatedCardWidget(self.fileInterface)
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(18, 18, 18, 18)
        preview_layout.setSpacing(12)
        preview_layout.addWidget(StrongBodyLabel("预览图", preview_card))

        self.previewHintLabel = CaptionLabel("点击左侧文件切换预览，右侧支持键盘左右方向键切换。", preview_card)
        self.previewHintLabel.setWordWrap(True)
        preview_layout.addWidget(self.previewHintLabel)

        self.previewStack = QStackedWidget(preview_card)

        self.previewEmptyState = QWidget(preview_card)
        empty_layout = QVBoxLayout(self.previewEmptyState)
        empty_layout.setContentsMargins(24, 24, 24, 24)
        empty_layout.setSpacing(10)
        empty_layout.setAlignment(Qt.AlignCenter)

        self.emptyIconLabel = QLabel(self.previewEmptyState)
        self.emptyIconLabel.setPixmap(FIF.PHOTO.icon().pixmap(46, 46))
        self.emptyIconLabel.setAlignment(Qt.AlignCenter)
        self.emptyTitleLabel = StrongBodyLabel("等待导入发票文件", self.previewEmptyState)
        self.emptyCaptionLabel = CaptionLabel("支持拖拽、单文件选择和文件夹选择。", self.previewEmptyState)
        self.emptyCaptionLabel.setAlignment(Qt.AlignCenter)
        self.emptyCaptionLabel.setWordWrap(True)

        empty_layout.addWidget(self.emptyIconLabel, 0, Qt.AlignCenter)
        empty_layout.addWidget(self.emptyTitleLabel, 0, Qt.AlignCenter)
        empty_layout.addWidget(self.emptyCaptionLabel, 0, Qt.AlignCenter)

        self.image_label = QLabel(self.previewStack)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(560, 520)
        self.image_label.setStyleSheet(
            """
            QLabel {
                border: 1px dashed rgba(120, 120, 120, 0.45);
                border-radius: 14px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255,255,255,0.02),
                    stop:1 rgba(47,141,99,0.05)
                );
            }
            """
        )

        self.previewStack.addWidget(self.previewEmptyState)
        self.previewStack.addWidget(self.image_label)
        self.previewStack.setCurrentWidget(self.previewEmptyState)
        preview_layout.addWidget(self.previewStack, 1)

        info_bar = QHBoxLayout()
        info_bar.setContentsMargins(0, 0, 0, 0)
        info_bar.setSpacing(10)

        self.previewNamePill = PillPushButton("文件：-", preview_card)
        self.previewSizePill = PillPushButton("尺寸：-", preview_card)
        self.previewIndexPill = PillPushButton("位置：-", preview_card)
        for button in [self.previewNamePill, self.previewSizePill, self.previewIndexPill]:
            button.setCheckable(False)
            info_bar.addWidget(button)
        info_bar.addStretch(1)
        preview_layout.addLayout(info_bar)

        content_row.addWidget(list_card, 4)
        content_row.addWidget(preview_card, 8)
        layout.addLayout(content_row, 1)

    def _build_process_interface(self):
        layout = QHBoxLayout(self.processInterface)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        run_card = ElevatedCardWidget(self.processInterface)
        run_layout = QVBoxLayout(run_card)
        run_layout.setContentsMargins(18, 18, 18, 18)
        run_layout.setSpacing(12)

        run_layout.addWidget(StrongBodyLabel("发票识别", run_card))
        self.processFileLabel = CaptionLabel("当前文件：未选择", run_card)
        self.processConfigLabel = CaptionLabel("", run_card)
        self.processConfigLabel.setWordWrap(True)
        self.status_pill = PillPushButton("等待导入发票图片", run_card)
        self.status_pill.setCheckable(False)
        self.stepFileStatus = PillPushButton("待导入文件", run_card)
        self.stepProcessStatus = PillPushButton("等待识别", run_card)
        self.stepResultStatus = PillPushButton("等待结果", run_card)
        for button in [self.stepFileStatus, self.stepProcessStatus, self.stepResultStatus]:
            button.setCheckable(False)

        step_row = QHBoxLayout()
        step_row.setContentsMargins(0, 0, 0, 0)
        step_row.setSpacing(10)
        step_row.addWidget(self.stepFileStatus)
        step_row.addWidget(self.stepProcessStatus)
        step_row.addWidget(self.stepResultStatus)
        step_row.addStretch(1)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(10)
        self.btn_back_file = PushButton(FIF.LEFT_ARROW, "返回文件选择", run_card)
        self.btn_run = PrimaryPushButton(FIF.PLAY, "开始识别", run_card)
        self.btn_run.setEnabled(False)
        button_row.addWidget(self.btn_back_file)
        button_row.addWidget(self.btn_run)
        button_row.addStretch(1)

        run_layout.addWidget(self.processFileLabel)
        run_layout.addWidget(self.processConfigLabel)
        run_layout.addWidget(self.status_pill)
        run_layout.addLayout(step_row)
        run_layout.addStretch(1)
        run_layout.addLayout(button_row)

        note_card = ElevatedCardWidget(self.processInterface)
        note_layout = QVBoxLayout(note_card)
        note_layout.setContentsMargins(18, 18, 18, 18)
        note_layout.setSpacing(10)
        note_layout.addWidget(StrongBodyLabel("处理模式", note_card))
        note_layout.addWidget(BodyLabel("单个文件：识别 1 张图片。", note_card))
        note_layout.addWidget(BodyLabel("文件夹：顺序识别全部图片。", note_card))
        note_layout.addWidget(BodyLabel("识别完成后可在结果页查看汇总和单项详情。", note_card))
        note_layout.addStretch(1)

        layout.addWidget(run_card, 7)
        layout.addWidget(note_card, 5)

    def _build_result_interface(self):
        layout = QVBoxLayout(self.resultInterface)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        action_card = ElevatedCardWidget(self.resultInterface)
        action_layout = QHBoxLayout(action_card)
        action_layout.setContentsMargins(16, 12, 16, 12)
        action_layout.setSpacing(10)

        self.btn_back_process = PushButton(FIF.LEFT_ARROW, "返回识别步骤", action_card)
        self.btn_save_ledger = PushButton(FIF.SAVE, "批量保存到台账", action_card)
        self.btn_export = PrimaryPushButton(FIF.SHARE, "导出 JSON", action_card)
        self.btn_save_ledger.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.resultStatePill = PillPushButton("暂无识别结果", action_card)
        self.resultStatePill.setCheckable(False)

        action_layout.addWidget(self.btn_back_process)
        action_layout.addWidget(self.btn_save_ledger)
        action_layout.addWidget(self.btn_export)
        action_layout.addStretch(1)
        action_layout.addWidget(self.resultStatePill)
        layout.addWidget(action_card)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(14)

        summary_card = ElevatedCardWidget(self.resultInterface)
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        summary_layout.setSpacing(8)
        summary_layout.addWidget(StrongBodyLabel("批量结果汇总", summary_card))

        self.summary_table = TableWidget(summary_card)
        self.summary_table.setBorderVisible(True)
        self.summary_table.setBorderRadius(8)
        self.summary_table.setWordWrap(False)
        self.summary_table.setColumnCount(5)
        self.summary_table.setHorizontalHeaderLabels(["文件", "发票代码", "发票号码", "状态", "错误数"])
        self.summary_table.verticalHeader().hide()
        self.summary_table.setMinimumHeight(360)
        summary_layout.addWidget(self.summary_table, 1)

        detail_column = QVBoxLayout()
        detail_column.setContentsMargins(0, 0, 0, 0)
        detail_column.setSpacing(14)

        result_card = ElevatedCardWidget(self.resultInterface)
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(16, 16, 16, 16)
        result_layout.setSpacing(8)
        result_layout.addWidget(StrongBodyLabel("单项识别结果", result_card))

        self.result_table = TableWidget(result_card)
        self.result_table.setBorderVisible(True)
        self.result_table.setBorderRadius(8)
        self.result_table.setWordWrap(False)
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["字段", "值"])
        self.result_table.verticalHeader().hide()
        self.result_table.setMinimumHeight(220)
        result_layout.addWidget(self.result_table, 1)

        raw_card = ElevatedCardWidget(self.resultInterface)
        raw_layout = QVBoxLayout(raw_card)
        raw_layout.setContentsMargins(16, 16, 16, 16)
        raw_layout.setSpacing(8)
        raw_layout.addWidget(StrongBodyLabel("原始文本", raw_card))
        self.raw_text = TextEdit(raw_card)
        self.raw_text.setPlaceholderText("识别后的原始文本将显示在这里")
        self.raw_text.setReadOnly(True)
        raw_layout.addWidget(self.raw_text, 1)

        detail_column.addWidget(result_card, 5)
        detail_column.addWidget(raw_card, 6)
        content_row.addWidget(summary_card, 6)
        content_row.addLayout(detail_column, 5)
        layout.addLayout(content_row, 1)

    def _connect_signals(self):
        self.pickFileButton.clicked.connect(self.open_image)
        self.pickFolderButton.clicked.connect(self.open_folder)
        self.btn_go_process.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.processInterface))
        self.btn_back_file.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.fileInterface))
        self.btn_back_process.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.processInterface))
        self.btn_run.clicked.connect(self.run_ocr)
        self.btn_export.clicked.connect(self.export_json)
        self.btn_save_ledger.clicked.connect(self.save_to_ledger)
        self.fileList.currentRowChanged.connect(self.on_file_selection_changed)
        self.summary_table.itemSelectionChanged.connect(self.on_summary_selection_changed)

    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index: int):
        widget = self.stackedWidget.widget(index)
        if widget:
            self.pivot.setCurrentItem(widget.objectName())

    def keyPressEvent(self, event: QKeyEvent):
        if self.stackedWidget.currentWidget() is self.fileInterface and self.image_paths:
            current_row = self.fileList.currentRow()
            if event.key() == Qt.Key_Left and current_row > 0:
                self.fileList.setCurrentRow(current_row - 1)
                return
            if event.key() == Qt.Key_Right and current_row < len(self.image_paths) - 1:
                self.fileList.setCurrentRow(current_row + 1)
                return
        super().keyPressEvent(event)

    def _apply_drop_highlight(self, active: bool):
        if active:
            self.entryCard.setStyleSheet(
                """
                QWidget {
                    border: 1px solid rgba(47, 141, 99, 0.88);
                    border-radius: 22px;
                    background-color: rgba(47, 141, 99, 0.10);
                }
                """
            )
            self.dropHintLabel.setText("松开鼠标即可导入发票文件或图片文件夹。")
        else:
            self.entryCard.setStyleSheet(
                """
                QWidget {
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 22px;
                    background-color: rgba(255, 255, 255, 0.015);
                }
                """
            )
            self.dropHintLabel.setText("拖拽发票图片或图片文件夹到这里，或者使用右侧按钮选择。")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self._apply_drop_highlight(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._apply_drop_highlight(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._apply_drop_highlight(False)

        urls = event.mimeData().urls()
        if not urls:
            return

        local_paths = [Path(url.toLocalFile()) for url in urls if url.isLocalFile()]
        if not local_paths:
            return

        if len(local_paths) == 1 and local_paths[0].is_dir():
            self._load_folder(local_paths[0])
            return

        image_paths = [
            str(path)
            for path in local_paths
            if path.is_file() and path.suffix.lower() in self.SUPPORTED_IMAGE_SUFFIXES
        ]
        if image_paths:
            self._load_selected_images(image_paths, "拖拽文件", "single" if len(image_paths) == 1 else "folder")
            return

        QMessageBox.warning(self, "提示", "拖拽内容中没有可识别的图片文件")

    def _sync_process_summary(self):
        if not self.current_image_path:
            self.processFileLabel.setText("当前文件：未选择")
        elif self.input_mode == "folder":
            self.processFileLabel.setText(f"当前来源：文件夹，共 {len(self.image_paths)} 张图片")
        else:
            self.processFileLabel.setText(f"当前文件：{self.current_image_path}")

        self.processConfigLabel.setText(
            "当前配置："
            f"引擎 {self.config.get('ocr.engine', 'paddleocr')} | "
            f"语言 {self.config.get('ocr.lang', 'ch')} | "
            f"GPU {'开启' if self.config.get('ocr.use_gpu', False) else '关闭'} | "
            f"调试图 {'保存' if self.config.get('ocr.save_debug_image', True) else '不保存'}"
        )

    def _update_step_status(self):
        self.stepFileStatus.setText("文件已就绪" if self.current_image_path else "待导入文件")
        self.stepProcessStatus.setText("识别完成" if self.batch_results else ("可开始识别" if self.current_image_path else "等待识别"))
        self.stepResultStatus.setText("可分析导出" if self.batch_results else "等待结果")

    def _reset_results(self):
        self.batch_results = []
        self.current_result_index = 0
        self.result_table.setRowCount(0)
        self.summary_table.setRowCount(0)
        self.raw_text.clear()
        self.btn_save_ledger.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.resultStatePill.setText("暂无识别结果")

    def _show_empty_preview(self):
        self.previewStack.setCurrentWidget(self.previewEmptyState)
        self.previewNamePill.setText("文件：-")
        self.previewSizePill.setText("尺寸：-")
        self.previewIndexPill.setText("位置：-")

    def _render_preview(self, image_path: str):
        self.current_image_path = image_path
        pixmap = QPixmap(image_path)
        scaled = pixmap.scaled(720, 680, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.previewStack.setCurrentWidget(self.image_label)

        file_name = Path(image_path).name
        image_index = self.image_paths.index(image_path) + 1 if image_path in self.image_paths else 1
        self.previewNamePill.setText(f"文件：{file_name}")
        self.previewSizePill.setText(
            f"尺寸：{pixmap.width()} x {pixmap.height()}" if not pixmap.isNull() else "尺寸：读取失败"
        )
        self.previewIndexPill.setText(f"位置：{image_index}/{len(self.image_paths)}")
        self._sync_process_summary()

    def _populate_file_list(self):
        self.fileList.clear()
        for index, path in enumerate(self.image_paths, start=1):
            item = QListWidgetItem(f"{index:02d}. {Path(path).name}")
            item.setToolTip(path)
            self.fileList.addItem(item)
        if self.image_paths:
            self.fileList.setCurrentRow(0)
        else:
            self._show_empty_preview()

    def _load_selected_images(self, image_paths: list[str], source: str, mode: str):
        self.input_mode = "folder" if mode == "folder" or len(image_paths) > 1 else "single"
        self.input_source = source
        self.image_paths = image_paths
        self._reset_results()
        self.btn_run.setEnabled(True)
        self.btn_go_process.setEnabled(True)

        self.sourceInput.setText(source)
        if self.input_mode == "folder":
            self.filePathLabel.setText(f"当前来源：{source}")
            self.fileStatePill.setText(f"已加载 {len(image_paths)} 个文件")
            self.fileModePill.setText("当前模式：文件夹")
        else:
            self.filePathLabel.setText(f"当前文件：{source}")
            self.fileStatePill.setText("已加载 1 个文件")
            self.fileModePill.setText("当前模式：单个文件")
        self.fileCountPill.setText(f"文件数量：{len(image_paths)}")

        self._populate_file_list()
        self._update_step_status()
        self.stackedWidget.setCurrentWidget(self.fileInterface)
        self.pivot.setCurrentItem("FileInterface")
        self.setFocus()

    def _load_folder(self, folder_path: Path):
        image_paths = [
            str(path)
            for path in sorted(folder_path.iterdir())
            if path.is_file() and path.suffix.lower() in self.SUPPORTED_IMAGE_SUFFIXES
        ]
        if not image_paths:
            QMessageBox.warning(self, "提示", "该文件夹中没有可识别的图片文件")
            return
        self._load_selected_images(image_paths, str(folder_path), "folder")

    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择发票图片",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not file_path:
            return
        self._load_selected_images([file_path], file_path, "single")

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择发票图片文件夹",
            "",
        )
        if not folder_path:
            return
        self._load_folder(Path(folder_path))

    def on_file_selection_changed(self, row: int):
        if row < 0 or row >= len(self.image_paths):
            return
        self._render_preview(self.image_paths[row])

    def run_ocr(self):
        if not self.image_paths:
            QMessageBox.warning(self, "提示", "请先选择图片或文件夹")
            return

        self.thread = QThread()
        self.worker = InvoiceOCRWorker(self.image_paths, self.config)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)

        self.btn_run.setEnabled(False)
        self.status_pill.setText("识别中...")
        self.stepProcessStatus.setText("识别中")
        self.thread.start()

    def on_progress(self, index: int, message: str):
        self.status_pill.setText(message)
        if self.input_mode == "folder":
            self.stepProcessStatus.setText(f"批量识别 {index}/{len(self.image_paths)}")

    def _render_summary_table(self):
        self.summary_table.setRowCount(len(self.batch_results))
        for row, result in enumerate(self.batch_results):
            file_name = Path(result.source_file).name if result.source_file else f"第 {row + 1} 项"
            status = "待复核" if result.errors else "通过"
            values = [
                file_name,
                result.invoice_code or "",
                result.invoice_number or "",
                status,
                str(len(result.errors)),
            ]
            for column, value in enumerate(values):
                self.summary_table.setItem(row, column, QTableWidgetItem(value))

    def _render_result_detail(self, index: int):
        if not self.batch_results or index < 0 or index >= len(self.batch_results):
            return
        self.current_result_index = index
        result = self.batch_results[index]
        rows = result.display_rows()
        self.result_table.setRowCount(len(rows))
        for row, (key, value) in enumerate(rows):
            self.result_table.setItem(row, 0, QTableWidgetItem(key))
            self.result_table.setItem(row, 1, QTableWidgetItem(value))
        self.raw_text.setPlainText("\n".join(result.raw_texts))
        self.summary_table.selectRow(index)

    def on_finished(self, results: list[InvoiceOCRResult]):
        self.batch_results = results
        self.btn_run.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.btn_save_ledger.setEnabled(True)
        self.status_pill.setText("识别完成")
        self.resultStatePill.setText(f"已生成 {len(results)} 条识别结果")

        self._render_summary_table()
        if results:
            self._render_result_detail(0)
        self._update_step_status()
        self.stackedWidget.setCurrentWidget(self.resultInterface)
        self.pivot.setCurrentItem("ResultInterface")

        InfoBar.success(
            "识别完成",
            f"已完成 {len(results)} 个文件的识别，现在可以查看汇总、导出或批量入账。",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2200,
            parent=self.window(),
        )

    def on_failed(self, message: str):
        self.btn_run.setEnabled(True)
        self.status_pill.setText("识别失败")
        self.stepProcessStatus.setText("识别失败")
        QMessageBox.critical(self, "识别失败", message)

    def on_summary_selection_changed(self):
        selected_items = self.summary_table.selectedItems()
        if not selected_items:
            return
        self._render_result_detail(selected_items[0].row())

    def export_json(self):
        if not self.batch_results:
            return

        if len(self.batch_results) == 1:
            default_name = Path(self.batch_results[0].source_file or "invoice").with_suffix(".json").name
            default_payload = self.batch_results[0].to_dict()
        else:
            default_name = f"{Path(self.input_source or 'invoice_batch').name}.json"
            default_payload = {
                "mode": self.input_mode,
                "source": self.input_source,
                "count": len(self.batch_results),
                "items": [result.to_dict() for result in self.batch_results],
            }

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 JSON",
            str(Path(self.config.get("storage.export_dir", "data/export")) / default_name),
            "JSON Files (*.json)",
        )
        if not save_path:
            return

        Path(save_path).write_text(
            json.dumps(default_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        InfoBar.success(
            "导出成功",
            f"JSON 已导出到 {save_path}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2500,
            parent=self.window(),
        )

    def save_to_ledger(self):
        if not self.batch_results:
            QMessageBox.warning(self, "提示", "请先完成识别")
            return

        success_count = 0
        duplicate_count = 0
        last_row_id = None
        for result in self.batch_results:
            ok, _, row_id = self.ledger_service.save_invoice_result(
                result,
                result.source_file or self.current_image_path or "",
            )
            if ok:
                success_count += 1
                last_row_id = row_id
            else:
                duplicate_count += 1

        self.resultStatePill.setText("已批量保存到台账")
        InfoBar.success(
            "保存完成",
            f"成功 {success_count} 条，跳过重复 {duplicate_count} 条"
            + (f"，最后记录 ID: {last_row_id}" if last_row_id else ""),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2800,
            parent=self.window(),
        )
