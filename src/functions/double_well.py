import numpy as np
from ._base import BenchmarkFunc


class DoubleWell(BenchmarkFunc):
    """双井对称函数
    两个等高对称全局峰分别位于 x≈-3 和 x≈3，中间有轻微凹陷。
    难点：对称结构使 GP 无法区分两峰优劣；BO 常反复收敛到先采到的那个峰。
    """
    name       = "double_well_func"
    global_max = 4.0
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        left    =  4.0 * np.exp(-0.8 * (x + 3) ** 2)
        right   =  4.0 * np.exp(-0.8 * (x - 3) ** 2)
        repulse = -0.5 * np.exp(-0.5 *  x      ** 2)
        return left + right + repulse
