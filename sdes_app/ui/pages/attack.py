from functools import partial

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel

from sdes_app.services.exchange import write_csv
from sdes_app.services.experiments import search_keys
from sdes_app.ui.widgets.layout import Page, button, card
from sdes_app.ui.widgets.pairs import PairEditor
from sdes_app.ui.widgets.tables import DataTable
from sdes_app.ui.widgets.tasks import TaskPanel
from sdes_app.ui.widgets.metrics import MetricsRow, elapsed_text


class AttackPage(Page):
    def __init__(self):
        super().__init__("暴力破解", "输入已知明密文对，搜索全部 1024 个密钥")
        self.result = None
        frame, layout = card("已知明密文对")
        self.pairs = PairEditor()
        self.task = TaskPanel("开始搜索", show_elapsed=False)
        layout.addWidget(self.pairs)
        layout.addWidget(self.task)
        self.body.addWidget(frame)
        frame, layout = card("候选密钥")
        self.metrics = MetricsRow(("候选密钥", "已检查密钥", "计算耗时"))
        self.summary = QLabel("等待搜索")
        self.summary.setObjectName("hint")
        self.summary.setWordWrap(True)
        self.table = DataTable(("序号", "密钥 · 10 位", "十进制"))
        self.export_button = button("导出候选 CSV")
        self.export_button.setEnabled(False)
        layout.addWidget(self.metrics)
        result_actions = QHBoxLayout()
        result_actions.addWidget(self.export_button)
        result_actions.addWidget(self.summary, 1)
        layout.addLayout(result_actions)
        layout.addWidget(self.table)
        self.body.addWidget(frame)
        self.finish()
        self.task.start_button.clicked.connect(self.start)
        self.task.succeeded.connect(self.show_result)
        self.task.failed.connect(self.show_error)
        self.task.idle.connect(self.unlock_inputs)
        self.export_button.clicked.connect(self.export)

    def start(self):
        try:
            pairs = self.pairs.values()
        except ValueError:
            return
        self.result = None
        self.metrics.reset()
        self.table.set_rows([])
        self.export_button.setEnabled(False)
        self.summary.setText(f"正在匹配 {len(pairs)} 组明密文对…")
        self.pairs.setEnabled(False)
        self.task.start(partial(search_keys, pairs))

    def unlock_inputs(self):
        self.pairs.setEnabled(True)

    def show_result(self, result):
        self.result = result
        self.metrics.set_values(len(result.candidates), f"{result.checked:,}", elapsed_text(result.elapsed))
        self.table.set_rows([(index + 1, f"{key:010b}", key) for index, key in enumerate(result.candidates)])
        explanation = "含等效密钥，候选可能不唯一" if result.candidates else "没有匹配密钥"
        self.summary.setText(explanation if result.completed else "未完成 · 仅显示已检查范围的候选")
        self.summary.setToolTip("本作业规则使相差 0100000000 的两个主密钥等效；更多明密文对也无法区分。")
        self.export_button.setEnabled(True)

    def show_error(self, error):
        self.summary.setText(f"搜索失败：{error}")

    def export(self):
        if self.result is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出候选", "key_candidates.csv", "CSV 文件 (*.csv)")
        if not path:
            return
        result = self.result
        try:
            write_csv(path, ("key", "decimal", "completed", "checked", "elapsed_seconds"),
                      [(f"{key:010b}", key, result.completed, result.checked, f"{result.elapsed:.9f}")
                       for key in result.candidates] or [("", "", result.completed, result.checked, f"{result.elapsed:.9f}")])
            self.summary.setText(f"已导出：{path}")
        except OSError as error:
            self.show_error(str(error))
