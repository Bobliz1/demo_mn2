import numpy as np
from ._base import BenchmarkFunc


class FlatRegion(BenchmarkFunc):
    """平坦区域 + 尖峰
    背景近乎水平 (≈1)，全局极值是 x=0 处极窄高斯尖峰。
    难点：平坦区域采集信息量极低，GP 不确定度均匀，难以聚焦。
    """
    name       = "flat_region_func"
    global_max = 3.0
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        flat  = 1.0 * np.ones_like(np.asarray(x, float)) + 0.2 * np.sin(10 * x)
        spike = 2.0 * np.exp(-500 * x ** 2)
        return flat + spike
