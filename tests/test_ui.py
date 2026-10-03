import os
import sys
import subprocess
import tempfile
import time
import unittest
from functools import partial
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QRawFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QPushButton

from sdes_app.services.experiments import analyze_collisions, search_keys
from sdes_app.services.exchange import verify_csv
from sdes_app.ui.main_window import MainWindow
from sdes_app.ui.theme import apply_theme
from sdes_app.ui.widgets.tasks import TaskPanel


class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)
        apply_theme(cls.app)

    def setUp(self):
        self.qt_errors = []
        self.original_hook = sys.excepthook
        sys.excepthook = lambda kind, error, traceback: self.qt_errors.append(str(error))
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.wait_until(lambda: not self.window.isVisible())
        self.window.deleteLater()
        self.app.processEvents()
        sys.excepthook = self.original_hook
        self.assertEqual(self.qt_errors, [], "Qt 槽函数发生未捕获异常")

    def wait_until(self, predicate, timeout=10):
        deadline = time.perf_counter() + timeout
        while not predicate() and time.perf_counter() < deadline:
            self.app.processEvents()
            QTest.qWait(5)
        self.assertTrue(predicate(), "Qt 操作超时")
        self.app.processEvents()

    def test_binary_actions_copy_validation_keyboard_and_navigation(self):
        page = self.window.pages[0]
        QTest.mouseClick(page.encrypt_button, Qt.MouseButton.LeftButton)
        self.assertEqual(page.result.text(), "11101111")
        self.assertEqual(page.trace.table.model().rowCount(), 18)
        page.result.copy_button.click()
        self.assertEqual(self.app.clipboard().text(), "11101111")
        page.block.set_text("11101111")
        page.decrypt_button.click()
        self.assertEqual(page.result.text(), "10011010")
        page.block.set_text("10011010")
        page.block.editor.setFocus()
        QTest.keyClick(page.block.editor, Qt.Key.Key_Return)
        self.assertEqual(page.result.text(), "11101111")
        page.block.set_text("abc")
        page.encrypt_button.click()
        self.assertFalse(page.block.error.isHidden())
        self.assertEqual(page.result.text(), "")
        for index in range(5):
            self.window.navigation.setCurrentRow(index)
            self.app.processEvents()
            self.assertEqual(self.window.stack.currentIndex(), index)

    def test_text_actions_formats_empty_and_non_ascii(self):
        self.window.navigation.setCurrentRow(1)
        page = self.window.pages[1]
        page.encrypt_button.click()
        for name in ("二进制", "十六进制", "Base64"):
            page.format.setCurrentText(name)
            page.decrypt_button.click()
            self.assertEqual(page.recovered.text(), "This is a test")
            self.assertEqual(page.table.model().rowCount(), 14)
        page.plaintext.set_text("")
        page.encrypt_button.click()
        page.decrypt_button.click()
        self.assertEqual(page.ciphertext.text(), "")
        self.assertEqual(page.recovered.text(), "")
        page.plaintext.set_text("中文")
        page.encrypt_button.click()
        self.assertFalse(page.plaintext.error.isHidden())
        page.ciphertext.set_text("!!!!")
        page.decrypt_button.click()
        self.assertFalse(page.ciphertext.error.isHidden())

    def test_background_attack_and_input_unlock(self):
        self.window.navigation.setCurrentRow(2)
        page = self.window.pages[2]
        page.task.start_button.click()
        self.assertFalse(page.pairs.isEnabled())
        self.wait_until(lambda: not page.task.running)
        self.assertTrue(page.result.completed)
        self.assertIn(642, page.result.candidates)
        self.assertTrue(page.pairs.isEnabled())
        self.assertTrue(page.export_button.isEnabled())
        self.assertTrue(page.task.start_button.isEnabled())

    def test_collision_and_self_check_pages(self):
        page = self.window.pages[3]
        page.start()
        self.wait_until(lambda: not page.task.running)
        self.assertTrue(page.result.completed)
        self.assertTrue(page.plaintext.isEnabled())
        self.assertTrue(page.groups.model().rowCount() > 0)
        testing = self.window.pages[4]
        testing.exhaustive.setChecked(True)
        testing.start_checks()
        self.wait_until(lambda: not testing.task.running)
        self.assertEqual(testing.check_table.model().rowCount(), 5)
        self.assertTrue(testing.exhaustive.isEnabled())

    def test_worker_failure_and_cooperative_cancel_restore_controls(self):
        panel = TaskPanel("测试后台任务")
        panel.setParent(self.window)
        failures = []
        panel.failed.connect(failures.append)

        def broken(**kwargs):
            raise ValueError("测试异常")

        panel.start(broken)
        self.wait_until(lambda: not panel.running)
        self.assertEqual(failures, ["测试异常"])
        self.assertTrue(panel.start_button.isEnabled())
        results = []
        panel.succeeded.connect(results.append)
        panel.start(partial(analyze_collisions, 154, True))
        panel.cancel()
        self.wait_until(lambda: not panel.running)
        self.assertFalse(results[-1].completed)
        self.assertIn("未完成", panel.status.text())
        self.assertTrue(panel.start_button.isEnabled())

    def test_resize_and_close_while_task_running(self):
        self.window.resize(880, 600)
        self.app.processEvents()
        self.assertEqual(self.window.width(), 880)
        self.window.pages[3].task.start(partial(analyze_collisions, 154, True))
        self.window.close()
        self.wait_until(lambda: not self.window.isVisible())
        self.assertFalse(self.window.pages[3].task.running)

    def test_chinese_and_digit_glyphs_are_available(self):
        glyphs = QRawFont.fromFont(self.app.font()).glyphIndexesForString("实验01AB")
        self.assertEqual(len(glyphs), 6)
        self.assertTrue(all(glyph > 0 for glyph in glyphs))
        self.assertGreater(len(set(glyphs)), 1, "字体不能全部退化为同一个缺失字符方框")

    def test_cross_csv_buttons_and_navigation_item_spacing(self):
        page = self.window.pages[4]
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "cross.csv")
            with patch("sdes_app.ui.pages.testing.QFileDialog.getSaveFileName", return_value=(path, "")):
                page.export_button.click()
            self.assertTrue(all(row.passed for row in verify_csv(path)))
            with patch("sdes_app.ui.pages.testing.QFileDialog.getOpenFileName", return_value=(path, "")):
                page.import_button.click()
            self.assertEqual(page.cross_table.model().rowCount(), 8)
            self.assertIn("8/8", page.cross_status.text())
            self.assertIn("只证明文件数据", page.cross_status.text())
        rects = [self.window.navigation.visualItemRect(self.window.navigation.item(index)) for index in range(5)]
        self.assertTrue(all(rect.height() >= 44 for rect in rects))
        self.assertTrue(all(first.bottom() < second.top() for first, second in zip(rects, rects[1:])))
        self.assertFalse(self.window.navigation.horizontalScrollBar().isVisible())

    def test_module_entrypoint_runs_event_loop_and_exits_cleanly(self):
        script = """
import runpy
from PySide6.QtCore import QTimer
from sdes_app.ui.main_window import MainWindow
original_show = MainWindow.show
def show_and_close(self):
    original_show(self)
    QTimer.singleShot(100, self.close)
MainWindow.show = show_and_close
runpy.run_module('sdes_app', run_name='__main__')
"""
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        result = subprocess.run([sys.executable, "-X", "utf8", "-c", script],
                                cwd=Path(__file__).resolve().parents[1], env=env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
