# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from PySide6.QtCore import QEvent, QThread, Qt
from PySide6.QtGui import QKeyEvent, QPixmap
from PySide6.QtWidgets import QBoxLayout, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QListWidget, QListWidgetItem, QMessageBox, QProgressBar, QSizePolicy, QStackedWidget, QTableWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, CaptionLabel, ElevatedCardWidget, FluentIcon as FIF, InfoBar, InfoBarPosition, LineEdit, PillPushButton, PrimaryPushButton, PushButton, SegmentedWidget, StrongBodyLabel, TableWidget, TextEdit, ToolButton

from app.modules.invoice.application.dto import InvoiceOCRResult
from app.modules.invoice.application.invoice_ledger_service import InvoiceLedgerService
from app.modules.invoice.domain.invoice_parser import InvoiceParser
from app.modules.invoice.infrastructure.pdf_invoice_renderer import PDFInvoiceRenderer
from app.modules.invoice.ui.invoice_ocr_worker import InvoiceOCRWorker


class InvoiceOCRPage(QWidget):
    SUPPORTED_FILE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.pdf'}

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setObjectName('invoiceOcrInterface')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAcceptDrops(True)
        self.config = config
        self.input_mode = 'single'
        self.input_source: str | None = None
        self.image_paths: list[str] = []
        self.processing_image_paths: list[str] = []
        self.current_image_path: str | None = None
        self.batch_results: list[InvoiceOCRResult] = []
        self.current_result_index = 0
        self.file_preview_path: str = ''
        self.result_preview_path: str = ''
        self.thread: QThread | None = None
        self.worker: InvoiceOCRWorker | None = None
        self.resultDetailCompact: bool | None = None
        self.ledger_service = InvoiceLedgerService(config)
        self.pdf_renderer = PDFInvoiceRenderer(config.get('storage.temp_dir', 'data/temp'))
        self.pivot = SegmentedWidget(self)
        self.pivot.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)
        self.fileInterface = QWidget(self)
        self.resultInterface = QWidget(self)
        self._init_ui()
        self._connect_signals()
        self._sync_result_summary()
        self._reset_results()

    def _init_ui(self):
        self._build_file_interface()
        self._build_result_interface()
        self.addSubInterface(self.fileInterface, 'FileInterface', '获取发票文件')
        self.addSubInterface(self.resultInterface, 'ResultInterface', '识别结果分析导出')
        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(30, 10, 30, 30)
        self.vBoxLayout.setSpacing(16)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.fileInterface)
        self.pivot.setCurrentItem('FileInterface')

    def _build_file_interface(self):
        layout = QVBoxLayout(self.fileInterface)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        self.entryCard = ElevatedCardWidget(self.fileInterface)
        self.entryCard.setStyleSheet(self._entry_style(False))
        entry_layout = QVBoxLayout(self.entryCard)
        entry_layout.setContentsMargins(24, 22, 24, 22)
        entry_layout.setSpacing(14)
        self.dropHintLabel = CaptionLabel('拖拽发票图片、PDF 电子发票或文件夹到这里，或使用右侧按钮导入。', self.entryCard)
        self.dropHintLabel.setWordWrap(True)
        entry_layout.addWidget(self.dropHintLabel)
        input_row = QHBoxLayout()
        input_row.setSpacing(12)
        self.sourceInput = LineEdit(self.entryCard)
        self.sourceInput.setReadOnly(True)
        self.sourceInput.setPlaceholderText('选择单个发票图片或 PDF，或选择一个包含发票文件的文件夹')
        self.sourceInput.setClearButtonEnabled(False)
        self.sourceInput.setFixedHeight(48)
        self.sourceInput.setStyleSheet(self.sourceInput.styleSheet() + 'QLineEdit { border-radius: 20px; padding: 0 18px; background-color: transparent; border: 1px solid rgba(255,255,255,0.08);} QLineEdit[readOnly="true"] { color: rgba(255,255,255,0.92); }')
        self.pickFileButton = ToolButton(self.entryCard)
        self.pickFileButton.setIcon(FIF.PHOTO)
        self.pickFileButton.setFixedSize(48, 48)
        self.pickFolderButton = ToolButton(self.entryCard)
        self.pickFolderButton.setIcon(FIF.FOLDER)
        self.pickFolderButton.setFixedSize(48, 48)
        for button in [self.pickFileButton, self.pickFolderButton]:
            button.setStyleSheet(button.styleSheet() + 'QToolButton { border-radius: 24px; background-color: #2F8D63; } QToolButton:hover { background-color: #2A7E58; } QToolButton:pressed { background-color: #236A4B; }')
        self.btn_go_result = PrimaryPushButton(FIF.RIGHT_ARROW, '进入结果分析', self.entryCard)
        self.btn_go_result.setEnabled(False)
        self.btn_go_result.setFixedHeight(48)
        self.processingCountLabel = CaptionLabel('本次将处理 0 个文件', self.entryCard)
        self.processingCountLabel.setAlignment(Qt.AlignCenter)
        input_row.addWidget(self.sourceInput, 1)
        input_row.addWidget(self.pickFileButton)
        input_row.addWidget(self.pickFolderButton)
        input_row.addWidget(self.btn_go_result)
        input_row.addWidget(self.processingCountLabel)
        entry_layout.addLayout(input_row)
        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        self.fileStatePill = PillPushButton('未加载', self.entryCard)
        self.fileModePill = PillPushButton('当前模式：单个文件', self.entryCard)
        self.fileCountPill = PillPushButton('文件数量：0', self.entryCard)
        self.fileSelectionPill = PillPushButton('处理范围：全部文件', self.entryCard)
        for button in [self.fileStatePill, self.fileModePill, self.fileCountPill, self.fileSelectionPill]:
            button.setCheckable(False)
            status_row.addWidget(button)
        status_row.addStretch(1)
        entry_layout.addLayout(status_row)
        layout.addWidget(self.entryCard)
        content_row = QHBoxLayout()
        content_row.setSpacing(16)
        list_card = ElevatedCardWidget(self.fileInterface)
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(18, 18, 18, 18)
        list_layout.setSpacing(10)
        list_layout.addWidget(StrongBodyLabel('文件列表', list_card))
        self.filePathLabel = CaptionLabel('左侧显示当前输入范围内的全部发票文件。', list_card)
        self.filePathLabel.setWordWrap(True)
        list_layout.addWidget(self.filePathLabel)
        list_action_row = QHBoxLayout()
        list_action_row.setSpacing(8)
        self.selectAllButton = PushButton('全选', list_card)
        self.clearSelectionButton = PushButton('清空勾选', list_card)
        list_action_row.addWidget(self.selectAllButton)
        list_action_row.addWidget(self.clearSelectionButton)
        list_action_row.addStretch(1)
        list_layout.addLayout(list_action_row)
        self.fileList = QListWidget(list_card)
        self.fileList.setMinimumWidth(280)
        self.fileList.setStyleSheet('QListWidget { border: none; background: transparent; outline: none; } QListWidget::item { padding: 12px 14px; margin: 5px 0; border-radius: 12px; background: rgba(255,255,255,0.02); border: 1px solid transparent; } QListWidget::item:hover { background: rgba(47,141,99,0.12); } QListWidget::item:selected { background: rgba(47,141,99,0.22); border: 1px solid rgba(47,141,99,0.48); color: white; font-weight: 600; }')
        list_layout.addWidget(self.fileList, 1)
        self.fileCheckHintLabel = CaptionLabel('可勾选需要进入识别和结果分析的文件；如果一个都不勾选，则默认处理全部文件。', list_card)
        self.fileCheckHintLabel.setWordWrap(True)
        list_layout.addWidget(self.fileCheckHintLabel)
        preview_card = ElevatedCardWidget(self.fileInterface)
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(18, 18, 18, 18)
        preview_layout.setSpacing(12)
        preview_layout.addWidget(StrongBodyLabel('发票预览', preview_card))
        self.previewHintLabel = CaptionLabel('点击左侧文件切换预览，右侧支持键盘左右方向键切换。', preview_card)
        self.previewHintLabel.setWordWrap(True)
        preview_layout.addWidget(self.previewHintLabel)
        self.previewStack = QStackedWidget(preview_card)
        self.previewEmptyState = self._create_empty_preview_state(preview_card, '等待导入发票文件', '支持拖拽、单文件选择和文件夹选择。')
        self.image_label = self._create_preview_label(self.previewStack, 520, 380)
        self.previewStack.addWidget(self.previewEmptyState)
        self.previewStack.addWidget(self.image_label)
        self.previewStack.setCurrentWidget(self.previewEmptyState)
        self.previewStack.setMinimumHeight(440)
        preview_layout.addWidget(self.previewStack, 1)
        info_bar = QHBoxLayout()
        info_bar.setSpacing(10)
        self.previewNamePill = PillPushButton('文件：-', preview_card)
        self.previewSizePill = PillPushButton('尺寸：-', preview_card)
        self.previewIndexPill = PillPushButton('位置：-', preview_card)
        for button in [self.previewNamePill, self.previewSizePill, self.previewIndexPill]:
            button.setCheckable(False)
            info_bar.addWidget(button)
        info_bar.addStretch(1)
        preview_layout.addLayout(info_bar)
        content_row.addWidget(list_card, 3)
        content_row.addWidget(preview_card, 9)
        layout.addLayout(content_row, 1)
    def _build_result_interface(self):
        layout = QVBoxLayout(self.resultInterface)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        action_card = ElevatedCardWidget(self.resultInterface)
        action_layout = QHBoxLayout(action_card)
        action_layout.setContentsMargins(16, 12, 16, 12)
        action_layout.setSpacing(10)
        self.btn_back_file = PushButton(FIF.LEFT_ARROW, '返回文件选择', action_card)
        self.btn_run = PrimaryPushButton(FIF.PLAY, '开始识别', action_card)
        self.btn_save_ledger = PushButton(FIF.SAVE, '批量保存到台账', action_card)
        self.btn_export = PushButton(FIF.SHARE, '导出结果', action_card)
        self.resultStatePill = PillPushButton('等待识别', action_card)
        self.resultStatePill.setCheckable(False)
        self.btn_run.setEnabled(False)
        self.btn_save_ledger.setEnabled(False)
        self.btn_export.setEnabled(False)
        action_layout.addWidget(self.btn_back_file)
        action_layout.addWidget(self.btn_run)
        action_layout.addWidget(self.btn_save_ledger)
        action_layout.addWidget(self.btn_export)
        action_layout.addStretch(1)
        action_layout.addWidget(self.resultStatePill)
        layout.addWidget(action_card)
        state_card = ElevatedCardWidget(self.resultInterface)
        state_layout = QVBoxLayout(state_card)
        state_layout.setContentsMargins(16, 16, 16, 16)
        state_layout.setSpacing(10)
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        icon_label = QLabel(state_card)
        icon_label.setPixmap(FIF.DOCUMENT.icon().pixmap(18, 18))
        title_row.addWidget(icon_label, 0, Qt.AlignVCenter)
        title_row.addWidget(StrongBodyLabel('识别状态', state_card), 0, Qt.AlignVCenter)
        title_row.addStretch(1)
        state_layout.addLayout(title_row)
        self.resultFileLabel = CaptionLabel('当前文件：未选择', state_card)
        self.resultConfigLabel = CaptionLabel('', state_card)
        self.resultConfigLabel.setWordWrap(True)
        self.resultProgressPill = PillPushButton('待识别', state_card)
        self.resultProgressPill.setCheckable(False)
        self.resultProgressInfoLabel = CaptionLabel('当前进度：0 / 0', state_card)
        self.resultProgressBar = QProgressBar(state_card)
        self.resultProgressBar.setRange(0, 100)
        self.resultProgressBar.setValue(0)
        self.resultProgressBar.setTextVisible(True)
        state_layout.addWidget(self.resultFileLabel)
        state_layout.addWidget(self.resultConfigLabel)
        state_layout.addWidget(self.resultProgressPill)
        state_layout.addWidget(self.resultProgressInfoLabel)
        state_layout.addWidget(self.resultProgressBar)
        layout.addWidget(state_card)
        content_row = QHBoxLayout()
        content_row.setSpacing(14)
        summary_card = ElevatedCardWidget(self.resultInterface)
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        summary_layout.setSpacing(8)
        summary_layout.addWidget(StrongBodyLabel('批量结果汇总', summary_card))
        self.summary_table = TableWidget(summary_card)
        self.summary_table.setBorderVisible(True)
        self.summary_table.setBorderRadius(8)
        self.summary_table.setWordWrap(False)
        self.summary_table.setColumnCount(4)
        self.summary_table.setHorizontalHeaderLabels(['文件', '发票号码', '状态', '错误数'])
        self.summary_table.verticalHeader().hide()
        header = self.summary_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.summary_table.setMinimumHeight(320)
        summary_layout.addWidget(self.summary_table, 1)
        preview_card = ElevatedCardWidget(self.resultInterface)
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(16, 16, 16, 16)
        preview_layout.setSpacing(8)
        preview_layout.addWidget(StrongBodyLabel('发票预览', preview_card))
        self.resultPreviewStack = QStackedWidget(preview_card)
        self.resultPreviewEmptyState = self._create_empty_preview_state(preview_card, '等待识别结果', '识别前后都可以在这里查看当前发票。')
        self.resultImageLabel = self._create_preview_label(self.resultPreviewStack, 460, 320)
        self.resultPreviewStack.addWidget(self.resultPreviewEmptyState)
        self.resultPreviewStack.addWidget(self.resultImageLabel)
        self.resultPreviewStack.setCurrentWidget(self.resultPreviewEmptyState)
        self.resultPreviewStack.setMinimumHeight(360)
        preview_layout.addWidget(self.resultPreviewStack, 1)
        preview_info = QHBoxLayout()
        preview_info.setSpacing(10)
        self.resultPreviewNamePill = PillPushButton('文件：-', preview_card)
        self.resultPreviewSizePill = PillPushButton('尺寸：-', preview_card)
        self.resultPreviewIndexPill = PillPushButton('位置：-', preview_card)
        for button in [self.resultPreviewNamePill, self.resultPreviewSizePill, self.resultPreviewIndexPill]:
            button.setCheckable(False)
            preview_info.addWidget(button)
        preview_info.addStretch(1)
        preview_layout.addLayout(preview_info)
        result_card = ElevatedCardWidget(self.resultInterface)
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(16, 16, 16, 16)
        result_layout.setSpacing(8)
        result_layout.addWidget(StrongBodyLabel('单项识别结果', result_card))
        self.result_table = TableWidget(result_card)
        self.result_table.setBorderVisible(True)
        self.result_table.setBorderRadius(8)
        self.result_table.setWordWrap(False)
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(['字段', '值'])
        self.result_table.verticalHeader().hide()
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setMinimumHeight(220)
        result_layout.addWidget(self.result_table, 1)
        raw_card = ElevatedCardWidget(self.resultInterface)
        raw_layout = QVBoxLayout(raw_card)
        raw_layout.setContentsMargins(16, 16, 16, 16)
        raw_layout.setSpacing(8)
        raw_layout.addWidget(StrongBodyLabel('原始文本', raw_card))
        self.raw_text = TextEdit(raw_card)
        self.raw_text.setPlaceholderText('识别后的原始文本将显示在这里')
        self.raw_text.setReadOnly(True)
        self.raw_text.setStyleSheet(self.raw_text.styleSheet() + 'QTextEdit { padding: 14px 16px; line-height: 1.6; }')
        raw_layout.addWidget(self.raw_text, 1)
        self.summaryCard = summary_card
        self.resultCard = result_card
        self.previewCard = preview_card
        self.rawCard = raw_card
        self.topRowLayout = QVBoxLayout()
        self.topRowLayout.setSpacing(14)
        self.detailSplitRow = QHBoxLayout()
        self.detailSplitRow.setSpacing(14)
        self.detailSplitRow.addWidget(self.resultCard, 5)
        self.detailSplitRow.addWidget(self.rawCard, 5)
        self.topRowLayout.addLayout(self.detailSplitRow, 4)
        self.topRowLayout.addWidget(self.previewCard, 5)
        content_row.addWidget(self.summaryCard, 4)
        content_row.addLayout(self.topRowLayout, 7)
        layout.addLayout(content_row, 1)

    def _create_empty_preview_state(self, parent, title: str, caption: str):
        state = QWidget(parent)
        state_layout = QVBoxLayout(state)
        state_layout.setAlignment(Qt.AlignCenter)
        state_layout.setSpacing(10)
        icon = QLabel(state)
        icon.setPixmap(FIF.PHOTO.icon().pixmap(46, 46))
        icon.setAlignment(Qt.AlignCenter)
        title_label = StrongBodyLabel(title, state)
        caption_label = CaptionLabel(caption, state)
        caption_label.setAlignment(Qt.AlignCenter)
        caption_label.setWordWrap(True)
        state_layout.addWidget(icon, 0, Qt.AlignCenter)
        state_layout.addWidget(title_label, 0, Qt.AlignCenter)
        state_layout.addWidget(caption_label, 0, Qt.AlignCenter)
        return state

    def _create_preview_label(self, parent, min_width: int = 320, min_height: int = 220):
        label = QLabel(parent)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumSize(min_width, min_height)
        label.setStyleSheet('QLabel { border: 1px dashed rgba(120,120,120,0.45); border-radius: 14px; background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255,255,255,0.02), stop:1 rgba(47,141,99,0.05)); }')
        return label

    def _connect_signals(self):
        self.pickFileButton.clicked.connect(self.open_image)
        self.pickFolderButton.clicked.connect(self.open_folder)
        self.btn_go_result.clicked.connect(self.go_to_result_step)
        self.btn_back_file.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.fileInterface))
        self.btn_run.clicked.connect(self.run_ocr)
        self.btn_export.clicked.connect(self.export_results)
        self.btn_save_ledger.clicked.connect(self.save_to_ledger)
        self.fileList.currentRowChanged.connect(self.on_file_selection_changed)
        self.fileList.itemChanged.connect(self.on_file_check_changed)
        self.summary_table.itemSelectionChanged.connect(self.on_summary_selection_changed)
        self.selectAllButton.clicked.connect(self.select_all_files)
        self.clearSelectionButton.clicked.connect(self.clear_checked_files)
        for widget in [self.resultInterface, self.summary_table, self.result_table, self.raw_text, self.resultPreviewStack, self.resultImageLabel]:
            widget.installEventFilter(self)

    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text, onClick=lambda: self.stackedWidget.setCurrentWidget(widget))

    def onCurrentIndexChanged(self, index: int):
        widget = self.stackedWidget.widget(index)
        if widget:
            self.pivot.setCurrentItem(widget.objectName())

    def resizeEvent(self, event):
        self._update_result_detail_layout()
        if self.file_preview_path:
            self._show_preview(self.previewStack, self.previewEmptyState, self.image_label, self.previewNamePill, self.previewSizePill, self.previewIndexPill, self.file_preview_path)
        if self.result_preview_path:
            self._show_preview(self.resultPreviewStack, self.resultPreviewEmptyState, self.resultImageLabel, self.resultPreviewNamePill, self.resultPreviewSizePill, self.resultPreviewIndexPill, self.result_preview_path)
        super().resizeEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if self.stackedWidget.currentWidget() is self.fileInterface and self.image_paths:
            current_row = self.fileList.currentRow()
            if event.key() == Qt.Key_Left and current_row > 0:
                self.fileList.setCurrentRow(current_row - 1)
                return
            if event.key() == Qt.Key_Right and current_row < len(self.image_paths) - 1:
                self.fileList.setCurrentRow(current_row + 1)
                return
        if self._handle_result_navigation_key(event.key()):
            return
        super().keyPressEvent(event)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and isinstance(event, QKeyEvent):
            if self._handle_result_navigation_key(event.key()):
                return True
        return super().eventFilter(watched, event)

    def _handle_result_navigation_key(self, key: int) -> bool:
        if self.stackedWidget.currentWidget() is not self.resultInterface or not self.batch_results:
            return False

        current_row = self.summary_table.currentRow()
        if current_row < 0:
            current_row = self.current_result_index

        if key == Qt.Key_Left and current_row > 0:
            self.summary_table.setCurrentCell(current_row - 1, 0)
            self.summary_table.selectRow(current_row - 1)
            self._render_result_detail(current_row - 1)
            return True

        if key == Qt.Key_Right and current_row < len(self.batch_results) - 1:
            self.summary_table.setCurrentCell(current_row + 1, 0)
            self.summary_table.selectRow(current_row + 1)
            self._render_result_detail(current_row + 1)
            return True

        return False

    def _entry_style(self, active: bool) -> str:
        if active:
            return 'QWidget { border: 1px solid rgba(47, 141, 99, 0.88); border-radius: 22px; background-color: rgba(47, 141, 99, 0.10); }'
        return 'QWidget { border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 22px; background-color: rgba(255, 255, 255, 0.015); }'

    def _update_result_detail_layout(self):
        compact = self.width() < 1280
        if compact == self.resultDetailCompact:
            return

        self.resultDetailCompact = compact
        if compact:
            self.detailSplitRow.setDirection(QBoxLayout.TopToBottom)
            self.detailSplitRow.setStretch(0, 1)
            self.detailSplitRow.setStretch(1, 1)
        else:
            self.detailSplitRow.setDirection(QBoxLayout.LeftToRight)
            self.detailSplitRow.setStretch(0, 5)
            self.detailSplitRow.setStretch(1, 5)

    def _apply_drop_highlight(self, active: bool):
        self.entryCard.setStyleSheet(self._entry_style(active))
        self.dropHintLabel.setText('松开鼠标即可导入发票文件或文件夹。' if active else '拖拽发票图片、PDF 电子发票或文件夹到这里，或使用右侧按钮导入。')

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
        file_paths = [str(path) for path in local_paths if path.is_file() and path.suffix.lower() in self.SUPPORTED_FILE_SUFFIXES]
        if file_paths:
            self._load_selected_images(file_paths, '拖拽导入', 'single' if len(file_paths) == 1 else 'folder')
            return
        QMessageBox.warning(self, '提示', '拖拽内容中没有可识别的图片或 PDF 文件。')

    def _checked_image_paths(self) -> list[str]:
        checked = []
        for row in range(self.fileList.count()):
            item = self.fileList.item(row)
            if item and item.checkState() == Qt.Checked and item.data(Qt.UserRole):
                checked.append(item.data(Qt.UserRole))
        return checked

    def _refresh_processing_scope(self):
        checked = self._checked_image_paths()
        self.processing_image_paths = checked or list(self.image_paths)
        self.fileSelectionPill.setText(f'处理范围：已勾选 {len(checked)} 个文件' if checked else '处理范围：全部文件')
        self.processingCountLabel.setText(f'本次将处理 {len(self.processing_image_paths)} 个文件')
        self._sync_result_summary()

    def _sync_result_summary(self):
        total_loaded = len(self.image_paths)
        total_processing = len(self.processing_image_paths or self.image_paths)
        if not self.current_image_path:
            self.resultFileLabel.setText('当前文件：未选择')
        elif self.input_mode == 'folder':
            self.resultFileLabel.setText(f'当前来源：文件夹，共 {total_loaded} 个文件，本次处理 {total_processing} 个')
        else:
            self.resultFileLabel.setText(f'当前文件：{self.current_image_path}')
        self.resultConfigLabel.setText('当前配置：' + f"引擎 {self.config.get('ocr.engine', 'paddleocr')} | 语言 {self.config.get('ocr.lang', 'ch')} | GPU {'开启' if self.config.get('ocr.use_gpu', False) else '关闭'} | 调试图 {'保存' if self.config.get('ocr.save_debug_image', True) else '不保存'}")

    def _reset_results(self):
        self.batch_results = []
        self.current_result_index = 0
        self.result_table.setRowCount(0)
        self.summary_table.setRowCount(0)
        self.raw_text.clear()
        self.btn_export.setEnabled(False)
        self.btn_save_ledger.setEnabled(False)
        self.btn_run.setEnabled(bool(self.image_paths))
        self.resultStatePill.setText('等待识别')
        self.resultProgressPill.setText('待识别')
        total = len(self.processing_image_paths or self.image_paths)
        self.resultProgressInfoLabel.setText(f'当前进度：0 / {total}')
        self.resultProgressBar.setValue(0)
        self._show_preview(self.previewStack, self.previewEmptyState, self.image_label, self.previewNamePill, self.previewSizePill, self.previewIndexPill, '')
        self._show_preview(self.resultPreviewStack, self.resultPreviewEmptyState, self.resultImageLabel, self.resultPreviewNamePill, self.resultPreviewSizePill, self.resultPreviewIndexPill, '')

    def _show_preview(self, stack, empty_state, label, name_pill, size_pill, index_pill, image_path: str):
        if not image_path:
            if stack is self.previewStack:
                self.file_preview_path = ''
            elif stack is self.resultPreviewStack:
                self.result_preview_path = ''
            stack.setCurrentWidget(empty_state)
            name_pill.setText('文件：-')
            size_pill.setText('尺寸：-')
            index_pill.setText('位置：-')
            return
        if stack is self.previewStack:
            self.file_preview_path = image_path
        elif stack is self.resultPreviewStack:
            self.result_preview_path = image_path
        preview_path = image_path
        if Path(image_path).suffix.lower() == '.pdf':
            try:
                preview_path = self.pdf_renderer.render_preview_file(image_path)
            except Exception:
                preview_path = ''
        pixmap = QPixmap(preview_path) if preview_path else QPixmap()
        name_pill.setText(f'文件：{Path(image_path).name}')
        image_index = self.image_paths.index(image_path) + 1 if image_path in self.image_paths else 1
        index_pill.setText(f'位置：{image_index}/{len(self.image_paths) if self.image_paths else 1}')
        if pixmap.isNull():
            label.clear()
            stack.setCurrentWidget(empty_state)
            size_pill.setText('尺寸：预览读取失败')
            return
        target_width = max(280, label.contentsRect().width() - 8)
        target_height = max(220, label.contentsRect().height() - 8)
        label.setPixmap(pixmap.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        stack.setCurrentWidget(label)
        size_pill.setText(f'尺寸：{pixmap.width()} x {pixmap.height()}')

    def _populate_file_list(self):
        self.fileList.blockSignals(True)
        self.fileList.clear()
        for index, path in enumerate(self.image_paths, start=1):
            item = QListWidgetItem(f'{index:02d}. {Path(path).name}')
            item.setToolTip(path)
            item.setData(Qt.UserRole, path)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.fileList.addItem(item)
        self.fileList.blockSignals(False)
        if self.image_paths:
            self.fileList.setCurrentRow(0)
        else:
            self._show_preview(self.previewStack, self.previewEmptyState, self.image_label, self.previewNamePill, self.previewSizePill, self.previewIndexPill, '')
        self._refresh_processing_scope()

    def _load_selected_images(self, image_paths: list[str], source: str, mode: str):
        self.input_mode = 'folder' if mode == 'folder' or len(image_paths) > 1 else 'single'
        self.input_source = source
        self.image_paths = image_paths
        self.processing_image_paths = list(image_paths)
        self.current_image_path = image_paths[0] if image_paths else None
        self.sourceInput.setText(source)
        self.btn_go_result.setEnabled(bool(image_paths))
        self.btn_run.setEnabled(bool(image_paths))
        if self.input_mode == 'folder':
            self.filePathLabel.setText(f'当前来源：{source}')
            self.fileStatePill.setText(f'已加载 {len(image_paths)} 个文件')
            self.fileModePill.setText('当前模式：文件夹')
        else:
            self.filePathLabel.setText(f'当前文件：{source}')
            self.fileStatePill.setText('已加载 1 个文件')
            self.fileModePill.setText('当前模式：单个文件')
        self.fileCountPill.setText(f'文件数量：{len(image_paths)}')
        self._reset_results()
        self._populate_file_list()
        self.setFocus()

    def _load_folder(self, folder_path: Path):
        file_paths = [str(path) for path in sorted(folder_path.iterdir()) if path.is_file() and path.suffix.lower() in self.SUPPORTED_FILE_SUFFIXES]
        if not file_paths:
            QMessageBox.warning(self, '提示', '该文件夹中没有可识别的图片或 PDF 文件。')
            return
        self._load_selected_images(file_paths, str(folder_path), 'folder')

    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择发票文件', '', 'Invoice Files (*.png *.jpg *.jpeg *.bmp *.webp *.pdf)')
        if file_path:
            self._load_selected_images([file_path], file_path, 'single')

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, '选择发票文件夹', '')
        if folder_path:
            self._load_folder(Path(folder_path))

    def on_file_selection_changed(self, row: int):
        if 0 <= row < len(self.image_paths):
            self.current_image_path = self.image_paths[row]
            self._show_preview(self.previewStack, self.previewEmptyState, self.image_label, self.previewNamePill, self.previewSizePill, self.previewIndexPill, self.current_image_path)
            if not self.batch_results:
                self._show_preview(self.resultPreviewStack, self.resultPreviewEmptyState, self.resultImageLabel, self.resultPreviewNamePill, self.resultPreviewSizePill, self.resultPreviewIndexPill, self.current_image_path)
            self._sync_result_summary()

    def on_file_check_changed(self, _item):
        self._refresh_processing_scope()

    def select_all_files(self):
        self.fileList.blockSignals(True)
        for row in range(self.fileList.count()):
            item = self.fileList.item(row)
            if item:
                item.setCheckState(Qt.Checked)
        self.fileList.blockSignals(False)
        self._refresh_processing_scope()

    def clear_checked_files(self):
        self.fileList.blockSignals(True)
        for row in range(self.fileList.count()):
            item = self.fileList.item(row)
            if item:
                item.setCheckState(Qt.Unchecked)
        self.fileList.blockSignals(False)
        self._refresh_processing_scope()

    def go_to_result_step(self):
        if not self.image_paths:
            QMessageBox.warning(self, '提示', '请先选择图片或文件夹。')
            return
        self._refresh_processing_scope()
        self.stackedWidget.setCurrentWidget(self.resultInterface)
        self.pivot.setCurrentItem('ResultInterface')
        self._show_preview(self.resultPreviewStack, self.resultPreviewEmptyState, self.resultImageLabel, self.resultPreviewNamePill, self.resultPreviewSizePill, self.resultPreviewIndexPill, self.current_image_path or '')
    def run_ocr(self):
        target_paths = list(self.processing_image_paths or self.image_paths)
        if not target_paths:
            QMessageBox.warning(self, '提示', '请先选择图片或文件夹。')
            return
        self.stackedWidget.setCurrentWidget(self.resultInterface)
        self.pivot.setCurrentItem('ResultInterface')
        self.thread = QThread()
        self.worker = InvoiceOCRWorker(target_paths, self.config)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.btn_run.setEnabled(False)
        self.resultStatePill.setText('识别中...')
        self.resultProgressPill.setText('识别中')
        self.resultProgressInfoLabel.setText(f'当前进度：0 / {len(target_paths)}')
        self.resultProgressBar.setValue(0)
        self.thread.start()

    def on_progress(self, index: int, message: str):
        total = len(self.processing_image_paths or self.image_paths)
        progress = int(index / total * 100) if total else 0
        self.resultProgressPill.setText(f'{message} ({index}/{total})' if total > 1 else message)
        self.resultProgressInfoLabel.setText(f'当前进度：{index} / {total}')
        self.resultProgressBar.setValue(progress)

    def _render_summary_table(self):
        self.summary_table.setRowCount(len(self.batch_results))
        for row, result in enumerate(self.batch_results):
            file_name = Path(result.source_file).name if result.source_file else f'第 {row + 1} 项'
            status = '待复核' if result.errors else '通过'
            values = [file_name, result.invoice_number or '', status, str(len(result.errors))]
            for column, value in enumerate(values):
                self.summary_table.setItem(row, column, QTableWidgetItem(value))

    def _render_result_detail(self, index: int):
        if not self.batch_results or not 0 <= index < len(self.batch_results):
            return
        self.current_result_index = index
        result = self.batch_results[index]
        rows = result.display_rows()
        self.result_table.setRowCount(len(rows))
        for row, (key, value) in enumerate(rows):
            self.result_table.setItem(row, 0, QTableWidgetItem(key))
            self.result_table.setItem(row, 1, QTableWidgetItem(value))
        self.raw_text.setPlainText('\n'.join(result.raw_texts))
        self._show_preview(self.resultPreviewStack, self.resultPreviewEmptyState, self.resultImageLabel, self.resultPreviewNamePill, self.resultPreviewSizePill, self.resultPreviewIndexPill, result.source_file or '')
        self.summary_table.selectRow(index)

    def on_finished(self, results: list[InvoiceOCRResult]):
        self.batch_results = results
        self.btn_run.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.btn_save_ledger.setEnabled(True)
        self.resultStatePill.setText(f'已生成 {len(results)} 条识别结果')
        self.resultProgressPill.setText('识别完成')
        self.resultProgressInfoLabel.setText(f'当前进度：{len(results)} / {len(results)}')
        self.resultProgressBar.setValue(100)
        self._render_summary_table()
        if results:
            self._render_result_detail(0)
        InfoBar.success('识别完成', f'已完成 {len(results)} 个文件的识别，现在可以查看汇总、预览、导出或批量入账。', orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2200, parent=self.window())

    def on_failed(self, message: str):
        self.btn_run.setEnabled(True)
        self.resultStatePill.setText('识别失败')
        self.resultProgressPill.setText('识别失败')
        total = len(self.processing_image_paths or self.image_paths)
        current = min(max(int(self.resultProgressBar.value() * total / 100), 0), total) if total else 0
        self.resultProgressInfoLabel.setText(f'当前进度：{current} / {total}')
        QMessageBox.critical(self, '识别失败', message)

    def on_summary_selection_changed(self):
        selected = self.summary_table.selectedItems()
        if selected:
            self._render_result_detail(selected[0].row())

    def _export_base_name(self) -> str:
        if len(self.batch_results) == 1:
            return Path(self.batch_results[0].source_file or 'invoice').stem
        return Path(self.input_source or 'invoice_batch').stem

    def _export_headers(self) -> list[tuple[str, str]]:
        return [
            ('source_file', '来源文件'),
            ('invoice_type', '发票类型'),
            ('invoice_number', '发票号码'),
            ('invoice_date', '开票日期'),
            ('buyer_name', '购买方'),
            ('buyer_tax_id', '购买方税号'),
            ('seller_name', '销售方'),
            ('seller_tax_id', '销售方税号'),
            ('item_name', '项目名称'),
            ('unit', '单位'),
            ('quantity', '数量'),
            ('unit_price', '单价'),
            ('tax_rate', '税率/征收率'),
            ('amount_without_tax', '不含税金额'),
            ('tax_amount', '税额'),
            ('amount_with_tax', '价税合计'),
            ('amount_with_tax_cn', '价税合计大写'),
            ('issuer', '开票人'),
            ('remark', '备注'),
            ('check_code', '校验码'),
            ('confidence', '置信度'),
            ('status', '状态'),
            ('error_count', '错误数'),
            ('errors', '错误信息'),
            ('raw_text', '原始文本'),
        ]

    def _export_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for result in self.batch_results:
            rows.append({
                'source_file': result.source_file or '',
                'invoice_type': result.invoice_type or '',
                'invoice_number': result.invoice_number or '',
                'invoice_date': result.invoice_date or '',
                'buyer_name': result.buyer_name or '',
                'buyer_tax_id': result.buyer_tax_id or '',
                'seller_name': result.seller_name or '',
                'seller_tax_id': result.seller_tax_id or '',
                'item_name': result.item_name or '',
                'unit': result.unit or '',
                'quantity': '' if result.quantity is None else str(result.quantity),
                'unit_price': '' if result.unit_price is None else str(result.unit_price),
                'tax_rate': result.tax_rate or '',
                'amount_without_tax': '' if result.amount_without_tax is None else str(result.amount_without_tax),
                'tax_amount': '' if result.tax_amount is None else str(result.tax_amount),
                'amount_with_tax': '' if result.amount_with_tax is None else str(result.amount_with_tax),
                'amount_with_tax_cn': InvoiceParser.extract_uppercase_amount(result.amount_with_tax_cn)
                or InvoiceParser.extract_uppercase_amount_from_lines(result.raw_texts)
                or '',
                'issuer': result.issuer or '',
                'remark': result.remark or '',
                'check_code': result.check_code or '',
                'confidence': '' if result.confidence is None else f'{result.confidence:.4f}',
                'status': '待复核' if result.errors else '通过',
                'error_count': str(len(result.errors)),
                'errors': '；'.join(result.errors),
                'raw_text': '\n'.join(result.raw_texts),
            })
        return rows

    @staticmethod
    def _xlsx_column_name(index: int) -> str:
        name = ''
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            name = chr(65 + remainder) + name
        return name

    def _write_json_export(self, save_path: str) -> None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        if len(self.batch_results) == 1:
            payload = self.batch_results[0].to_dict()
        else:
            payload = {
                'mode': self.input_mode,
                'source': self.input_source,
                'count': len(self.batch_results),
                'items': [result.to_dict() for result in self.batch_results],
            }
        Path(save_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    def _write_csv_export(self, save_path: str) -> None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        headers = self._export_headers()
        rows = self._export_rows()
        with open(save_path, 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=[key for key, _ in headers])
            writer.writerow({key: label for key, label in headers})
            writer.writerows(rows)

    def _write_xlsx_export(self, save_path: str) -> None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        headers = self._export_headers()
        rows = self._export_rows()
        sheet_rows = [[label for _, label in headers]]
        sheet_rows.extend([[row[key] for key, _ in headers] for row in rows])

        def cell_xml(value: str, row_index: int, col_index: int) -> str:
            cell_ref = f'{self._xlsx_column_name(col_index)}{row_index}'
            escaped = escape(value).replace('\n', '&#10;')
            return f'<c r="{cell_ref}" t="inlineStr"><is><t xml:space="preserve">{escaped}</t></is></c>'

        row_xml_parts: list[str] = []
        for row_index, row_values in enumerate(sheet_rows, start=1):
            cells = ''.join(cell_xml(str(value), row_index, col_index) for col_index, value in enumerate(row_values, start=1))
            row_xml_parts.append(f'<row r="{row_index}">{cells}</row>')
        sheet_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(row_xml_parts)}</sheetData>'
            '</worksheet>'
        )

        content_types_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '</Types>'
        )
        rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        )
        workbook_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="识别结果" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>'
        )
        workbook_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>'
        )
        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
            '</styleSheet>'
        )

        with zipfile.ZipFile(save_path, 'w', compression=zipfile.ZIP_DEFLATED) as workbook:
            workbook.writestr('[Content_Types].xml', content_types_xml)
            workbook.writestr('_rels/.rels', rels_xml)
            workbook.writestr('xl/workbook.xml', workbook_xml)
            workbook.writestr('xl/_rels/workbook.xml.rels', workbook_rels_xml)
            workbook.writestr('xl/styles.xml', styles_xml)
            workbook.writestr('xl/worksheets/sheet1.xml', sheet_xml)

    def export_results(self):
        if not self.batch_results:
            return
        base_name = self._export_base_name()
        export_dir = Path(self.config.get('storage.export_dir', 'data/export'))
        save_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            '导出识别结果',
            str(export_dir / f'{base_name}.xlsx'),
            'Excel Files (*.xlsx);;CSV Files (*.csv);;JSON Files (*.json)',
        )
        if not save_path:
            return

        path = Path(save_path)
        if selected_filter.startswith('Excel') and path.suffix.lower() != '.xlsx':
            path = path.with_suffix('.xlsx')
        elif selected_filter.startswith('CSV') and path.suffix.lower() != '.csv':
            path = path.with_suffix('.csv')
        elif selected_filter.startswith('JSON') and path.suffix.lower() != '.json':
            path = path.with_suffix('.json')

        if path.suffix.lower() == '.csv':
            self._write_csv_export(str(path))
            export_type = 'CSV'
        elif path.suffix.lower() == '.json':
            self._write_json_export(str(path))
            export_type = 'JSON'
        else:
            self._write_xlsx_export(str(path))
            export_type = 'Excel'

        InfoBar.success('导出成功', f'{export_type} 已导出到 {path}', orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2500, parent=self.window())

    def save_to_ledger(self):
        if not self.batch_results:
            QMessageBox.warning(self, '提示', '请先完成识别。')
            return
        success_count = 0
        duplicate_count = 0
        last_row_id = None
        for result in self.batch_results:
            ok, _, row_id = self.ledger_service.save_invoice_result(result, result.source_file or self.current_image_path or '')
            if ok:
                success_count += 1
                last_row_id = row_id
            else:
                duplicate_count += 1
        message = f'成功 {success_count} 条，跳过重复 {duplicate_count} 条'
        if last_row_id:
            message += f'，最后记录 ID: {last_row_id}'
        self.resultStatePill.setText('已批量保存到台账')
        InfoBar.success('保存完成', message, orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2800, parent=self.window())
