from functools import lru_cache

from .bit_ops import permute, rotate_left, validate_int
from .constants import P10, P8


@lru_cache(maxsize=1024)
def _subkeys(key: int) -> tuple[int, int]:
    state = permute(key, 10, P10)
    left, right = state >> 5, state & 31
    # 两次均从 P10 状态出发；第二轮总位移为 2，而不是 3。
    return tuple(permute((rotate_left(left, 5, count) << 5)
                         | rotate_left(right, 5, count), 10, P8)
                 for count in (1, 2))


def generate_subkeys(key: int) -> tuple[int, int]:
    validate_int(key, 10, "密钥")
    return _subkeys(key)
