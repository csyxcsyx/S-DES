from dataclasses import dataclass

from .bit_ops import permute, rotate_left, validate_int
from .cipher import substitute
from .constants import EP, IP, IP_INVERSE, P10, P4, SBOX1, SBOX2
from .key_schedule import generate_subkeys


@dataclass(frozen=True)
class TraceStep:
    name: str
    bits: str
    detail: str


@dataclass(frozen=True)
class BlockTrace:
    output: int
    subkeys: tuple[int, int]
    steps: tuple[TraceStep, ...]


def trace_block(block: int, key: int, decrypt: bool = False) -> BlockTrace:
    validate_int(block, 8, "分组")
    subkeys = generate_subkeys(key)
    steps = []

    def add(name, value, width, detail):
        steps.append(TraceStep(name, f"{value:0{width}b}", detail))

    state = permute(key, 10, P10)
    add("P10", state, 10, "主密钥置换")
    for count, subkey in zip((1, 2), subkeys):
        shifted = (rotate_left(state >> 5, 5, count) << 5) | rotate_left(state & 31, 5, count)
        add(f"累计左移 {count} 位", shifted, 10, "两个 5 位分组各自循环移位")
        add(f"K{count}", subkey, 8, "移位结果经过 P8")
    state = permute(block, 8, IP)
    add("IP", state, 8, "输入分组初始置换")
    order = ((2, subkeys[1]), (1, subkeys[0])) if decrypt else ((1, subkeys[0]), (2, subkeys[1]))
    for number, (key_number, subkey) in enumerate(order, 1):
        left, right = state >> 4, state & 15
        expanded = permute(right, 4, EP)
        add(f"第{number}轮 EP", expanded, 8, f"R={right:04b} 扩展")
        mixed = expanded ^ subkey
        add(f"第{number}轮 XOR", mixed, 8, f"与 K{key_number}={subkey:08b} 异或")
        substituted = (substitute(mixed >> 4, SBOX1) << 2) | substitute(mixed & 15, SBOX2)
        add(f"第{number}轮 S-Box", substituted, 4, "外侧两位选行，内侧两位选列")
        output = permute(substituted, 4, P4)
        add(f"第{number}轮 P4", output, 4, "轮函数 F 输出")
        state = ((left ^ output) << 4) | right
        add(f"第{number}轮 fK", state, 8, "左半异或 F，右半保持")
        if number == 1:
            state = ((state & 15) << 4) | (state >> 4)
            add("SW", state, 8, "交换左右两个 4 位分组")
    output = permute(state, 8, IP_INVERSE)
    add("IP⁻¹", output, 8, "最终置换")
    return BlockTrace(output, subkeys, tuple(steps))
