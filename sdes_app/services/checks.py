from dataclasses import dataclass
from threading import Event
from time import perf_counter

from sdes_app.core import decrypt_block, encrypt_block, generate_subkeys, trace_block
from .experiments import Progress


@dataclass(frozen=True)
class CheckRow:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class CheckReport:
    rows: tuple[CheckRow, ...]
    checked: int
    elapsed: float
    completed: bool


def run_checks(exhaustive: bool = False, progress: Progress | None = None,
               cancel: Event | None = None) -> CheckReport:
    start = perf_counter()
    rows = []
    key, plaintext, ciphertext = 0b1010000010, 0b10011010, 0b11101111
    checks = (
        ("手算子密钥", lambda: generate_subkeys(key) == (0b10100100, 0b10010010), "K1=10100100，K2=10010010"),
        ("手算加密结果", lambda: encrypt_block(plaintext, key) == ciphertext, "10011010 → 11101111"),
        ("手算解密结果", lambda: decrypt_block(ciphertext, key) == plaintext, "11101111 → 10011010"),
        ("过程记录一致", lambda: trace_block(plaintext, key).output == ciphertext, "步骤输出与加密 API 一致"),
    )
    for name, function, detail in checks:
        rows.append(CheckRow(name, function(), detail))
    checked = 0
    if exhaustive:
        for candidate in range(1024):
            for block in range(256):
                if cancel is not None and cancel.is_set():
                    rows.append(CheckRow("全空间验证", False, f"已取消，仅检查 {checked}/262144 组"))
                    return CheckReport(tuple(rows), checked, perf_counter() - start, False)
                output = encrypt_block(block, candidate)
                if decrypt_block(output, candidate) != block:
                    rows.append(CheckRow("全空间验证", False, f"失败：P={block:08b}，K={candidate:010b}"))
                    return CheckReport(tuple(rows), checked + 1, perf_counter() - start, True)
                checked += 1
            if progress:
                progress(checked, 262144)
        rows.append(CheckRow("全空间验证", True, "262144 组加解密往返全部通过"))
    return CheckReport(tuple(rows), checked, perf_counter() - start, True)
