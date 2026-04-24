import numpy as np
from ._base import BenchmarkFunc


class PeriodicTrap(BenchmarkFunc):
    """周期陷阱函数
    高频余弦+正弦背景制造密集局部极值，全局尖峰叠加在 x≈4.2 处。
    难点：背景振荡与全局峰在幅度上接近，EI 极易被周期局部极值吸走。
    """
    name       = "periodic_trap_func"
    global_max = 6.8413
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        periodic = 1.5 * np.cos(3 * x) + 1.0 * np.sin(5 * x)
        peak     = 4.5 * np.exp(-80 * (x - 4.2) ** 2)
        return periodic + peak
