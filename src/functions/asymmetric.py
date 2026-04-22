import numpy as np
from ._base import BenchmarkFunc


class Asymmetric(BenchmarkFunc):
    """非对称函数
    左侧为陡升直线 (斜率2)，右侧为缓降直线 (斜率-0.5)，叠加正弦噪声。
    难点：左右梯度差异极大，GP 长度尺度难以均衡；真正最大值位于分段点附近。
    """
    name       = "asymmetric_func"
    global_max = 10.0
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        left  = 2.0 * x + 4.0
        right = -0.5 * x + 8.5
        noise = 0.3 * np.sin(5 * x)
        return np.where(x < 0, left + noise, right + noise)
