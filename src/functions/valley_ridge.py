import numpy as np
from ._base import BenchmarkFunc


class ValleyRidge(BenchmarkFunc):
    """山谷山脊函数
    中央深 V 谷 (x≈0) 制造强梯度吸引采样，真正的山脊藏在远端 x≈-4.5。
    难点：BO 被 V 谷的陡峭梯度拉走，山脊处平坦导致 EI 低而难被发现。
    """
    name       = "valley_ridge_func"
    global_max = 6.1267
    bounds     = (-5.0, 5.0)

    def __call__(self, x):
        valley = -3.0 * np.exp(-0.5 *  x         ** 2)
        ridge  =  6.0 * np.exp(-0.3 * (x + 4.5)  ** 2)
        noise  =  0.2 * np.sin(7 * x)
        return valley + ridge + noise
