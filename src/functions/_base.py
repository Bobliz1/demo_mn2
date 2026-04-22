"""functions/_base.py — 基准函数基类"""
import numpy as np
from abc import ABC, abstractmethod


class BenchmarkFunc(ABC):
    """所有基准函数的抽象基类。

    子类必须声明类属性：
        name       : str   函数的字符串标识符
        global_max : float 理论全局最大值
        bounds     : tuple (low, high) 一维搜索边界

    并实现 __call__(self, x) -> np.ndarray。
    """

    name:       str
    global_max: float
    bounds:     tuple  # (low, high)

    @abstractmethod
    def __call__(self, x: np.ndarray) -> np.ndarray:
        """对输入 x 求值，x 可以是标量或 1-D ndarray。"""
        ...

    # ------------------------------------------------------------------
    # 便利方法
    # ------------------------------------------------------------------
    def np_bounds(self) -> np.ndarray:
        """返回 shape=(1,2) 的 numpy bounds，适配 scipy/BO 接口。"""
        return np.array([[self.bounds[0], self.bounds[1]]])

    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__} "
                f"name={self.name!r} max={self.global_max} "
                f"bounds={self.bounds}>")
