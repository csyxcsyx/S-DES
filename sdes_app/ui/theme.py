import os
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

COLORS = {
    "background": "#F4F7FC", "surface": "#FFFFFF", "text": "#182943",
    "muted": "#52647B", "primary": "#215AC5", "hover": "#184AAB",
    "border": "#CED8E6", "error": "#B42318", "focus": "#3574DE",
}


def apply_theme(app):
    # Windows 的 offscreen 插件没有系统字体目录；测试渲染显式加载本机字体。
    # 不分发字体文件，正常 Windows 平台仍使用系统的字体发现机制。
    if os.name == "nt" and app.platformName() == "offscreen" and not QFontDatabase.families():
        font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for filename in ("msyh.ttc", "msyhbd.ttc", "consola.ttf", "consolab.ttf"):
            path = font_dir / filename
            if path.is_file():
                QFontDatabase.addApplicationFont(str(path))
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setStyleSheet("""
        QWidget { color: %(text)s; }
        QMainWindow, QScrollArea, QWidget#page { background: %(background)s; }
        QFrame#card { background: %(surface)s; border: 1px solid %(border)s; border-radius: 12px; }
        QFrame#sidebar { background: %(surface)s; border-right: 1px solid %(border)s; }
        QLabel#title { font-size: 25px; font-weight: 700; }
        QLabel#brand { font-size: 22px; font-weight: 700; color: %(primary)s; }
        QLabel#subtitle, QLabel#hint { color: %(muted)s; }
        QLabel#error { color: %(error)s; }
        QLabel#section { font-size: 15px; font-weight: 600; }
        QLineEdit, QPlainTextEdit, QTextBrowser, QComboBox {
            background: %(surface)s; border: 1px solid %(border)s; border-radius: 6px;
            padding: 8px; selection-background-color: %(primary)s;
        }
        QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QTextBrowser:focus {
            border: 2px solid %(focus)s;
        }
        QLineEdit[invalid="true"], QPlainTextEdit[invalid="true"] { border: 1px solid %(error)s; }
        QPushButton { background: %(surface)s; border: 1px solid %(border)s;
            border-radius: 6px; padding: 8px 16px; min-height: 18px; }
        QPushButton:hover { background: #EDF3FD; border-color: %(primary)s; }
        QPushButton:pressed { background: #DBE8FD; }
        QPushButton:focus { border: 2px solid %(focus)s; }
        QPushButton[primary="true"] { background: %(primary)s; color: white; border-color: %(primary)s; }
        QPushButton[primary="true"]:hover { background: %(hover)s; }
        QPushButton:disabled { background: #E8EDF4; color: #66758B; border-color: %(border)s; }
        QListWidget#navigation { border: none; background: transparent; outline: none; }
        QListWidget#navigation::item { padding: 13px 12px; border-radius: 7px; margin: 3px 0; }
        QListWidget#navigation::item:selected { background: #E7EFFD; color: %(primary)s; font-weight: 600; }
        QListWidget#navigation::item:hover { background: #F0F4FA; }
        QListWidget#navigation:focus { border: 2px solid %(focus)s; border-radius: 6px; }
        QTableView { background: %(surface)s; border: 1px solid %(border)s; border-radius: 6px;
            gridline-color: #E4EAF3; selection-background-color: #DCE9FD; selection-color: %(text)s; }
        QHeaderView::section { background: #EEF3FA; border: none; border-bottom: 1px solid %(border)s;
            padding: 9px; font-weight: 600; }
        QProgressBar { border: 1px solid %(border)s; background: #EAF0F8; border-radius: 5px;
            min-height: 18px; text-align: center; }
        QProgressBar::chunk { background: %(primary)s; border-radius: 4px; }
        QToolTip { background: white; color: %(text)s; border: 1px solid %(border)s; padding: 6px; }
    """ % COLORS)
