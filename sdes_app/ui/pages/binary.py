from PySide6.QtWidgets import QLabel

from sdes_app.core import trace_block
from sdes_app.ui.widgets.inputs import BitInput
from sdes_app.ui.widgets.layout import Page, actions, button, card
from sdes_app.ui.widgets.results import ResultPanel, TracePanel


class BinaryPage(Page):
    def __init__(self):
        super().__init__("二进制加解密", "单个 8 位分组，观察两轮变换如何得到结果。")
        frame, layout = card("输入分组与密钥")
        self.block = BitInput("输入分组（8 位）", 8, "10011010")
        self.key = BitInput("主密钥（10 位）", 10, "1010000010")
        layout.addWidget(self.block)
        layout.addWidget(self.key)
        self.encrypt_button = button("加密", True)
        self.decrypt_button = button("解密")
        self.example_button = button("载入手算示例")
        layout.addLayout(actions(self.encrypt_button, self.decrypt_button, self.example_button))
        self.body.addWidget(frame)
        frame, layout = card("计算结果")
        self.subkeys = QLabel("轮密钥将在计算后显示")
        self.subkeys.setObjectName("hint")
        self.subkeys.setWordWrap(True)
        self.result = ResultPanel("输出分组")
        self.trace = TracePanel()
        layout.addWidget(self.subkeys)
        layout.addWidget(self.result)
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
        self.subkeys.setText("轮密钥将在计算后显示")
        self.trace.table.set_rows(("步骤", "位串", "说明"), [])

    def calculate(self, decrypt: bool):
        try:
            block, key = self.block.value(), self.key.value()
        except ValueError:
            return
        trace = trace_block(block, key, decrypt)
        self.result.label.setText("解密明文" if decrypt else "加密密文")
        self.result.set_text(f"{trace.output:08b}")
        first, second = trace.subkeys
        self.subkeys.setText(f"K1 = {first:08b}    K2 = {second:08b}    ·    {'解密顺序 K2 → K1' if decrypt else '加密顺序 K1 → K2'}")
        self.trace.set_trace(trace)

    def encrypt(self):
        self.calculate(False)

    def decrypt(self):
        self.calculate(True)

    def example(self):
        self.block.set_text("10011010")
        self.key.set_text("1010000010")
        self.encrypt()
