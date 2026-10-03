"""独立的字符串参考实现，仅供测试；不复用产品中的表或位运算。"""
from functools import lru_cache


def choose(bits, positions):
    return "".join(bits[position - 1] for position in positions)


@lru_cache(maxsize=1024)
def reference_keys(key):
    initial = choose(f"{key:010b}", (3, 5, 2, 7, 4, 10, 1, 9, 8, 6))
    keys = []
    for amount in (1, 2):
        halves = (initial[:5], initial[5:])
        shifted = "".join(half[amount:] + half[:amount] for half in halves)
        keys.append(choose(shifted, (6, 3, 7, 4, 8, 5, 10, 9)))
    return tuple(keys)


def xor(left, right):
    return "".join("0" if a == b else "1" for a, b in zip(left, right))


def reference_encrypt(block, key):
    boxes = (((1, 0, 3, 2), (3, 2, 1, 0), (0, 2, 1, 3), (3, 1, 0, 2)),
             ((0, 1, 2, 3), (2, 3, 1, 0), (3, 0, 1, 2), (2, 1, 0, 3)))
    state = choose(f"{block:08b}", (2, 6, 3, 1, 4, 8, 5, 7))
    for index, round_key in enumerate(reference_keys(key)):
        left, right = state[:4], state[4:]
        expanded = choose(right, (4, 1, 2, 3, 2, 3, 4, 1))
        mixed = xor(expanded, round_key)
        output = ""
        for box, part in zip(boxes, (mixed[:4], mixed[4:])):
            row = int(part[0] + part[-1], 2)
            column = int(part[1:3], 2)
            output += f"{box[row][column]:02b}"
        state = xor(left, choose(output, (2, 4, 3, 1))) + right
        if index == 0:
            state = state[4:] + state[:4]
    return int(choose(state, (4, 1, 3, 5, 7, 2, 8, 6)), 2)
