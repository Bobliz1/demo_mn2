import numpy as np
from ._base import BenchmarkFunc


class OscillatingDecay(BenchmarkFunc):
    """振荡衰减函数
    高斯包络 × 正弦振荡，全局峰位于 x≈0.39（第一正半周期峰值）。
    难点：GP 长度尺度需同时适配慢包络和快振荡；远端峰幅度接近使 EI 难以聚焦。
    """
    name       = "oscillating_decay_func"
    global_max = 3.5
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        envelope    = np.exp(-0.15 * x ** 2)
        oscillation = 3.5 * np.sin(4 * x)
        baseline    = 0.1 * np.cos(x)
        return envelope * oscillation + baseline
