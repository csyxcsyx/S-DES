from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QApplication, QWidget


class FocusPolicy(QObject):
    """鼠标操作使用背景反馈；Tab 导航保留可见焦点。"""
    def eventFilter(self, watched, event):
        if isinstance(watched, QWidget):
            if event.type() == QEvent.Type.FocusIn:
                self.mark(watched, event.reason() in (
                    Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason,
                    Qt.FocusReason.ShortcutFocusReason))
            elif event.type() == QEvent.Type.FocusOut:
                self.mark(watched, False)
            elif event.type() == QEvent.Type.MouseButtonPress:
                focused = QApplication.focusWidget()
                if focused:
                    self.mark(focused, False)
        return False

    @staticmethod
    def mark(widget, value):
        if widget.property("keyboardFocus") != value:
            widget.setProperty("keyboardFocus", value)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
