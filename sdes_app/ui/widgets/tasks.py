from threading import Event
from time import perf_counter

from PySide6.QtCore import QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from .layout import actions, button


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

    def __init__(self, start_text: str):
        super().__init__()
        self.worker = None
        self.cancel_event = Event()
        self._result = None
        self._error = ""
        self._started = 0.0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.start_button = button(start_text, True)
        self.cancel_button = button("取消")
        self.cancel_button.setEnabled(False)
        self.status = QLabel("尚未运行")
        self.status.setObjectName("hint")
        self.status.setWordWrap(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setAccessibleName("任务进度")
        self.progress_bar.setTextVisible(False)
        self.count = QLabel()
        self.count.setObjectName("hint")
        layout.addLayout(actions(self.start_button, self.cancel_button))
        layout.addWidget(self.progress_bar)
        status_row = QHBoxLayout()
        status_row.addWidget(self.status, 1)
        status_row.addWidget(self.count)
        layout.addLayout(status_row)
        self.cancel_button.clicked.connect(self.cancel)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.tick)

    @property
    def running(self):
        return self.worker is not None

    def start(self, function) -> bool:
        if self.running:
            return False
        self.cancel_event = Event()
        self._result, self._error = None, ""
        self._started = perf_counter()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.count.clear()
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.status.setText("运行中 · 0.000 秒")
        self.worker = Worker(function, self.cancel_event, self)
        self.worker.progress.connect(self.update_progress)
        self.worker.result.connect(self.receive_result)
        self.worker.error.connect(self.receive_error)
        self.worker.finished.connect(self.finish)
        self.timer.start()
        self.worker.start()
        return True

    @Slot(int, int)
    def update_progress(self, checked, total):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(checked)
        self.progress_bar.setFormat(f"{checked:,} / {total:,}")
        self.count.setText(f"已检查 {checked:,} / {total:,}")

    @Slot(object)
    def receive_result(self, result):
        self._result = result

    @Slot(str)
    def receive_error(self, error):
        self._error = error

    @Slot()
    def tick(self):
        state = "正在取消" if self.cancel_event.is_set() else "运行中"
        self.status.setText(f"{state} · {perf_counter() - self._started:.3f} 秒")

    @Slot()
    def cancel(self):
        if self.running:
            self.cancel_event.set()
            self.cancel_button.setEnabled(False)
            self.status.setText("正在取消，等待当前计算结束…")

    @Slot()
    def finish(self):
        # 等 finished 再释放线程和恢复操作，避免线程尚未退出就关闭窗口。
        worker, self.worker = self.worker, None
        self.timer.stop()
        worker.deleteLater()
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        if self._error:
            self.status.setText(f"任务失败：{self._error}")
            self.failed.emit(self._error)
        elif self._result is not None:
            completed = getattr(self._result, "completed", True)
            elapsed = getattr(self._result, "elapsed", perf_counter() - self._started)
            if completed:
                self.progress_bar.setValue(self.progress_bar.maximum())
            self.status.setText(f"{'已完成' if completed else '未完成 / 已取消'} · 实际耗时 {elapsed:.6f} 秒")
            self.succeeded.emit(self._result)
        self.idle.emit()
