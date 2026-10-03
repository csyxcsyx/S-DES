from dataclasses import dataclass
from threading import Event
from time import perf_counter
from typing import Callable

from sdes_app.core import encrypt_block
from sdes_app.core.bit_ops import validate_int

Progress = Callable[[int, int], None]


@dataclass(frozen=True)
class SearchResult:
    candidates: tuple[int, ...]
    checked: int
    elapsed: float
    completed: bool


@dataclass(frozen=True)
class CollisionSummary:
    plaintext: int
    distinct_ciphertexts: int
    collision_groups: int
    max_candidates: int


@dataclass(frozen=True)
class CollisionResult:
    summaries: tuple[CollisionSummary, ...]
    groups: dict[int, tuple[int, ...]]
    selected_plaintext: int
    checked: int
    total: int
    elapsed: float
    completed: bool


def search_keys(pairs: list[tuple[int, int]], progress: Progress | None = None,
                cancel: Event | None = None) -> SearchResult:
    if not pairs:
        raise ValueError("至少提供一组明密文对。")
    for plaintext, ciphertext in pairs:
        validate_int(plaintext, 8, "明文")
        validate_int(ciphertext, 8, "密文")
    start = perf_counter()
    candidates, checked = [], 0
    for key in range(1024):
        if cancel is not None and cancel.is_set():
            break
        if all(encrypt_block(plaintext, key) == ciphertext for plaintext, ciphertext in pairs):
            candidates.append(key)
        checked += 1
        if progress and (checked % 32 == 0 or checked == 1024):
            progress(checked, 1024)
    return SearchResult(tuple(candidates), checked, perf_counter() - start, checked == 1024)


def analyze_collisions(plaintext: int, all_plaintexts: bool = False,
                       progress: Progress | None = None,
                       cancel: Event | None = None) -> CollisionResult:
    validate_int(plaintext, 8, "明文")
    start = perf_counter()
    # 先处理指定明文，使全空间任务中止时仍能展示已完成的实例。
    inputs = [plaintext] + [value for value in range(256) if value != plaintext] if all_plaintexts else [plaintext]
    total, checked = len(inputs) * 1024, 0
    summaries, selected = [], {}
    for value in inputs:
        groups = {}
        for key in range(1024):
            if cancel is not None and cancel.is_set():
                return CollisionResult(tuple(sorted(summaries, key=lambda item: item.plaintext)), selected,
                                       plaintext, checked, total, perf_counter() - start, False)
            ciphertext = encrypt_block(value, key)
            groups.setdefault(ciphertext, []).append(key)
            checked += 1
            if progress and (checked % 1024 == 0 or checked == total):
                progress(checked, total)
        if value == plaintext:
            selected = {ciphertext: tuple(keys) for ciphertext, keys in sorted(groups.items())}
        summaries.append(CollisionSummary(value, len(groups), sum(len(keys) > 1 for keys in groups.values()),
                                          max(map(len, groups.values()))))
    return CollisionResult(tuple(sorted(summaries, key=lambda item: item.plaintext)), selected,
                           plaintext, checked, total, perf_counter() - start, True)
