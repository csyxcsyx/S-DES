from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QStyle, QStyleOptionButton, QStylePainter, QVBoxLayout, QWidget


class QuietButton(QPushButton):
    def paintEvent(self, event):
        option = QStyleOptionButton()
        self.initStyleOption(option)
        if not self.property("keyboardFocus"):
            option.state &= ~QStyle.StateFlag.State_HasFocus
        painter = QStylePainter(self)
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)


def button(text: str, primary: bool = False) -> QPushButton:
    result = QuietButton(text)
    result.setProperty("primary", primary)
    result.setCursor(Qt.CursorShape.PointingHandCursor)
    return result


def card(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(14)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    label = QLabel(title)
    label.setObjectName("section")
    layout.addWidget(label)
    return frame, layout


def actions(*widgets) -> QHBoxLayout:
    layout = QHBoxLayout()
    layout.setSpacing(10)
    for widget in widgets:
        layout.addWidget(widget)
    layout.addStretch()
    return layout


class Page(QWidget):
    def __init__(self, title: str, description: str):
        super().__init__()
        self.setObjectName("page")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(28, 24, 28, 24)
        self.body.setSpacing(18)
        heading = QLabel(title)
        heading.setObjectName("title")
        self.body.addWidget(heading)
        subtitle = QLabel(description)
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        self.body.addWidget(subtitle)

    def finish(self):
        self.body.addStretch()
