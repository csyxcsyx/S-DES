"""统一表格绘制、数据模型和尺寸管理。"""
from PySide6.QtCore import QAbstractTableModel, QEvent, QModelIndex, QObject, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QAbstractItemView, QFrame, QHeaderView, QStyle, QStyledItemDelegate, QStyleOptionViewItem, QTableView, QTabWidget

HEADER_HEIGHT = 42
ROW_HEIGHT = 44


class QuietDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        clean = QStyleOptionViewItem(option)
        clean.state &= ~QStyle.StateFlag.State_HasFocus
        super().paint(painter, clean, index)


class TableDelegate(QuietDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        painter.save()
        painter.setPen(QColor("#E8EDF5"))
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        if index.column() == 0 and option.state & QStyle.StateFlag.State_Selected and self.parent().property("keyboardFocus"):
            painter.fillRect(option.rect.x(), option.rect.y() + 10, 2, option.rect.height() - 20, QColor("#215AC5"))
        painter.restore()


class TableLayout(QObject):
    changed = Signal()

    def __init__(self, table, visible_rows, weights=None, minimums=None):
        super().__init__(table)
        self.table, self.visible_rows = table, visible_rows
        self.weights, self.minimums = weights, minimums
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fit)
        table.installEventFilter(self)
        table.viewport().installEventFilter(self)
        for signal in (table.model().modelReset, table.model().rowsInserted,
                       table.model().rowsRemoved, table.model().dataChanged):
            signal.connect(self.schedule)
        self.schedule()

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.FontChange):
            self.schedule()
        return False

    def schedule(self, *args):
        self.timer.start(0)

    def fit(self):
        table = self.table
        count = table.model().columnCount()
        metrics = table.horizontalHeader().fontMetrics()
        minimums = self.minimums or tuple(max(110, metrics.horizontalAdvance(str(
            table.model().headerData(i, Qt.Orientation.Horizontal))) + 32) for i in range(count))
        weights = self.weights or (1,) * count
        extra = max(0, table.viewport().width() - sum(minimums))
        for column in range(count):
            width = minimums[column] + int(extra * weights[column] / sum(weights))
            if table.columnWidth(column) != width:
                table.setColumnWidth(column, width)
        table.resizeRowsToContents()
        rows = table.model().rowCount()
        body = sum(table.rowHeight(i) for i in range(min(rows, self.visible_rows))) if rows else 72
        horizontal = table.horizontalHeader().length() > table.viewport().width()
        height = HEADER_HEIGHT + body + (table.horizontalScrollBar().sizeHint().height() if horizontal else 0) + 2
        if table.height() != height:
            table.setFixedHeight(height)
            self.changed.emit()


def configure_table(table, editable=False, visible_rows=6, weights=None, minimums=None):
    table.setFrameShape(QFrame.Shape.NoFrame)
    table.setShowGrid(False)
    table.setAlternatingRowColors(False)
    table.setCornerButtonEnabled(False)
    table.verticalHeader().hide()
    table.setWordWrap(True)
    table.setTextElideMode(Qt.TextElideMode.ElideNone)
    table.verticalHeader().setMinimumSectionSize(ROW_HEIGHT)
    table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
    header = table.horizontalHeader()
    header.setFixedHeight(HEADER_HEIGHT)
    header.setHighlightSections(False)
    header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.verticalScrollBar().setProperty("tableScroll", True)
    table.setItemDelegate(TableDelegate(table))
    if not editable:
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.sizing = TableLayout(table, visible_rows, weights, minimums)


class RowsModel(QAbstractTableModel):
    def __init__(self, headers, parent):
        super().__init__(parent)
        self.headers, self.rows = tuple(headers), ()
        self.mono = QFont("Consolas", 11)

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        text = str(self.rows[index.row()][index.column()])
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return text
        if role == Qt.ItemDataRole.FontRole:
            tokens = text.split()
            if tokens and all(len(token) in (4, 8, 10) and set(token) <= {"0", "1"} for token in tokens):
                return self.mono
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return (Qt.AlignmentFlag.AlignCenter if text.isdecimal() else
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return self.headers[section]
        return None

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = tuple(tuple(row) for row in rows)
        self.endResetModel()


class DataTable(QTableView):
    def __init__(self, headers, visible_rows=6, weights=None, minimums=None):
        super().__init__()
        self.setModel(RowsModel(headers, self))
        configure_table(self, visible_rows=visible_rows, weights=weights, minimums=minimums)

    def set_rows(self, rows):
        self.model().set_rows(rows)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.model().rowCount():
            painter = QPainter(self.viewport())
            painter.setPen(QColor("#74839A"))
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")


class TableTabs(QTabWidget):
    def __init__(self, *tabs):
        super().__init__()
        for title, table in tabs:
            self.addTab(table, title)
            table.sizing.changed.connect(self.fit)
        self.currentChanged.connect(self.fit)
        self.fit()

    def fit(self, *args):
        self.setFixedHeight(self.currentWidget().height() + self.tabBar().sizeHint().height() + 8)
