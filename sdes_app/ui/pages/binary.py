from PySide6.QtWidgets import QHBoxLayout, QLabel

from sdes_app.core import trace_block
from sdes_app.ui.widgets.inputs import BitInput
from sdes_app.ui.widgets.layout import Page, actions, button, card
from sdes_app.ui.widgets.results import ResultPanel, TracePanel


class BinaryPage(Page):
    def __init__(self):
        super().__init__("二进制加解密", "8 位分组 → 两轮变换 → 输出结果")
        columns = QHBoxLayout()
        columns.setSpacing(18)
        frame, layout = card("输入")
        self.block = BitInput("分组 · 8 位", 8, "10011010")
        self.key = BitInput("密钥 · 10 位", 10, "1010000010")
        layout.addWidget(self.block)
        layout.addWidget(self.key)
        self.encrypt_button = button("加密", True)
        self.decrypt_button = button("解密")
        self.example_button = button("示例")
        self.example_button.setProperty("quiet", True)
        layout.addLayout(actions(self.encrypt_button, self.decrypt_button, self.example_button))
        columns.addWidget(frame, 1)
        frame, layout = card("结果")
        self.subkeys = QLabel("K1  —\nK2  —")
        self.subkeys.setObjectName("hint")
        self.subkeys.setWordWrap(True)
        self.result = ResultPanel("输出分组", height=95, hero=True)
        self.trace = TracePanel()
        layout.addWidget(self.result)
        layout.addWidget(self.subkeys)
        layout.addStretch()
        columns.addWidget(frame, 1)
        self.body.addLayout(columns)
        frame, layout = card("计算过程")
        layout.addWidget(self.trace)
        self.body.addWidget(frame)
        self.finish()
        self.encrypt_button.clicked.connect(self.encrypt)
        self.decrypt_button.clicked.connect(self.decrypt)
        self.example_button.clicked.connect(self.example)
        self.block.editor.returnPressed.connect(self.encrypt)
        self.key.editor.returnPressed.connect(self.encrypt)
        self.block.editor.textChanged.connect(self.invalidate)
        self.key.editor.textChanged.connect(self.invalidate)

    def invalidate(self):
        self.result.set_text("")
        self.subkeys.setText("K1  —\nK2  —")
        self.trace.table.set_rows([])

    def calculate(self, decrypt: bool):
        try:
            block, key = self.block.value(), self.key.value()
        except ValueError:
            return
        trace = trace_block(block, key, decrypt)
        self.result.label.setText("解密明文" if decrypt else "加密密文")
        self.result.set_text(f"{trace.output:08b}")
        first, second = trace.subkeys
        self.subkeys.setText(f"K1  {first:08b}\nK2  {second:08b}")
        self.subkeys.setToolTip('解密顺序 K2 → K1' if decrypt else '加密顺序 K1 → K2')
        self.trace.set_trace(trace)

    def encrypt(self):
        self.calculate(False)

    def decrypt(self):
        self.calculate(True)

    def example(self):
        self.block.set_text("10011010")
        self.key.set_text("1010000010")
        self.encrypt()
