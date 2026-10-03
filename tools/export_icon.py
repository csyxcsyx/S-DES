"""从单一 SVG 源导出 PNG 预览和 Windows 多尺寸 ICO。"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication
from sdes_app.ui.assets import ASSETS


def main():
    app = QApplication.instance() or QApplication([])
    renderer = QSvgRenderer(str(ASSETS / "app.svg"))
    if not renderer.isValid():
        raise ValueError("应用图标 SVG 无效")
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    image.save(str(ASSETS / "app.png"))
    with Image.open(ASSETS / "app.png") as preview:
        preview.save(ASSETS / "app.ico", sizes=[(size, size) for size in (16, 24, 32, 48, 64, 128, 256)])
    print(ASSETS / "app.ico")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
