from functools import partial
from html import escape

from PySide6.QtWidgets import QCheckBox, QFileDialog, QLabel, QTextBrowser

from sdes_app.core import constants
from sdes_app.services.checks import run_checks
from sdes_app.services.exchange import export_vectors, verify_csv
from sdes_app.ui.widgets.layout import Page, actions, button, card
from sdes_app.ui.widgets.results import DataTable
from sdes_app.ui.widgets.tasks import TaskPanel

SAMPLE_PAIRS = [(154, 642), (0, 0), (255, 1023), (1, 1), (128, 512), (215, 170), (85, 341), (170, 682)]


class TestingPage(Page):
    def __init__(self):
        super().__init__("测试与说明", "核对参数、运行算法自检，并使用 CSV 与其他小组交换明密文样例。")
        frame, layout = card("算法自检")
        self.exhaustive = QCheckBox("检查全部 1024 × 256 组加解密往返")
        self.task = TaskPanel("运行自检")
        self.check_table = DataTable(("测试项", "结果", "说明"), 160)
        layout.addWidget(self.exhaustive)
        layout.addWidget(self.task)
        layout.addWidget(self.check_table)
        self.body.addWidget(frame)
        frame, layout = card("交叉测试数据")
        self.cross_status = QLabel("正式组间交叉测试：待完成。请导入其他小组导出的 CSV，并在报告中注明数据来源。")
        self.cross_status.setWordWrap(True)
        self.import_button = button("导入 CSV 并验证")
        self.export_button = button("导出本地样例 CSV")
        self.cross_table = DataTable(("CSV 行", "明文", "密钥", "对方密文", "本地密文", "本地解密", "结果"), 180)
        layout.addWidget(self.cross_status)
        layout.addLayout(actions(self.import_button, self.export_button))
        layout.addWidget(self.cross_table)
        self.body.addWidget(frame)
        frame, layout = card("参数与操作说明")
        self.help = QTextBrowser()
        self.help.setMinimumHeight(260)
        self.help.setOpenExternalLinks(False)
        self.help.setAccessibleName("算法参数与操作说明")
        self.help.setHtml(self.help_html())
        layout.addWidget(self.help)
        self.body.addWidget(frame)
        self.finish()
        self.task.start_button.clicked.connect(self.start_checks)
        self.task.succeeded.connect(self.show_checks)
        self.task.idle.connect(lambda: self.exhaustive.setEnabled(True))
        self.import_button.clicked.connect(self.import_csv)
        self.export_button.clicked.connect(self.export_csv)

    def start_checks(self):
        self.check_table.set_rows(("测试项", "结果", "说明"), [])
        self.exhaustive.setEnabled(False)
        self.task.start(partial(run_checks, self.exhaustive.isChecked()))

    def show_checks(self, report):
        self.check_table.set_rows(("测试项", "结果", "说明"),
                                 [(row.name, "通过" if row.passed else "未通过 / 未完成", row.detail) for row in report.rows])

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入其他小组 CSV", "", "CSV 文件 (*.csv)")
        if not path:
            return
        try:
            checks = verify_csv(path)
        except (OSError, ValueError, UnicodeError) as error:
            self.cross_status.setText(f"导入失败：{error}")
            self.cross_table.set_rows(("CSV 行", "明文", "密钥", "对方密文", "本地密文", "本地解密", "结果"), [])
            return
        self.cross_table.set_rows(("CSV 行", "明文", "密钥", "对方密文", "本地密文", "本地解密", "结果"),
                                 [(row.line, row.plaintext, row.key, row.ciphertext, row.actual_ciphertext,
                                   row.actual_plaintext, "通过" if row.passed else row.error or "加密或解密不一致") for row in checks])
        self.cross_status.setText(f"文件验证通过 {sum(row.passed for row in checks)}/{len(checks)} 行。"
                                 "这只证明文件数据与本地一致；正式组间测试请补充对方组名、程序版本和测试记录。")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出本地测试样例", "sdes_vectors.csv", "CSV 文件 (*.csv)")
        if path:
            try:
                export_vectors(path, SAMPLE_PAIRS)
                self.cross_status.setText(f"已导出 {len(SAMPLE_PAIRS)} 条本地样例：{path}。请交给其他小组验证；组间测试仍待完成。")
            except OSError as error:
                self.cross_status.setText(f"导出失败：{error}")

    @staticmethod
    def help_html():
        rows = "".join(f"<tr><td><b>{name}</b></td><td><code>{escape(str(getattr(constants, name)))}</code></td></tr>"
                       for name in ("P10", "P8", "IP", "IP_INVERSE", "EP", "P4", "SBOX1", "SBOX2"))
        return f"""<h3>本程序使用的作业参数</h3>
            <p><b>{constants.KEY_RULE}</b>。第二轮总位移是 2；采用截图 S-Box。</p>
            <table cellspacing='6'>{rows}</table>
            <h3>操作提示</h3>
            <p>二进制页输入 8 位分组和 10 位密钥；加密用 K1、K2，解密用 K2、K1。</p>
            <p>文本页只接受 ASCII；密文使用二进制、十六进制或 Base64 无损表示，空文本是合法输入。</p>
            <p>破解页每行填写一组已知明密文对，搜索会返回所有候选；候选不等于已证明唯一的原始密钥。</p>
            <p>累计左移 1、2 位的规则使原始密钥第 2 位不进入任何轮密钥。因此相差 <code>0100000000</code> 的两个密钥产生相同的两个轮密钥；增加明密文对也无法区分它们。</p>
            <p>封闭测试按题面检查密钥碰撞。1024 个密钥映射到最多 256 种密文，因此固定明文必有碰撞；每组候选数由实测得出。</p>
            <p>任务取消后结果明确标为未完成，导出包含完成状态。耗时来自实际计算，没有人为延时。</p>
            <p>交叉 CSV 表头：<code>plaintext,key,ciphertext</code>，数据宽度为 8、10、8 位。</p>
            <p>完整指南、开发接口和五关报告位于项目 docs 目录。运行全部测试：<code>python -m unittest discover -v</code>。</p>"""
