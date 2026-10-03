import os
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

from .focus import FocusPolicy

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
    if not hasattr(app, "_sdes_focus_policy"):
        app._sdes_focus_policy = FocusPolicy(app)
        app.installEventFilter(app._sdes_focus_policy)
    assets = Path(__file__).resolve().parent / "assets"
    style_values = dict(COLORS, arrow=(assets / "chevron.svg").as_posix(), check=(assets / "check.svg").as_posix())
    app.setStyleSheet("""
        QWidget { color: %(text)s; }
        QMainWindow, QScrollArea, QWidget#page { background: %(background)s; }
        QFrame#card { background: %(surface)s; border: none; border-radius: 12px; }
        QFrame#sidebar { background: %(surface)s; border: none; }
        QLabel#title { font-size: 25px; font-weight: 700; }
        QLabel#brand { font-size: 22px; font-weight: 700; color: %(primary)s; }
        QLabel#subtitle, QLabel#hint { color: %(muted)s; }
        QLabel#error { color: %(error)s; }
        QLabel#section { font-size: 15px; font-weight: 600; }
        QLabel#metric { font-size: 23px; font-weight: 700; color: %(primary)s; }
        QLineEdit, QPlainTextEdit, QTextBrowser, QComboBox {
            background: #F3F6FA; border: 1px solid transparent; border-radius: 7px;
            padding: 8px; selection-background-color: %(primary)s;
        }
        QLineEdit:hover, QComboBox:hover { background: #EDF2F9; }
        QLineEdit:focus, QPlainTextEdit:focus { background: #EDF3FC; }
        QPlainTextEdit[result="true"] { background: #F3F6FA; }
        QPlainTextEdit[hero="true"] { background: #EAF1FD; color: %(primary)s; padding: 18px 12px; }
        QLineEdit[keyboardFocus="true"], QPlainTextEdit[keyboardFocus="true"],
        QComboBox[keyboardFocus="true"], QTextBrowser[keyboardFocus="true"] { border: 1px solid %(focus)s; }
        QLineEdit[invalid="true"], QPlainTextEdit[invalid="true"] { border: 1px solid %(error)s; }
        QPushButton { background: #EEF2F8; border: 1px solid transparent;
            border-radius: 7px; padding: 8px 14px; min-height: 20px; }
        QPushButton:hover { background: #E5EDFA; }
        QPushButton:pressed { background: #DBE8FD; }
        QPushButton[keyboardFocus="true"] { border-color: %(focus)s; }
        QPushButton[primary="true"] { background: %(primary)s; color: white; }
        QPushButton[primary="true"]:hover { background: %(hover)s; }
        QPushButton[primary="true"]:pressed { background: #143E94; }
        QPushButton[quiet="true"] { background: transparent; color: %(primary)s; padding: 5px 8px; }
        QPushButton[quiet="true"]:hover { background: #EDF3FD; }
        QPushButton:disabled { background: #F1F4F8; color: #8693A5; }
        QComboBox { padding-right: 32px; min-height: 20px; }
        QComboBox::drop-down { border: none; width: 28px; }
        QComboBox::down-arrow { image: url("%(arrow)s"); width: 16px; height: 16px; }
        QComboBox QAbstractItemView { background: white; border: none; padding: 6px;
            selection-background-color: #EAF1FD; selection-color: %(primary)s; outline: none; }
        QListView#comboOptions::item { min-height: 34px; padding: 2px 10px; border-radius: 5px; }
        QListView#comboOptions::item:hover { background: #F2F6FC; }
        QListView#comboOptions::item:selected { background: #EAF1FD; color: %(primary)s; }
        QListWidget#navigation { border: none; background: transparent; outline: none; }
        QListWidget#navigation::item { padding: 10px 12px; border-radius: 7px; }
        QListWidget#navigation::item:selected { background: #E7EFFD; color: %(primary)s; font-weight: 600; }
        QListWidget#navigation::item:hover { background: #F0F4FA; }
        QListWidget#navigation[keyboardFocus="true"]::item:selected { border-left: 2px solid %(focus)s; }
        QTableView { background: %(surface)s; border: none; outline: none;
            selection-background-color: #EAF1FD; selection-color: %(text)s; }
        QTableView::item { padding: 9px 12px; border: none; }
        QTableView::item:hover { background: #F5F8FD; }
        QHeaderView { background: #F3F6FA; border: none; }
        QHeaderView::section { background: #F3F6FA; color: %(muted)s; border: none;
            border-bottom: 1px solid #E8EDF5; padding: 10px 12px; font-weight: 600; }
        QTabWidget::pane { border: none; background: white; }
        QTabBar { border: none; background: transparent; }
        QTabBar::tab { background: transparent; color: %(muted)s; padding: 10px 14px;
            border: none; border-bottom: 2px solid transparent; margin-right: 10px; }
        QTabBar::tab:selected { color: %(primary)s; border-bottom-color: %(primary)s; font-weight: 600; }
        QTabBar::tab:hover { background: #F3F6FC; }
        QProgressBar { border: none; background: #EAF0F8; border-radius: 2px; }
        QProgressBar::chunk { background: %(primary)s; border-radius: 2px; }
        QCheckBox { spacing: 8px; padding: 4px 0; }
        QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #BAC8DC;
            background: #F3F6FA; border-radius: 4px; }
        QCheckBox::indicator:checked { background: %(primary)s; border-color: %(primary)s;
            image: url("%(check)s"); }
        QCheckBox[keyboardFocus="true"] { border: none; color: %(primary)s; }
        QScrollBar:vertical { background: #F6F8FC; width: 10px; margin: 2px 0; }
        QScrollBar:vertical[tableScroll="true"] { margin: 42px 0 2px 0; }
        QScrollBar::handle:vertical { background: #C6D2E3; border-radius: 4px; min-height: 36px; }
        QScrollBar::handle:vertical:hover { background: #A6B8D2; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        QScrollBar:horizontal { background: #F6F8FC; height: 10px; margin: 0 2px; }
        QScrollBar::handle:horizontal { background: #C6D2E3; border-radius: 4px; min-width: 36px; }
        QScrollBar::handle:horizontal:hover { background: #A6B8D2; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }
        QAbstractScrollArea::corner { background: white; }
        QToolTip { background: white; color: %(text)s; border: 1px solid %(border)s; padding: 6px; }
    """ % style_values)
