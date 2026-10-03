from pathlib import Path

from PySide6.QtGui import QIcon

ASSETS = Path(__file__).with_name("assets")


def application_icon():
    return QIcon(str(ASSETS / "app.svg"))
