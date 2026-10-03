"""渲染实际 Qt 窗口，并通过应用自身操作生成可复现的报告截图。"""
import os
import argparse
import sys
import time
from unittest.mock import patch
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtTest import QTest
from PySide6.QtCore import QPoint
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from sdes_app.ui.main_window import MainWindow
from sdes_app.ui.theme import apply_theme
from sdes_app.ui.motion import TRANSITION_MS


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--animation", action="store_true", help="额外生成真实 Qt 帧动图，需要 Pillow")
    options = parser.parse_args()
    output = ROOT / "docs" / "evidence" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    apply_theme(app)
    window = MainWindow()
    window.resize(1120, 900)
    window.show()
    app.processEvents()
    window.grab().save(str(output / "10-binary-empty.png"))
    binary, text, attack, collision, testing = window.pages
    binary.example()
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
    vectors = str(ROOT / "docs" / "evidence" / "results" / "local-vectors.csv")
    with patch("sdes_app.ui.pages.testing.QFileDialog.getOpenFileName", return_value=(vectors, "")):
        testing.import_button.click()
    names = ("01-binary", "02-ascii", "03-attack", "04-collisions", "05-testing")
    for index, name in enumerate(names):
        window.navigation.setCurrentRow(index)
        app.processEvents()
        QTest.qWait(TRANSITION_MS + 60)
        path = output / f"{name}.png"
        if not window.grab().save(str(path)):
            raise RuntimeError(f"无法保存截图：{path}")
        print(path)
    window.navigation.setCurrentRow(3)
    collision.tabs.setCurrentIndex(1)
    QTest.qWait(60)
    window.grab().save(str(output / "09-key-groups.png"))
    collision.tabs.setCurrentIndex(0)
    window.navigation.setCurrentRow(0)
    binary.trace.toggle.setChecked(True)
    QTest.qWait(TRANSITION_MS + 60)
    window.grab().save(str(output / "07-trace.png"))
    binary.trace.toggle.setChecked(False)
    window.navigation.setCurrentRow(1)
    QTest.qWait(TRANSITION_MS + 60)
    text.format.showPopup()
    QTest.qWait(60)
    snapshot = window.grab()
    popup = text.format.view().window()
    painter = QPainter(snapshot)
    painter.drawPixmap(window.mapFromGlobal(popup.mapToGlobal(QPoint(0, 0))), popup.grab())
    painter.end()
    snapshot.save(str(output / "08-dropdown.png"))
    text.format.hidePopup()
    if options.animation:
        capture_loading(app, window, attack, output / "06-loading.gif")
    window.resize(880, 600)
    for index, name in enumerate(names):
        window.navigation.setCurrentRow(index)
        app.processEvents()
        QTest.qWait(TRANSITION_MS + 60)
        window.grab().save(str(output / f"{name}-compact.png"))
    window.close()
    app.processEvents()
    return 0


def capture_loading(app, window, attack, path):
    from PIL import Image

    window.navigation.setCurrentRow(2)
    QTest.qWait(TRANSITION_MS + 60)
    frames, timestamps = [], []
    attack.start()
    # 捕获实际 Qt 状态；算法线程不增加睡眠，显示过渡由应用自身控制。
    deadline = time.perf_counter() + 1.6
    while time.perf_counter() < deadline or attack.task.running:
        app.processEvents()
        frames.append(window.grab().toImage())
        timestamps.append(time.perf_counter())
        QTest.qWait(20)
    # 编码放到采样结束后，避免 PNG 压缩占用采样时间使预览卡顿。
    encoded = []
    for frame in frames:
        rgb = frame.convertToFormat(QImage.Format.Format_RGB888)
        encoded.append(Image.frombytes("RGB", (rgb.width(), rgb.height()), bytes(rgb.constBits()),
                                       "raw", "RGB", rgb.bytesPerLine()))
    durations = [max(10, round((second - first) * 100) * 10)
                 for first, second in zip(timestamps, timestamps[1:])] + [40]
    encoded[0].save(path, save_all=True, append_images=encoded[1:], duration=durations, loop=0)
    print(path)


if __name__ == "__main__":
    raise SystemExit(main())
