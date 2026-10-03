from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget, QLayout

from ..motion import TRANSITION_MS, reduced_motion
from .layout import button


class Disclosure(QWidget):
    def __init__(self, title, content):
        super().__init__()
        self.title = title
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.toggle = button(f"展开{title}")
        self.toggle.setCheckable(True)
        self.toggle.setProperty("quiet", True)
        self.panel = QWidget()
        inner = QVBoxLayout(self.panel)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        inner.addWidget(content)
        self.content = content
        self.panel.setMaximumHeight(0)
        self.panel.hide()
        self.animation = QPropertyAnimation(self.panel, b"maximumHeight", self)
        self.animation.setDuration(TRANSITION_MS)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.finished.connect(self.settled)
        self.toggle.toggled.connect(self.set_expanded)
        layout.addWidget(self.toggle, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.panel)

    def set_expanded(self, expanded):
        self.animation.stop()
        self.toggle.setText(f"{'收起' if expanded else '展开'}{self.title}")
        height = max(self.content.minimumHeight(), self.content.sizeHint().height()) if expanded else 0
        self.panel.show()
        if reduced_motion():
            self.panel.setMaximumHeight(height)
            self.settled()
        else:
            self.animation.setStartValue(self.panel.height())
            self.animation.setEndValue(height)
            self.animation.start()

    def settled(self):
        if not self.toggle.isChecked():
            self.panel.hide()
        else:
            self.panel.setMaximumHeight(16777215)
