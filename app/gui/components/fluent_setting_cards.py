# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from qfluentwidgets import (
    ColorPickerButton,
    ComboBox,
    EditableComboBox,
    LineEdit,
    PlainTextEdit,
    SettingCard,
)


class ComboBoxSettingCard(SettingCard):
    currentTextChanged = Signal(str)

    def __init__(self, icon, title: str, content: str = "", items: Iterable[str] | None = None, parent=None):
        super().__init__(icon, title, content, parent)
        self.comboBox = ComboBox(self)
        self.comboBox.setMinimumWidth(320)
        for item in items or []:
            self.comboBox.addItem(item)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.comboBox.currentTextChanged.connect(self.currentTextChanged.emit)

    def setValue(self, value: str) -> None:
        self.comboBox.setCurrentText(value)

    def value(self) -> str:
        return self.comboBox.currentText().strip()


class LineEditSettingCard(SettingCard):
    textChanged = Signal(str)

    def __init__(self, icon, title: str, content: str = "", placeholder: str = "", parent=None):
        super().__init__(icon, title, content, parent)
        self.lineEdit = LineEdit(self)
        self.lineEdit.setPlaceholderText(placeholder)
        self.lineEdit.setMinimumWidth(320)
        self.hBoxLayout.addWidget(self.lineEdit, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.lineEdit.textChanged.connect(self.textChanged.emit)

    def setValue(self, value: str) -> None:
        self.lineEdit.setText(value)

    def value(self) -> str:
        return self.lineEdit.text().strip()


class EditComboBoxSettingCard(SettingCard):
    currentTextChanged = Signal(str)

    def __init__(self, icon, title: str, content: str = "", items: Iterable[str] | None = None, parent=None):
        super().__init__(icon, title, content, parent)
        self.comboBox = EditableComboBox(self)
        self.comboBox.setMinimumWidth(320)
        for item in items or []:
            self.comboBox.addItem(item)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.comboBox.currentTextChanged.connect(self.currentTextChanged.emit)

    def setValue(self, value: str) -> None:
        self.comboBox.setText(value)

    def value(self) -> str:
        return self.comboBox.currentText().strip()

    def setItems(self, items: Iterable[str]) -> None:
        self.comboBox.clear()
        for item in items:
            self.comboBox.addItem(item)


class TextEditSettingCard(SettingCard):
    textChanged = Signal(str)

    def __init__(self, icon, title: str, content: str = "", placeholder: str = "", parent=None, height: int = 112):
        super().__init__(icon, title, content, parent)
        self.setFixedHeight(max(self.height(), height + 30))
        self.textEdit = PlainTextEdit(self)
        self.textEdit.setPlaceholderText(placeholder)
        self.textEdit.setFixedSize(320, height)
        self.hBoxLayout.addWidget(self.textEdit, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.textEdit.textChanged.connect(lambda: self.textChanged.emit(self.textEdit.toPlainText()))

    def setValue(self, value: str) -> None:
        self.textEdit.setPlainText(value)

    def value(self) -> str:
        return self.textEdit.toPlainText().strip()


class ColorSettingCard(SettingCard):
    colorChanged = Signal(str)

    def __init__(self, icon, title: str, content: str = "", color: str = "#2dd36f", parent=None):
        super().__init__(icon, title, content, parent)
        self.button = ColorPickerButton(QColor(color), "选择颜色", self, enableAlpha=False)
        self.button.setMinimumWidth(132)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.button.colorChanged.connect(self._on_color_changed)

    def _on_color_changed(self, color: QColor) -> None:
        self.colorChanged.emit(color.name())

    def setValue(self, value: str) -> None:
        self.button.setColor(QColor(value))

    def value(self) -> str:
        return self.button.color.name()
