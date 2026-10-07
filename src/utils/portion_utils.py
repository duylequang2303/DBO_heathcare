"""Portion rounding utilities for realistic dietary servings.

Rounding gram portions to realistic multiples (e.g., 5g step) ensures that
recommended meal plans are practical for patients to measure in daily life.
"""

from typing import Literal, Union
import numpy as np


def round_portions(
    portions_g: Union[np.ndarray, list, float, int],
    step: int = 5,
    mode: Literal["nearest", "floor", "ceil"] = "nearest",
) -> np.ndarray:
    """Làm tròn mảng gram về bội số của step.

    Mặc định step=5: 71.3 -> 70g, 336.3 -> 335g, 337.6 -> 340g.
    Sai số tối đa ±2.5g ≈ ±5~15 kcal — an toàn trong dinh dưỡng lâm sàng.

    Args:
        portions_g: Giá trị hoặc mảng khẩu phần tính bằng gram (1D, 2D, list, scalar).
        step: Bước làm tròn (mặc định 5g). Phải là số nguyên dương > 0.
        mode: Chế độ làm tròn ('nearest', 'floor', 'ceil').

    Returns:
        np.ndarray với kiểu int chứa các giá trị khẩu phần đã làm tròn.

    Raises:
        ValueError: Nếu step <= 0 hoặc mode không hợp lệ.
    """
    if step <= 0:
        raise ValueError(f"step must be a positive integer > 0, got {step}")

    arr = np.asarray(portions_g, dtype=float)

    if mode == "nearest":
        rounded = np.round(arr / step) * step
    elif mode == "floor":
        rounded = np.floor(arr / step) * step
    elif mode == "ceil":
        rounded = np.ceil(arr / step) * step
    else:
        raise ValueError(f"Unknown mode '{mode}'. Expected 'nearest', 'floor', or 'ceil'.")

    return rounded.astype(int)
