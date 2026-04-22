import numpy as np
from ._base import BenchmarkFunc

class DeceptiveTrap(BenchmarkFunc):
    """欺骗性陷阱函数
    宽局部峰 (x≈-3) 迷惑 GP，全局尖峰藏在 x≈4 处。
    难点：宽局部峰 EI 持续高估，BO 反复落入陷阱。
    """
    name      = "deceptive_trap_func"
    global_max = 4.9048
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        broad_peak   = 2.0 * np.exp(-0.5  * (x + 3) ** 2)
        global_spike = 5.0 * np.exp(-200  * (x - 4) ** 2)
        noise_ripple = 0.3 * np.sin(15 * x)
        return broad_peak + global_spike + noise_ripple
