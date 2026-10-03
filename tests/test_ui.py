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

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QRawFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QPushButton, QTableView

from sdes_app.services.experiments import analyze_collisions, search_keys
from sdes_app.services.exchange import verify_csv
from sdes_app.ui.main_window import MainWindow
from sdes_app.ui.theme import apply_theme
from sdes_app.ui.widgets.tasks import TaskPanel
from sdes_app.ui.motion import MIN_LOADING_MS


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
            self.assertIn("组间记录待补充", page.cross_status.text())
        rects = [self.window.navigation.visualItemRect(self.window.navigation.item(index)) for index in range(5)]
        self.assertTrue(all(rect.height() >= 44 for rect in rects))
        self.assertTrue(all(first.bottom() < second.top() for first, second in zip(rects, rects[1:])))
        self.assertFalse(self.window.navigation.horizontalScrollBar().isVisible())

    def test_uniform_tables_and_editable_pair_cells(self):
        for table in self.window.findChildren(QTableView):
            self.assertTrue(table.verticalHeader().isHidden())
            self.assertFalse(table.isCornerButtonEnabled())
            self.assertFalse(table.alternatingRowColors())
        pairs = self.window.pages[2].pairs
        self.assertEqual(pairs.table.rowCount(), 1)
        pairs.add_button.click()
        self.assertEqual(pairs.table.rowCount(), 2)
        pairs.table.item(1, 0).setText("01010101")
        pairs.table.item(1, 1).setText("00000101")
        self.assertEqual(pairs.values(), [(154, 239), (85, 5)])
        pairs.table.selectRow(1)
        pairs.remove_button.click()
        self.assertEqual(pairs.table.rowCount(), 1)

    def test_minimum_loading_feedback_keeps_event_loop_and_real_time(self):
        panel = self.window.pages[2].task
        results, beats = [], []
        panel.succeeded.connect(results.append)
        pulse = QTimer()
        pulse.setInterval(10)
        pulse.timeout.connect(lambda: beats.append(1))
        with patch.dict(os.environ, SDES_REDUCED_MOTION="0"):
            pulse.start()
            started = time.perf_counter()
            panel.start(partial(search_keys, [(154, 239)]))
            self.wait_until(lambda: panel.worker is None)
            actual_elapsed = panel._result.elapsed
            self.assertTrue(panel.running)
            self.assertEqual(panel.status.text(), "结果就绪")
            self.assertFalse(panel.start_button.isEnabled())
            self.wait_until(lambda: not panel.running)
            pulse.stop()
            self.assertGreaterEqual(time.perf_counter() - started, MIN_LOADING_MS / 1000 - 0.01)
            self.assertGreater(len(beats), 10, "加载展示不能阻塞 Qt 事件循环")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].elapsed, actual_elapsed)
            self.assertTrue(panel.spinner.isHidden())

    def test_cancel_presentation_and_reduced_motion_skip_minimum(self):
        panel = self.window.pages[2].task
        results = []
        panel.succeeded.connect(results.append)
        with patch.dict(os.environ, SDES_REDUCED_MOTION="0"):
            panel.start(partial(search_keys, [(154, 239)]))
            self.wait_until(lambda: panel.worker is None)
            self.assertTrue(panel.running)
            panel.cancel()
            self.assertFalse(panel.running)
            self.assertTrue(results[-1].completed, "已完成计算不能伪装为取消的部分结果")
            QTest.qWait(MIN_LOADING_MS + 20)
            self.assertEqual(len(results), 1)
        with patch.dict(os.environ, SDES_REDUCED_MOTION="1"):
            panel.start(partial(search_keys, [(154, 239)]))
            self.assertFalse(panel.spinner.timer.isActive())
            self.wait_until(lambda: not panel.running)
            self.assertFalse(panel.presentation_timer.isActive())
            self.window.navigation.setCurrentRow(1)
            self.assertIsNone(self.window.stack.graphicsEffect())
            self.assertEqual(len(results), 2)

    def test_rapid_navigation_disclosure_and_dropdown_keyboard(self):
        with patch.dict(os.environ, SDES_REDUCED_MOTION="0"):
            for index in (1, 3, 2, 4, 0):
                self.window.navigation.setCurrentRow(index)
                self.app.processEvents()
            trace = self.window.pages[0].trace
            for expanded in (True, False, True, False, True):
                trace.toggle.setChecked(expanded)
                self.app.processEvents()
            QTest.qWait(220)
            self.assertIsNone(self.window.stack.graphicsEffect())
            self.assertFalse(trace.panel.isHidden())
            self.assertGreaterEqual(trace.panel.maximumHeight(), trace.table.height())
            trace.toggle.setChecked(False)
            QTest.qWait(220)
            self.assertTrue(trace.panel.isHidden())
            self.window.navigation.setCurrentRow(1)
            combo = self.window.pages[1].format
            combo.setFocus(Qt.FocusReason.TabFocusReason)
            QTest.keyClick(combo, Qt.Key.Key_Down)
            self.assertEqual(combo.currentText(), "十六进制")
            combo.showPopup()
            self.app.processEvents()
            self.assertTrue(combo.view().isVisible())
            combo.hidePopup()

    def test_pointer_focus_quiet_and_keyboard_focus_visible(self):
        page = self.window.pages[0]
        page.key.editor.setFocus()
        page.block.editor.setFocus(Qt.FocusReason.TabFocusReason)
        self.app.processEvents()
        self.assertTrue(page.block.editor.property("keyboardFocus"))
        QTest.mouseClick(page.block.editor, Qt.MouseButton.LeftButton)
        self.assertFalse(page.block.editor.property("keyboardFocus"))
        QTest.keyClick(page.block.editor, Qt.Key.Key_Tab)
        self.assertTrue(page.key.editor.property("keyboardFocus"))

    def test_table_model_reuse_and_complete_rows(self):
        page = self.window.pages[2]
        table = page.table
        model = table.model()
        table.set_rows([(1, "1010000010", 642), (2, "1110000010", 898)])
        self.window.navigation.setCurrentRow(2)
        QTest.qWait(80)
        self.assertIs(table.model(), model)
        self.assertFalse(table.showGrid())
        self.assertLess(table.visualRect(model.index(1, 0)).bottom(), table.viewport().height())
        self.assertEqual(model.data(model.index(0, 1), Qt.ItemDataRole.ToolTipRole), "1010000010")
        table.set_rows([])
        self.assertIs(table.model(), model)
        self.assertEqual(model.rowCount(), 0)

    def test_table_layout_at_150_and_200_percent_scale(self):
        for scale in ("1.5", "2"):
            with self.subTest(scale=scale):
                env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_SCALE_FACTOR=scale)
                result = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).with_name("gui_probe.py"))],
                                        env=env, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)

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
