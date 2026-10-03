from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel

from sdes_app.services.exchange import write_csv
from sdes_app.services.experiments import analyze_collisions
from sdes_app.ui.widgets.inputs import BitInput
from sdes_app.ui.widgets.layout import Page, actions, button, card
from sdes_app.ui.widgets.tables import DataTable, TableTabs
from sdes_app.ui.widgets.tasks import TaskPanel
from sdes_app.ui.widgets.metrics import MetricsRow, elapsed_text


class CollisionPage(Page):
    def __init__(self):
        super().__init__("封闭测试", "检查不同密钥产生相同密文的情况")
        self.result = None
        frame, layout = card("分析范围")
        self.plaintext = BitInput("指定明文 · 8 位", 8, "10011010")
        self.all_plaintexts = QCheckBox("遍历全部 256 种明文")
        self.all_plaintexts.setToolTip("共执行 262144 次加密；指定明文的分组单独显示")
        self.task = TaskPanel("开始分析", show_elapsed=False)
        scope = QHBoxLayout()
        scope.setSpacing(20)
        scope.addWidget(self.plaintext, 1)
        scope.addWidget(self.all_plaintexts, 1, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(scope)
        layout.addWidget(self.task)
        self.body.addWidget(frame)
        frame, layout = card("碰撞统计与实例")
        self.metrics = MetricsRow(("不同密文", "碰撞组", "最大候选数", "计算耗时"))
        self.summary = QLabel("等待分析")
        self.summary.setObjectName("hint")
        self.summary.setWordWrap(True)
        self.statistics = DataTable(("明文", "不同密文", "碰撞组", "最大候选数"), visible_rows=5)
        self.groups = DataTable(("密文", "候选数", "候选密钥 · 10 位"), visible_rows=5,
                                weights=(1, 1, 3), minimums=(110, 90, 240))
        self.groups.setToolTip("悬停查看完整密钥，或导出全部映射")
        self.tabs = TableTabs(("明文统计", self.statistics), ("密钥分组", self.groups))
        self.export_stats = button("导出统计 CSV")
        self.export_groups = button("导出密钥映射")
        self.export_stats.setEnabled(False)
        self.export_groups.setEnabled(False)
        layout.addWidget(self.metrics)
        layout.addWidget(self.summary)
        layout.addLayout(actions(self.export_stats, self.export_groups))
        layout.addWidget(self.tabs)
        self.body.addWidget(frame)
        self.finish()
        self.task.start_button.clicked.connect(self.start)
        self.task.succeeded.connect(self.show_result)
        self.task.failed.connect(self.show_error)
        self.task.idle.connect(self.unlock_inputs)
        self.export_stats.clicked.connect(self.export_statistics)
        self.export_groups.clicked.connect(self.export_mapping)

    def start(self):
        try:
            plaintext = self.plaintext.value()
        except ValueError:
            return
        self.result = None
        self.metrics.reset()
        self.export_stats.setEnabled(False)
        self.export_groups.setEnabled(False)
        self.statistics.set_rows([])
        self.groups.set_rows([])
        self.tabs.setTabText(0, "明文统计")
        self.tabs.setTabText(1, "密钥分组")
        self.plaintext.setEnabled(False)
        self.all_plaintexts.setEnabled(False)
        self.summary.setText("正在统计…")
        self.task.start(partial(analyze_collisions, plaintext, self.all_plaintexts.isChecked()))

    def unlock_inputs(self):
        self.plaintext.setEnabled(True)
        self.all_plaintexts.setEnabled(True)

    def show_result(self, result):
        self.result = result
        selected = next((row for row in result.summaries if row.plaintext == result.selected_plaintext), None)
        self.metrics.set_values(selected.distinct_ciphertexts if selected else "—",
                                selected.collision_groups if selected else "—",
                                selected.max_candidates if selected else "—", elapsed_text(result.elapsed))
        self.summary.setText(f"指定明文 {result.selected_plaintext:08b} · 已统计 {len(result.summaries)} 种明文"
                             + ("" if result.completed else " · 未完成"))
        self.statistics.set_rows([(f"{row.plaintext:08b}", row.distinct_ciphertexts, row.collision_groups,
                                   row.max_candidates) for row in result.summaries])
        self.groups.set_rows([(f"{cipher:08b}", len(keys), " ".join(f"{key:010b}" for key in keys))
                              for cipher, keys in result.groups.items()])
        self.tabs.setTabText(0, f"明文统计 · {len(result.summaries)}")
        self.tabs.setTabText(1, f"密钥分组 · {len(result.groups)}")
        self.export_stats.setEnabled(bool(result.summaries))
        self.export_groups.setEnabled(bool(result.groups))

    def show_error(self, error):
        self.summary.setText(f"分析失败：{error}")

    def save(self, name, columns, rows):
        path, _ = QFileDialog.getSaveFileName(self, "导出分析", name, "CSV 文件 (*.csv)")
        if path:
            try:
                write_csv(path, columns, rows)
                self.summary.setText(f"已导出：{path}")
            except OSError as error:
                self.show_error(str(error))

    def export_statistics(self):
        result = self.result
        if result is None:
            return
        self.save("collision_statistics.csv",
                  ("plaintext", "distinct_ciphertexts", "collision_groups", "max_candidates", "completed", "checked", "elapsed_seconds"),
                  [(f"{row.plaintext:08b}", row.distinct_ciphertexts, row.collision_groups, row.max_candidates,
                    result.completed, result.checked, f"{result.elapsed:.9f}") for row in result.summaries])

    def export_mapping(self):
        result = self.result
        if result is None:
            return
        self.save("collision_mapping.csv", ("plaintext", "ciphertext", "key", "completed"),
                  [(f"{result.selected_plaintext:08b}", f"{cipher:08b}", f"{key:010b}", result.completed)
                   for cipher, keys in result.groups.items() for key in keys])
