import numpy as np
from ._base import BenchmarkFunc


class Step(BenchmarkFunc):
    """阶梯跳变函数
    5 级阶梯 (1→2→3→1.5→5)，各段叠加微弱正弦 ripple。
    难点：不连续目标完全违背 GP 的平滑性假设；跳变处方差爆炸导致过度探索。
    """
    name       = "step_func"
    global_max = 5.1
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        x      = np.asarray(x, dtype=float)
        ripple = 0.1 * np.sin(10 * x)
        val    = np.zeros_like(x)
        val    = np.where(x < -3,               1.0 + ripple, val)
        val    = np.where((x >= -3) & (x < -1), 2.0 + ripple, val)
        val    = np.where((x >= -1) & (x <  1), 3.0 + ripple, val)
        val    = np.where((x >=  1) & (x <  3), 1.5 + ripple, val)
        val    = np.where(x >=  3,              5.0 + ripple, val)
        return val
