from PySide6.QtCore import QSize, QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QListWidget, QMainWindow, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from .pages.attack import AttackPage
from .pages.binary import BinaryPage
from .pages.collisions import CollisionPage
from .pages.testing import TestingPage
from .pages.text import TextPage
from .widgets.tasks import TaskPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("S-DES 实验室 · 信息安全导论")
        self.resize(1120, 820)
        self.setMinimumSize(880, 600)
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 28, 18, 24)
        sidebar_layout.setSpacing(12)
        brand = QLabel("S-DES 实验室")
        brand.setObjectName("brand")
        sidebar_layout.addWidget(brand)
        course = QLabel("信息安全导论\n分组密码 · 两轮变换")
        course.setObjectName("hint")
        sidebar_layout.addWidget(course)
        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setAccessibleName("功能导航，使用上下方向键切换")
        self.navigation.addItems(("二进制加解密", "ASCII 文本", "暴力破解", "封闭测试", "测试与说明"))
        self.navigation.setSpacing(4)
        self.navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for index in range(self.navigation.count()):
            self.navigation.item(index).setSizeHint(QSize(120, 44))
        sidebar_layout.addWidget(self.navigation)
        rule = QLabel("8 位分组 / 10 位密钥\n子密钥累计移位：1、2\n作业截图参数")
        rule.setObjectName("hint")
        rule.setWordWrap(True)
        sidebar_layout.addWidget(rule)
        root_layout.addWidget(sidebar)
        self.stack = QStackedWidget()
        self.pages = [BinaryPage(), TextPage(), AttackPage(), CollisionPage(), TestingPage()]
        for page in self.pages:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setWidget(page)
            self.stack.addWidget(scroll)
        root_layout.addWidget(self.stack, 1)
        self.navigation.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        self.setCentralWidget(root)

    def closeEvent(self, event):
        active = [task for task in self.findChildren(TaskPanel) if task.running]
        if active:
            for task in active:
                task.cancel()
            event.ignore()
            self.statusBar().showMessage("正在停止后台任务，结束后自动关闭…")
            QTimer.singleShot(50, self.close)
        else:
            event.accept()
