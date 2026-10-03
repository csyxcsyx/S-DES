from functools import lru_cache

from .bit_ops import permute, validate_int
from .constants import EP, IP, IP_INVERSE, P4, SBOX1, SBOX2
from .key_schedule import generate_subkeys

_INITIAL = tuple(permute(value, 8, IP) for value in range(256))
_FINAL = tuple(permute(value, 8, IP_INVERSE) for value in range(256))


def substitute(nibble: int, box: tuple[tuple[int, ...], ...]) -> int:
    # 外侧两位选行，内侧两位选列。
    row = ((nibble & 8) >> 2) | (nibble & 1)
    column = (nibble >> 1) & 3
    return box[row][column]


def round_function(right: int, subkey: int) -> int:
    mixed = permute(right, 4, EP) ^ subkey
    substituted = (substitute(mixed >> 4, SBOX1) << 2) | substitute(mixed & 15, SBOX2)
    return permute(substituted, 4, P4)


@lru_cache(maxsize=256)
def _round_table(subkey: int) -> tuple[int, ...]:
    return tuple(round_function(right, subkey) for right in range(16))


def _crypt(block: int, first: int, second: int) -> int:
    state = _INITIAL[block]
    left, right = state >> 4, state & 15
    left ^= _round_table(first)[right]
    left, right = right, left
    left ^= _round_table(second)[right]
    return _FINAL[(left << 4) | right]


def encrypt_block(block: int, key: int) -> int:
    validate_int(block, 8, "分组")
    return _crypt(block, *generate_subkeys(key))


def decrypt_block(block: int, key: int) -> int:
    validate_int(block, 8, "分组")
    first, second = generate_subkeys(key)
    return _crypt(block, second, first)


def _transform_bytes(data: bytes, key: int, decrypt: bool) -> bytes:
    if not isinstance(data, bytes):
        raise ValueError("数据必须是 bytes。")
    first, second = generate_subkeys(key)
    if decrypt:
        first, second = second, first
    # 同一个密钥的字节映射只计算一次；translate 不损失控制字节。
    mapping = bytes(_crypt(block, first, second) for block in range(256))
    return data.translate(mapping)


def encrypt_bytes(data: bytes, key: int) -> bytes:
    return _transform_bytes(data, key, False)


def decrypt_bytes(data: bytes, key: int) -> bytes:
    return _transform_bytes(data, key, True)
