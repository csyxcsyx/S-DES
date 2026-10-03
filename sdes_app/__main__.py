import sys


def main():
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("缺少 PySide6，请先运行：python -m pip install -r requirements.txt", file=sys.stderr)
        return 1
    from .ui.main_window import MainWindow
    from .ui.theme import apply_theme

    app = QApplication(sys.argv)
    app.setApplicationName("S-DES 实验室")
    app.setOrganizationName("S-DES Course Lab")
    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
