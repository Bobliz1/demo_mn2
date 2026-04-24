import numpy as np
from ._base import BenchmarkFunc


class MultiPeak(BenchmarkFunc):
    """多峰函数
    三个高度递增的高斯峰 (3→4→5)，全局最优藏在最高峰 x≈2。
    难点：较高的次优峰 (x≈0, height≈4) 极易被提前收敛。
    """
    name       = "multipeak_func"
    global_max = 5.7323
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        peak1  = 3.0 * np.exp(-0.5 * (x + 3) ** 2)
        peak2  = 4.0 * np.exp(-0.5 *  x      ** 2)
        peak3  = 5.0 * np.exp(-0.5 * (x - 2) ** 2)
        valley = 1.0 * np.exp(-0.5 * (x - 5) ** 2)
        return peak1 + peak2 + peak3 + valley
