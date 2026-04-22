import numpy as np
from ._base import BenchmarkFunc


class Noisy(BenchmarkFunc):
    """高噪声函数
    真实信号为双峰高斯，叠加高斯白噪声 (σ=0.8)，信噪比低。
    难点：GP 拟合噪声项时 α 参数敏感；噪声使 EI 在全域均匀弥散。
    """
    name       = "noisy_func"
    global_max = 4.0
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        signal = (2.0 * np.exp(-0.5 * x ** 2)
                  + 1.5 * np.exp(-0.1 * (x - 3) ** 2))
        noise  = (0.8 * np.random.randn(*x.shape)
                  if isinstance(x, np.ndarray)
                  else 0.8 * np.random.randn())
        return signal + noise
