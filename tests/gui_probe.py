"""在独立 Qt 进程中验证缩放、表格几何及翻页重绘。"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QStyle, QStyleOptionSlider
from PySide6.QtTest import QTest
from sdes_app.ui.main_window import MainWindow
from sdes_app.ui.theme import apply_theme
from sdes_app.services.experiments import analyze_collisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    app = QApplication([])
    apply_theme(app)
    window = MainWindow()
    window.resize(880, 600)
    window.show()
    errors = []
    sys.excepthook = lambda kind, error, trace: errors.append(str(error))
    for index in (1, 0, 2, 1, 2):
        window.navigation.setCurrentRow(index)
        QTest.qWait(10)
    table = window.pages[2].pairs.table
    assert window.stack.graphicsEffect() is None
    assert table.visualRect(table.model().index(0, 0)).bottom() < table.viewport().height()
    header = table.horizontalHeader().grab().toImage()
    dpr = header.devicePixelRatio()
    assert header.pixelColor(int(30 * dpr), int(8 * dpr)).name() == "#f3f6fa"
    window.navigation.setCurrentRow(3)
    collision = window.pages[3]
    collision.show_result(analyze_collisions(154))
    collision.tabs.setCurrentIndex(1)
    QTest.qWait(80)
    table = collision.groups
    row = max(range(table.model().rowCount()), key=lambda i: len(table.model().rows[i][2]))
    assert table.rowHeight(row) > 44, "长候选列表必须自动换行"
    scrollbar = table.verticalScrollBar()
    option = QStyleOptionSlider()
    scrollbar.initStyleOption(option)
    groove = scrollbar.style().subControlRect(QStyle.ComplexControl.CC_ScrollBar, option,
                                               QStyle.SubControl.SC_ScrollBarGroove, scrollbar)
    assert groove.top() >= table.horizontalHeader().height(), "滚动轨道应从表体开始"
    scrollbar.setValue(scrollbar.maximum())
    last = table.model().index(table.model().rowCount() - 1, 0)
    assert table.visualRect(last).bottom() < table.viewport().height(), "最后一行必须能完整滚动到视口内"
    window.navigation.setCurrentRow(4)
    cross = window.pages[4].cross_table
    cross.set_rows([(2, "10011010", "1010000010", "11101111", "11101111", "10011010", "通过")])
    QTest.qWait(80)
    assert cross.horizontalScrollBar().maximum() > 0
    assert cross.horizontalScrollBar().height() == 10
    assert cross.columnWidth(2) >= 130
    assert cross.visualRect(cross.model().index(0, 0)).bottom() < cross.viewport().height()
    assert not window.windowIcon().pixmap(16, 16).isNull()
    assert not errors, errors
    if options.output:
        options.output.mkdir(parents=True, exist_ok=True)
        window.resize(1120, 900)
        for index, name in ((2, "attack"), (3, "groups"), (4, "cross")):
            window.navigation.setCurrentRow(index)
            QTest.qWait(80)
            window.grab().save(str(options.output / f"11-{name}-150.png"))
    print(f"缩放 {os.environ.get('QT_SCALE_FACTOR', '1')}：完整行、列宽、长文本、滚动条、重绘、图标通过")
    window.close()


if __name__ == "__main__":
    main()
