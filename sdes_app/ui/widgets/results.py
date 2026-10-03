from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QHeaderView, QLabel, QPlainTextEdit, QTableView, QVBoxLayout, QWidget

from .layout import actions, button


class RowsModel(QAbstractTableModel):
    def __init__(self, headers, rows, parent=None):
        super().__init__(parent)
        self.headers = headers
        self.rows = rows

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return str(self.rows[index.row()][index.column()])
        if role == Qt.ItemDataRole.FontRole:
            text = str(self.rows[index.row()][index.column()])
            if len(text) in (4, 8, 10) and set(text) <= {"0", "1"}:
                return QFont("Consolas", 11)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return self.headers[section] if orientation == Qt.Orientation.Horizontal else str(section + 1)
        return None


class DataTable(QTableView):
    def __init__(self, headers, minimum_height=160):
        super().__init__()
        self.setMinimumHeight(minimum_height)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setDefaultSectionSize(32)
        self.verticalHeader().hide()
        self.set_rows(headers, [])

    def set_rows(self, headers, rows):
        old = self.model()
        self.setModel(RowsModel(tuple(headers), tuple(tuple(row) for row in rows), self))
        if old:
            old.deleteLater()


class ResultPanel(QWidget):
    def __init__(self, title: str, mono: bool = True, height: int = 80):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.label = QLabel(title)
        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setAccessibleName(title)
        self.editor.setFixedHeight(height)
        if mono:
            self.editor.setFont(QFont("Consolas", 12))
        self.copy_button = button("复制结果")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy)
        self.copy_status = QLabel()
        self.copy_status.setObjectName("hint")
        layout.addWidget(self.label)
        layout.addWidget(self.editor)
        layout.addLayout(actions(self.copy_button, self.copy_status))

    def set_text(self, text: str):
        self.editor.setPlainText(text)
        self.copy_button.setEnabled(bool(text))
        self.copy_status.clear()

    def text(self):
        return self.editor.toPlainText()

    def copy(self):
        QApplication.clipboard().setText(self.text())
        self.copy_status.setText("已复制")


class TracePanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.toggle = button("展开计算步骤")
        self.toggle.setCheckable(True)
        self.table = DataTable(("步骤", "位串", "说明"), 300)
        self.table.setFont(QFont("Microsoft YaHei UI", 9))
        self.table.hide()
        self.toggle.toggled.connect(self.set_expanded)
        layout.addWidget(self.toggle, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.table)

    def set_expanded(self, expanded):
        self.table.setVisible(expanded)
        self.toggle.setText("收起计算步骤" if expanded else "展开计算步骤")

    def set_trace(self, trace):
        self.table.set_rows(("步骤", "位串", "说明"), [(step.name, step.bits, step.detail) for step in trace.steps])
