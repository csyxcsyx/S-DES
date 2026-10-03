"""渲染实际 Qt 窗口，并通过应用自身操作生成可复现的报告截图。"""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from sdes_app.ui.main_window import MainWindow
from sdes_app.ui.theme import apply_theme


def wait_for(app, task):
    deadline = time.perf_counter() + 15
    while task.running and time.perf_counter() < deadline:
        app.processEvents()
        QTest.qWait(5)
    if task.running:
        task.cancel()
        raise RuntimeError("截图任务超时。")
    app.processEvents()


def main():
    output = ROOT / "docs" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    apply_theme(app)
    window = MainWindow()
    window.resize(1120, 900)
    window.show()
    app.processEvents()
    binary, text, attack, collision, testing = window.pages
    binary.example()
    binary.trace.toggle.setChecked(True)
    text.encrypt()
    text.decrypt()
    attack.start()
    wait_for(app, attack.task)
    collision.all_plaintexts.setChecked(True)
    collision.start()
    wait_for(app, collision.task)
    testing.exhaustive.setChecked(True)
    testing.start_checks()
    wait_for(app, testing.task)
    names = ("01-binary", "02-ascii", "03-attack", "04-collisions", "05-testing")
    for index, name in enumerate(names):
        window.navigation.setCurrentRow(index)
        app.processEvents()
        QTest.qWait(20)
        path = output / f"{name}.png"
        if not window.grab().save(str(path)):
            raise RuntimeError(f"无法保存截图：{path}")
        print(path)
    window.resize(880, 600)
    for index, name in enumerate(names):
        window.navigation.setCurrentRow(index)
        app.processEvents()
        QTest.qWait(20)
        window.grab().save(str(output / f"{name}-compact.png"))
    window.close()
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
