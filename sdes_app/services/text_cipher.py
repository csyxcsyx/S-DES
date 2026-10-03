import base64
import binascii
import re

from sdes_app.core import decrypt_bytes, encrypt_bytes

FORMATS = ("二进制", "十六进制", "Base64")


def ascii_bytes(text: str) -> bytes:
    try:
        return text.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError(f"第 {error.start + 1} 个字符不是 ASCII 字符；本模式仅接受 ASCII。") from error


def ascii_text(data: bytes) -> str:
    try:
        return data.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError(f"解密结果第 {error.start + 1} 个字节不是 ASCII；请核对密钥和密文。") from error


def format_ciphertext(data: bytes, format_name: str) -> str:
    if format_name == "二进制":
        return " ".join(f"{value:08b}" for value in data)
    if format_name == "十六进制":
        return data.hex(" ").upper()
    if format_name == "Base64":
        return base64.b64encode(data).decode("ascii")
    raise ValueError("未知密文格式。")


def parse_ciphertext(text: str, format_name: str) -> bytes:
    compact = re.sub(r"\s+", "", text)
    if format_name == "二进制":
        if len(compact) % 8 or any(bit not in "01" for bit in compact):
            raise ValueError("二进制密文只能包含 0、1，位数必须是 8 的倍数。")
        return bytes(int(compact[index:index + 8], 2) for index in range(0, len(compact), 8))
    if format_name == "十六进制":
        if len(compact) % 2 or any(char not in "0123456789abcdefABCDEF" for char in compact):
            raise ValueError("十六进制密文必须由成对的 0～9、A～F 组成。")
        return bytes.fromhex(compact)
    if format_name == "Base64":
        try:
            raw = base64.b64decode(compact.encode("ascii"), validate=True)
        except (ValueError, binascii.Error) as error:
            raise ValueError("Base64 密文格式或填充无效。") from error
        if base64.b64encode(raw).decode("ascii") != compact:
            raise ValueError("请使用规范的 Base64 编码（含正确的 = 填充）。")
        return raw
    raise ValueError("未知密文格式。")


def encrypt_text(text: str, key: int) -> bytes:
    return encrypt_bytes(ascii_bytes(text), key)


def decrypt_text(data: bytes, key: int) -> str:
    return ascii_text(decrypt_bytes(data, key))
