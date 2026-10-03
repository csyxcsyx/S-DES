from functools import partial

from PySide6.QtWidgets import QFileDialog, QLabel

from sdes_app.services.exchange import write_csv
from sdes_app.services.experiments import search_keys
from sdes_app.ui.widgets.layout import Page, actions, button, card
from sdes_app.ui.widgets.pairs import PairEditor
from sdes_app.ui.widgets.results import DataTable
from sdes_app.ui.widgets.tasks import TaskPanel


class AttackPage(Page):
    def __init__(self):
        super().__init__("暴力破解", "枚举全部 1024 个密钥；增加明密文对可继续缩小候选集合。")
        self.result = None
        frame, layout = card("已知明密文对")
        self.pairs = PairEditor()
        self.task = TaskPanel("搜索全部密钥")
        layout.addWidget(self.pairs)
        layout.addWidget(self.task)
        self.body.addWidget(frame)
        frame, layout = card("候选密钥")
        self.summary = QLabel("尚未搜索。结果会列出全部匹配密钥。")
        self.summary.setWordWrap(True)
        self.table = DataTable(("候选序号", "10 位密钥", "十进制"), 220)
        self.export_button = button("导出候选 CSV")
        self.export_button.setEnabled(False)
        layout.addWidget(self.summary)
        layout.addWidget(self.table)
        layout.addLayout(actions(self.export_button))
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
        self.table.set_rows(("候选序号", "10 位密钥", "十进制"), [])
        self.export_button.setEnabled(False)
        self.summary.setText(f"正在匹配 {len(pairs)} 组明密文对…")
        self.pairs.setEnabled(False)
        self.task.start(partial(search_keys, pairs))

    def unlock_inputs(self):
        self.pairs.setEnabled(True)

    def show_result(self, result):
        self.result = result
        self.table.set_rows(("候选序号", "10 位密钥", "十进制"),
                            [(index + 1, f"{key:010b}", key) for index, key in enumerate(result.candidates)])
        state = "搜索完成" if result.completed else "未完成 / 已取消：仅展示已检查范围内的候选"
        explanation = ("可增加明密文对筛选；当前移位规则存在等效密钥，多对数据也不保证唯一。"
                       if result.candidates else "当前已检查范围内没有匹配密钥。")
        self.summary.setText(f"{state}；已检查 {result.checked}/1024 个密钥，找到 {len(result.candidates)} 个候选。{explanation}")
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
