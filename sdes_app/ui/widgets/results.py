from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from .layout import button
from .tables import DataTable
from .disclosure import Disclosure


class BinaryResultEdit(QPlainTextEdit):
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.document().isEmpty():
            painter = QPainter(self.viewport())
            painter.setFont(QFont("Microsoft YaHei UI", 10))
            painter.setPen(QColor("#74839A"))
            painter.drawText(self.viewport().rect().adjusted(4, 0, -4, 0),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "计算后显示结果")


class ResultPanel(QWidget):
    def __init__(self, title: str, mono: bool = True, height: int = 80, hero=False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.label = QLabel(title)
        self.editor = BinaryResultEdit() if hero else QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setProperty("result", True)
        self.editor.setProperty("hero", hero)
        if not hero:
            self.editor.setPlaceholderText("解密后显示明文")
        self.editor.setAccessibleName(title)
        self.editor.setFixedHeight(height)
        if mono:
            self.editor.setFont(QFont("Consolas", 27 if hero else 12))
        self.copy_button = button("复制")
        self.copy_button.setProperty("quiet", True)
        self.copy_button.setAccessibleName("复制" + title)
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy)
        self.copy_status = QLabel()
        self.copy_status.setObjectName("hint")
        heading = QHBoxLayout()
        heading.addWidget(self.label, 1)
        heading.addWidget(self.copy_status)
        heading.addWidget(self.copy_button)
        layout.addLayout(heading)
        layout.addWidget(self.editor)

    def set_text(self, text: str):
        self.editor.setPlainText(text)
        self.copy_button.setEnabled(bool(text))
        self.copy_status.clear()

    def text(self):
        return self.editor.toPlainText()

    def copy(self):
        QApplication.clipboard().setText(self.text())
        self.copy_status.setText("已复制")


class TracePanel(Disclosure):
    def __init__(self):
        self.table = DataTable(("步骤", "位串", "说明"), weights=(1.1, 1.2, 2), minimums=(140, 150, 240))
        self.table.setFont(QFont("Microsoft YaHei UI", 9))
        super().__init__("计算步骤", self.table)

    def set_trace(self, trace):
        self.table.set_rows([(step.name, step.bits, step.detail) for step in trace.steps])
