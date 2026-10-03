from functools import partial

from PySide6.QtWidgets import QCheckBox, QFileDialog, QLabel

from sdes_app.services.exchange import write_csv
from sdes_app.services.experiments import analyze_collisions
from sdes_app.ui.widgets.inputs import BitInput
from sdes_app.ui.widgets.layout import Page, actions, button, card
from sdes_app.ui.widgets.results import DataTable
from sdes_app.ui.widgets.tasks import TaskPanel


class CollisionPage(Page):
    def __init__(self):
        super().__init__("封闭测试 · 密钥碰撞", "按题面分析：同一明文是否能被不同密钥加密成相同密文。")
        self.result = None
        frame, layout = card("分析范围")
        self.plaintext = BitInput("指定明文（8 位）", 8, "10011010")
        self.all_plaintexts = QCheckBox("同时统计全部 256 种明文（262144 次加密）")
        self.task = TaskPanel("开始碰撞分析")
        layout.addWidget(self.plaintext)
        layout.addWidget(self.all_plaintexts)
        layout.addWidget(self.task)
        self.body.addWidget(frame)
        frame, layout = card("碰撞统计与实例")
        self.summary = QLabel("固定明文时，1024 个密钥对应最多 256 种密文，必然存在密钥碰撞。")
        self.summary.setWordWrap(True)
        self.statistics = DataTable(("明文", "不同密文数", "碰撞组数", "最大候选数"), 170)
        self.groups = DataTable(("指定明文的密文", "候选密钥数", "10 位候选密钥（完整内容见提示或导出）"), 220)
        self.groups.horizontalHeader().setStretchLastSection(True)
        self.export_stats = button("导出统计 CSV")
        self.export_groups = button("导出指定明文全部映射")
        self.export_stats.setEnabled(False)
        self.export_groups.setEnabled(False)
        layout.addWidget(self.summary)
        layout.addWidget(self.statistics)
        layout.addWidget(self.groups)
        layout.addLayout(actions(self.export_stats, self.export_groups))
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
        self.export_stats.setEnabled(False)
        self.export_groups.setEnabled(False)
        self.statistics.set_rows(("明文", "不同密文数", "碰撞组数", "最大候选数"), [])
        self.groups.set_rows(("指定明文的密文", "候选密钥数", "10 位候选密钥"), [])
        self.plaintext.setEnabled(False)
        self.all_plaintexts.setEnabled(False)
        self.summary.setText("正在统计…")
        self.task.start(partial(analyze_collisions, plaintext, self.all_plaintexts.isChecked()))

    def unlock_inputs(self):
        self.plaintext.setEnabled(True)
        self.all_plaintexts.setEnabled(True)

    def show_result(self, result):
        self.result = result
        state = "已完成" if result.completed else "未完成 / 已取消"
        self.summary.setText(f"{state}；已检查 {result.checked:,}/{result.total:,} 组，完整统计 {len(result.summaries)} 种明文。"
                             f"下表为指定明文 {result.selected_plaintext:08b} 的完整分组。")
        self.statistics.set_rows(("明文", "不同密文数", "碰撞组数", "最大候选数"),
                                 [(f"{row.plaintext:08b}", row.distinct_ciphertexts, row.collision_groups,
                                   row.max_candidates) for row in result.summaries])
        self.groups.set_rows(("指定明文的密文", "候选密钥数", "10 位候选密钥"),
                             [(f"{cipher:08b}", len(keys), " ".join(f"{key:010b}" for key in keys))
                              for cipher, keys in result.groups.items()])
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
