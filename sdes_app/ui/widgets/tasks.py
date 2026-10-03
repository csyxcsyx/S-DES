from threading import Event
from time import perf_counter

from PySide6.QtCore import QThread, QTimer, Signal, Slot, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..motion import MIN_LOADING_MS, reduced_motion
from .layout import actions, button
from .loading import BusySpinner, SmoothProgressBar
from .metrics import elapsed_text


class Worker(QThread):
    progress = Signal(int, int)
    result = Signal(object)
    error = Signal(str)

    def __init__(self, function, cancel: Event, parent=None):
        super().__init__(parent)
        self.function = function
        self.cancel = cancel

    def run(self):
        try:
            self.result.emit(self.function(progress=self.progress.emit, cancel=self.cancel))
        except Exception as error:
            self.error.emit(str(error) or type(error).__name__)


class TaskPanel(QWidget):
    succeeded = Signal(object)
    failed = Signal(str)
    idle = Signal()

    def __init__(self, start_text: str, show_elapsed=True):
        super().__init__()
        self.worker = None
        self.cancel_event = Event()
        self._result = None
        self._error = ""
        self._started = 0.0
        self._busy = False
        self.show_elapsed = show_elapsed
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.start_button = button(start_text, True)
        self.cancel_button = button("取消")
        self.cancel_button.setEnabled(False)
        self.status = QLabel("就绪")
        self.status.setObjectName("hint")
        self.status.setWordWrap(True)
        self.progress_bar = SmoothProgressBar()
        self.spinner = BusySpinner()
        self.count = QLabel()
        self.count.setObjectName("hint")
        layout.addLayout(actions(self.start_button, self.cancel_button))
        layout.addWidget(self.progress_bar)
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.addWidget(self.spinner)
        status_row.addWidget(self.status, 1)
        status_row.addWidget(self.count)
        layout.addLayout(status_row)
        self.cancel_button.clicked.connect(self.cancel)
        self.presentation_timer = QTimer(self)
        self.presentation_timer.setSingleShot(True)
        self.presentation_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.presentation_timer.timeout.connect(self.publish)

    @property
    def running(self):
        return self._busy

    def start(self, function) -> bool:
        if self.running:
            return False
        self.cancel_event = Event()
        self._result, self._error = None, ""
        self._busy = True
        self._started = perf_counter()
        self.presentation_timer.stop()
        self.progress_bar.move_to(0, immediate=True)
        self.count.clear()
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.status.setText("计算中")
        self.spinner.start()
        self.worker = Worker(function, self.cancel_event, self)
        self.worker.progress.connect(self.update_progress)
        self.worker.result.connect(self.receive_result)
        self.worker.error.connect(self.receive_error)
        self.worker.finished.connect(self.finish)
        self.worker.start()
        return True

    @Slot(int, int)
    def update_progress(self, checked, total):
        self.progress_bar.move_to(round(checked / total * 1000) if total else 0)
        self.count.setText(f"{checked:,} / {total:,}")

    @Slot(object)
    def receive_result(self, result):
        self._result = result

    @Slot(str)
    def receive_error(self, error):
        self._error = error

    @Slot()
    def cancel(self):
        if self.running:
            self.cancel_event.set()
            self.cancel_button.setEnabled(False)
            self.status.setText("正在取消…")
            if self.worker is None:
                self.presentation_timer.stop()
                self.publish()

    @Slot()
    def finish(self):
        # 等 finished 再释放线程和恢复操作，避免线程尚未退出就关闭窗口。
        worker, self.worker = self.worker, None
        worker.deleteLater()
        self.cancel_button.setEnabled(False)
        completed = getattr(self._result, "completed", True)
        remaining = MIN_LOADING_MS - int((perf_counter() - self._started) * 1000)
        if remaining > 0 and not (self._error or self.cancel_event.is_set() or not completed or reduced_motion()):
            # 服务已经完成；短暂展示过渡，绝不把展示时长加入实际计算耗时。
            self.status.setText("结果就绪")
            self.presentation_timer.start(remaining)
        else:
            self.publish()

    @Slot()
    def publish(self):
        if not self._busy or self.worker is not None:
            return
        self._busy = False
        self.spinner.stop()
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        if self._error:
            self.status.setText(f"任务失败：{self._error}")
            self.failed.emit(self._error)
        elif self._result is not None:
            completed = getattr(self._result, "completed", True)
            elapsed = getattr(self._result, "elapsed", perf_counter() - self._started)
            if completed:
                self.progress_bar.move_to(1000, immediate=True)
            state = '已完成' if completed else '未完成 / 已取消'
            self.status.setText(state + (f" · 计算耗时 {elapsed_text(elapsed)}" if self.show_elapsed else ""))
            self.succeeded.emit(self._result)
        self.count.clear()
        self.idle.emit()
