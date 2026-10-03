from time import perf_counter

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QProgressBar, QWidget

from ..motion import PROGRESS_MS, SPINNER_CYCLE_MS, reduced_motion


class BusySpinner(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(20, 20)
        self.setAccessibleName("任务处理中")
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.update)
        self.started = 0.0
        self.hide()

    def start(self):
        self.started = perf_counter()
        self.show()
        if not reduced_motion():
            self.timer.start()

    def stop(self):
        self.timer.stop()
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(3, 3, 14, 14)
        painter.setPen(QPen(QColor("#E2EAF7"), 2.5))
        painter.drawEllipse(rect)
        painter.setPen(QPen(QColor("#215AC5"), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        angle = 90 if reduced_motion() else 90 - (perf_counter() - self.started) * 360000 / SPINNER_CYCLE_MS
        painter.drawArc(rect, int(angle * 16), 110 * 16)


class SmoothProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setRange(0, 1000)
        self.setValue(0)
        self.setTextVisible(False)
        self.setFixedHeight(4)
        self.setAccessibleName("任务进度")
        self.animation = QPropertyAnimation(self, b"value", self)
        self.animation.setDuration(PROGRESS_MS)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def move_to(self, value, immediate=False):
        self.animation.stop()
        if immediate or reduced_motion():
            self.setValue(value)
        else:
            self.animation.setStartValue(self.value())
            self.animation.setEndValue(value)
            self.animation.start()
