import csv
from dataclasses import dataclass
from pathlib import Path

from sdes_app.core import decrypt_block, encrypt_block
from sdes_app.core.bit_ops import parse_bits

COLUMNS = ("plaintext", "key", "ciphertext")


@dataclass(frozen=True)
class CrossCheck:
    line: int
    plaintext: str
    key: str
    ciphertext: str
    actual_ciphertext: str
    actual_plaintext: str
    error: str = ""

    @property
    def passed(self) -> bool:
        return not self.error and self.ciphertext == self.actual_ciphertext and self.plaintext == self.actual_plaintext


def verify_csv(path: str | Path) -> list[CrossCheck]:
    results = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(COLUMNS):
            raise ValueError("CSV 表头必须按顺序为 plaintext,key,ciphertext。")
        for row in reader:
            plaintext, key, ciphertext = (str(row.get(column) or "").strip() for column in COLUMNS)
            try:
                if None in row:
                    raise ValueError("该行列数超过 3。")
                p = parse_bits(plaintext, 8, "明文")
                k = parse_bits(key, 10, "密钥")
                c = parse_bits(ciphertext, 8, "密文")
                results.append(CrossCheck(reader.line_num, plaintext, key, ciphertext,
                                          f"{encrypt_block(p, k):08b}", f"{decrypt_block(c, k):08b}"))
            except ValueError as error:
                results.append(CrossCheck(reader.line_num, plaintext, key, ciphertext, "", "", str(error)))
    if not results:
        raise ValueError("CSV 中至少需要一条测试数据。")
    return results


def export_vectors(path: str | Path, pairs: list[tuple[int, int]]) -> None:
    rows = [(f"{p:08b}", f"{key:010b}", f"{encrypt_block(p, key):08b}") for p, key in pairs]
    write_csv(path, COLUMNS, rows)


def write_csv(path: str | Path, columns, rows) -> None:
    with Path(path).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)
