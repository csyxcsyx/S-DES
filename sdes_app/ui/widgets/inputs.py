from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget

from sdes_app.core.bit_ops import parse_bits


class InputField(QWidget):
    def __init__(self, title: str, hint: str = "", multiline: bool = False, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.label = QLabel(title)
        self.editor = QPlainTextEdit() if multiline else QLineEdit()
        self.editor.setAccessibleName(title)
        self.label.setBuddy(self.editor)
        self.error = QLabel()
        self.error.setObjectName("error")
        self.error.setWordWrap(True)
        self.error.hide()
        layout.addWidget(self.label)
        layout.addWidget(self.editor)
        if hint:
            helper = QLabel(hint)
            helper.setObjectName("hint")
            helper.setWordWrap(True)
            layout.addWidget(helper)
        layout.addWidget(self.error)
        self.editor.textChanged.connect(self.clear_error)

    def text(self) -> str:
        return self.editor.toPlainText() if isinstance(self.editor, QPlainTextEdit) else self.editor.text()

    def set_text(self, text: str):
        if isinstance(self.editor, QPlainTextEdit):
            self.editor.setPlainText(text)
        else:
            self.editor.setText(text)

    def show_error(self, message: str):
        self.error.setText(message)
        self.error.show()
        self.editor.setProperty("invalid", True)
        self.editor.style().unpolish(self.editor)
        self.editor.style().polish(self.editor)
        self.editor.setFocus()

    def clear_error(self):
        self.error.hide()
        self.editor.setProperty("invalid", False)
        self.editor.style().unpolish(self.editor)
        self.editor.style().polish(self.editor)


class BitInput(InputField):
    def __init__(self, title: str, width: int, default: str = "", parent=None):
        super().__init__(title, f"恰好 {width} 位，仅接受 0 和 1；前导零会保留。", parent=parent)
        self.width = width
        self.editor.setFont(QFont("Consolas", 14))
        self.set_text(default)

    def value(self) -> int:
        try:
            return parse_bits(self.text(), self.width, self.label.text())
        except ValueError as error:
            self.show_error(str(error))
            raise
