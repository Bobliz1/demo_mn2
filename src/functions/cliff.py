import numpy as np
from ._base import BenchmarkFunc


class Cliff(BenchmarkFunc):
    """梯度悬崖函数
    左侧 (x<1) 为斜率 1.5 的缓升直线，x=1 处值跳降至 0.5，右侧平坦。
    难点：GP 平滑假设在不连续点处严重失效；跳降点两侧采样会导致极大预测误差。
    """
    name       = "cliff_func"
    global_max = 8.1979
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        x      = np.asarray(x, dtype=float)
        left   = 1.5 * x + 6.5
        right  = 0.5 * np.ones_like(x)
        ripple = 0.2 * np.sin(8 * x)
        return np.where(x < 1.0, left + ripple, right + ripple)
