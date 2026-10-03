"""共享动效策略；界面展示时间与算法计时独立。"""
import os

MIN_LOADING_MS = 600
TRANSITION_MS = 180
PROGRESS_MS = 180
SPINNER_CYCLE_MS = 1000


def reduced_motion() -> bool:
    override = os.environ.get("SDES_REDUCED_MOTION")
    if override is not None:
        return override.lower() in ("1", "true", "yes")
    if os.name == "nt":
        import ctypes
        enabled = ctypes.c_int(1)
        # 只读取 Windows 客户区动画偏好，不修改系统设置。
        if ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(enabled), 0):
            return not bool(enabled.value)
    return False
