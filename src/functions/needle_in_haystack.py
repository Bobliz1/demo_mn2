import numpy as np
from ._base import BenchmarkFunc


class NeedleInHaystack(BenchmarkFunc):
    """草堆针函数
    全局极值是宽度极窄的高斯峰 (σ≈0.01) 叠加在近乎平坦的背景上。
    难点：随机初始化几乎不可能命中极窄峰；GP 会将峰区域视为孤立噪声点。
    """
    name       = "needle_in_haystack_func"
    global_max = 10.0
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        background = 0.1 * np.sin(x)
        needle     = 10.0 * np.exp(-5000 * (x - 2.0) ** 2)
        return background + needle
