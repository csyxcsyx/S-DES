from functools import partial
from html import escape

from PySide6.QtWidgets import QCheckBox, QFileDialog, QLabel, QTextBrowser

from sdes_app.core import constants
from sdes_app.services.checks import run_checks
from sdes_app.services.exchange import export_vectors, verify_csv
from sdes_app.ui.widgets.layout import Page, actions, button, card
from sdes_app.ui.widgets.tables import DataTable
from sdes_app.ui.widgets.tasks import TaskPanel
from sdes_app.ui.widgets.disclosure import Disclosure

SAMPLE_PAIRS = [(154, 642), (0, 0), (255, 1023), (1, 1), (128, 512), (215, 170), (85, 341), (170, 682)]


class TestingPage(Page):
    def __init__(self):
        super().__init__("测试与说明", "算法自检 · CSV 交叉验证 · 作业参数")
        frame, layout = card("算法自检")
        self.exhaustive = QCheckBox("全空间验证 · 1024 × 256 组")
        self.task = TaskPanel("运行自检")
        self.check_table = DataTable(("测试项", "结果", "说明"), weights=(1.2, 0.7, 2.5), minimums=(145, 90, 240))
        layout.addWidget(self.exhaustive)
        layout.addWidget(self.task)
        layout.addWidget(self.check_table)
        self.body.addWidget(frame)
        frame, layout = card("交叉测试数据")
        self.cross_status = QLabel("组间测试待完成")
        self.cross_status.setObjectName("hint")
        self.cross_status.setToolTip("导入其他小组 CSV 后，须在交叉记录中注明对方组名、程序版本和结果。")
        self.cross_status.setWordWrap(True)
        self.import_button = button("导入并验证")
        self.export_button = button("导出样例")
        self.cross_table = DataTable(("CSV 行", "明文", "密钥", "对方密文", "本地密文", "本地解密", "结果"),
                                    visible_rows=5, minimums=(70, 110, 130, 110, 110, 110, 100))
        layout.addLayout(actions(self.import_button, self.export_button, self.cross_status))
        layout.addWidget(self.cross_table)
        self.body.addWidget(frame)
        frame, layout = card("参考")
        self.help = QTextBrowser()
        self.help.setMinimumHeight(260)
        self.help.setOpenExternalLinks(False)
        self.help.setAccessibleName("算法参数与操作说明")
        self.help.setHtml(self.help_html())
        self.reference = Disclosure("算法参数与说明", self.help)
        layout.addWidget(self.reference)
        self.body.addWidget(frame)
        self.finish()
        self.task.start_button.clicked.connect(self.start_checks)
        self.task.succeeded.connect(self.show_checks)
        self.task.idle.connect(lambda: self.exhaustive.setEnabled(True))
        self.import_button.clicked.connect(self.import_csv)
        self.export_button.clicked.connect(self.export_csv)

    def start_checks(self):
        self.check_table.set_rows([])
        self.exhaustive.setEnabled(False)
        self.task.start(partial(run_checks, self.exhaustive.isChecked()))

    def show_checks(self, report):
        self.check_table.set_rows([(row.name, "通过" if row.passed else "未通过 / 未完成", row.detail) for row in report.rows])

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入其他小组 CSV", "", "CSV 文件 (*.csv)")
        if not path:
            return
        try:
            checks = verify_csv(path)
        except (OSError, ValueError, UnicodeError) as error:
            self.cross_status.setText(f"导入失败：{error}")
            self.cross_table.set_rows([])
            return
        self.cross_table.set_rows([(row.line, row.plaintext, row.key, row.ciphertext, row.actual_ciphertext,
                                   row.actual_plaintext, "通过" if row.passed else row.error or "加密或解密不一致") for row in checks])
        self.cross_status.setText(f"通过 {sum(row.passed for row in checks)}/{len(checks)} 行 · 组间记录待补充")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出本地测试样例", "sdes_vectors.csv", "CSV 文件 (*.csv)")
        if path:
            try:
                export_vectors(path, SAMPLE_PAIRS)
                self.cross_status.setText(f"已导出 {len(SAMPLE_PAIRS)} 条样例 · 组间测试待完成")
                self.cross_status.setToolTip(path)
            except OSError as error:
                self.cross_status.setText(f"导出失败：{error}")

    @staticmethod
    def help_html():
        rows = "".join(f"<tr><td><b>{name}</b></td><td><code>{escape(str(getattr(constants, name)))}</code></td></tr>"
                       for name in ("P10", "P8", "IP", "IP_INVERSE", "EP", "P4", "SBOX1", "SBOX2"))
        return f"""<h3>作业参数</h3>
            <p><b>{constants.KEY_RULE}</b>。第二轮总位移是 2；采用截图 S-Box。</p>
            <table cellspacing='6'>{rows}</table>
            <h3>规则与数据</h3>
            <p>加密 K1 → K2；解密 K2 → K1。ASCII 空文本合法，控制字符以转义形式显示。</p>
            <p>相差 <code>0100000000</code> 的主密钥产生相同子密钥，更多明密文对也无法区分。</p>
            <p>加载反馈最短 600 ms，计算耗时单独记录。系统关闭动画时简化动效；取消后结果标为未完成。</p>
            <p>交叉 CSV 表头：<code>plaintext,key,ciphertext</code>，数据宽度为 8、10、8 位。</p>
            <p>完整指南与测试报告见项目 docs 目录。</p>"""
