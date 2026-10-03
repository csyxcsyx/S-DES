from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from sdes_app.core.bit_ops import parse_bits
from .layout import actions, button


class PairEditor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(("8 位明文", "8 位密文"))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(145)
        self.table.setAccessibleName("已知明密文对，双击或按 F2 编辑")
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.add_button = button("添加一对")
        self.remove_button = button("删除选中行")
        self.error = QLabel()
        self.error.setObjectName("error")
        self.error.setWordWrap(True)
        self.error.hide()
        layout.addWidget(self.table)
        layout.addLayout(actions(self.add_button, self.remove_button))
        layout.addWidget(self.error)
        self.add_button.clicked.connect(self.add_pair)
        self.remove_button.clicked.connect(self.remove_selected)
        self.table.itemChanged.connect(self.error.hide)
        self.add_pair("10011010", "11101111")

    def add_pair(self, plaintext="", ciphertext=""):
        # clicked(bool) 不能作为默认明文字符串使用。
        if isinstance(plaintext, bool):
            plaintext = ""
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, text in enumerate((plaintext, ciphertext)):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, column, item)

    def remove_selected(self):
        for row in sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(row)
        self.error.hide()

    def values(self):
        result = []
        try:
            if self.table.rowCount() == 0:
                raise ValueError("请至少添加一组明密文对。")
            for row in range(self.table.rowCount()):
                pair = []
                for column, name in enumerate(("明文", "密文")):
                    item = self.table.item(row, column)
                    try:
                        pair.append(parse_bits(item.text() if item else "", 8, f"第 {row + 1} 行{name}"))
                    except ValueError:
                        self.table.setCurrentCell(row, column)
                        self.table.setFocus()
                        raise
                result.append(tuple(pair))
        except ValueError as error:
            self.error.setText(str(error))
            self.error.show()
            raise
        return result
