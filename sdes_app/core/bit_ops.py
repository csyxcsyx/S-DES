def validate_int(value: int, width: int, name: str) -> None:
    if type(value) is not int or not 0 <= value < (1 << width):
        raise ValueError(f"{name}必须是 0～{(1 << width) - 1} 的整数。")


def permute(value: int, width: int, positions: tuple[int, ...]) -> int:
    """按从最高位开始、1-based 的位置表重排。"""
    result = 0
    for position in positions:
        result = (result << 1) | ((value >> (width - position)) & 1)
    return result


def rotate_left(value: int, width: int, count: int) -> int:
    count %= width
    return ((value << count) | (value >> (width - count))) & ((1 << width) - 1)


def parse_bits(text: str, width: int, name: str = "数据") -> int:
    value = text.strip()
    if len(value) != width or any(bit not in "01" for bit in value):
        raise ValueError(f"{name}必须恰好包含 {width} 个二进制位（仅 0 和 1）。")
    return int(value, 2)
