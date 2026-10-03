from PySide6.QtWidgets import QComboBox, QFrame, QListView

from .tables import QuietDelegate


class StyledComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        view = QListView(self)
        view.setObjectName("comboOptions")
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setSpacing(2)
        view.setItemDelegate(QuietDelegate(view))
        self.setView(view)
        self.setMinimumWidth(140)
        self.setMaxVisibleItems(8)

    def showPopup(self):
        super().showPopup()
        popup = self.view().window()
        if isinstance(popup, QFrame):
            popup.setFrameShape(QFrame.Shape.NoFrame)
            popup.setStyleSheet("QFrame { background: white; border: none; border-radius: 7px; }")
