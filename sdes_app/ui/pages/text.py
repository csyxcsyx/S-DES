from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel

from sdes_app.core import decrypt_bytes, encrypt_bytes
from sdes_app.services.text_cipher import FORMATS, ascii_bytes, ascii_text, format_ciphertext, parse_ciphertext
from sdes_app.ui.widgets.inputs import BitInput, InputField
from sdes_app.ui.widgets.layout import Page, actions, button, card
from sdes_app.ui.widgets.results import DataTable, ResultPanel


class TextPage(Page):
    def __init__(self):
        super().__init__("ASCII 文本", "每个 ASCII 字符对应一个字节，逐字节应用同一套 S-DES 算法。")
        frame, layout = card("文本、密钥与密文格式")
        self.plaintext = InputField("ASCII 明文", "支持空格、换行和 ASCII 控制字符。", multiline=True)
        self.plaintext.editor.setFixedHeight(100)
        self.plaintext.set_text("This is a test")
        self.key = BitInput("主密钥（10 位）", 10, "1010000010")
        self.format = QComboBox()
        self.format.addItems(FORMATS)
        self.format.setAccessibleName("密文格式")
        format_label = QLabel("密文格式")
        format_label.setBuddy(self.format)
        key_row = QHBoxLayout()
        key_row.setSpacing(20)
        key_row.addWidget(self.key, 1)
        key_row.addLayout(actions(format_label, self.format), 1)
        layout.addLayout(key_row)
        self.ciphertext = InputField("密文", "可粘贴对应格式的密文。空格和换行可作为格式分隔符。", multiline=True)
        self.ciphertext.editor.setFixedHeight(100)
        text_row = QHBoxLayout()
        text_row.setSpacing(20)
        text_row.addWidget(self.plaintext, 1)
        text_row.addWidget(self.ciphertext, 1)
        layout.addLayout(text_row)
        self.encrypt_button = button("加密文本", True)
        self.decrypt_button = button("解密密文")
        self.copy_cipher = button("复制密文")
        self.copy_cipher.clicked.connect(self.copy_ciphertext)
        layout.addLayout(actions(self.encrypt_button, self.decrypt_button, self.copy_cipher))
        self.body.addWidget(frame)
        frame, layout = card("恢复文本与字节明细")
        self.recovered = ResultPanel("恢复的 ASCII 明文", mono=False, height=70)
        layout.addWidget(self.recovered)
        self.byte_status = QLabel("字节明细将在计算后显示")
        self.byte_status.setObjectName("hint")
        self.byte_status.setWordWrap(True)
        self.table = DataTable(("序号", "ASCII 字符（转义显示）", "明文字节", "密文字节"), 160)
        layout.addWidget(self.byte_status)
        layout.addWidget(self.table)
        self.body.addWidget(frame)
        self.finish()
        self._old_format = self.format.currentText()
        self.encrypt_button.clicked.connect(self.encrypt)
        self.decrypt_button.clicked.connect(self.decrypt)
        self.format.currentTextChanged.connect(self.convert_format)
        self.key.editor.textChanged.connect(self.clear_results)
        self.ciphertext.editor.textChanged.connect(self.clear_results)
        self.plaintext.editor.textChanged.connect(self.clear_results)

    def clear_results(self):
        self.recovered.set_text("")
        self.table.set_rows(("序号", "ASCII 字符（转义显示）", "明文字节", "密文字节"), [])
        self.byte_status.setText("字节明细将在计算后显示")

    def show_bytes(self, plain: bytes, cipher: bytes):
        self.table.set_rows(("序号", "ASCII 字符（转义显示）", "明文字节", "密文字节"),
                            [(index + 1, repr(chr(p)), f"{p:08b}", f"{c:08b}")
                             for index, (p, c) in enumerate(zip(plain, cipher))])
        self.byte_status.setText(f"共 {len(plain)} 字节 · 密文按字节完整保留，控制字符以转义形式显示")

    def encrypt(self):
        self.plaintext.clear_error()
        self.ciphertext.clear_error()
        try:
            key = self.key.value()
        except ValueError:
            return
        try:
            plain = ascii_bytes(self.plaintext.text())
        except ValueError as error:
            self.plaintext.show_error(str(error))
            return
        cipher = encrypt_bytes(plain, key)
        self.ciphertext.set_text(format_ciphertext(cipher, self.format.currentText()))
        self.show_bytes(plain, cipher)

    def decrypt(self):
        self.ciphertext.clear_error()
        try:
            key = self.key.value()
        except ValueError:
            return
        try:
            cipher = parse_ciphertext(self.ciphertext.text(), self.format.currentText())
        except ValueError as error:
            self.ciphertext.show_error(str(error))
            return
        plain = decrypt_bytes(cipher, key)
        self.show_bytes(plain, cipher)
        try:
            self.recovered.set_text(ascii_text(plain))
        except ValueError as error:
            self.recovered.set_text("")
            self.ciphertext.show_error(str(error) + " 字节明细仍完整显示。")

    def convert_format(self, new_format):
        try:
            raw = parse_ciphertext(self.ciphertext.text(), self._old_format)
        except ValueError as error:
            self.format.blockSignals(True)
            self.format.setCurrentText(self._old_format)
            self.format.blockSignals(False)
            self.ciphertext.show_error(f"无法转换：{error}")
            return
        self._old_format = new_format
        self.ciphertext.set_text(format_ciphertext(raw, new_format))

    def copy_ciphertext(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.ciphertext.text())
        self.byte_status.setText("已复制密文；复制内容按当前格式完整保留。")
