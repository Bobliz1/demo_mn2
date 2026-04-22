"""functions/__init__.py
统一导出所有基准函数，并提供 REGISTRY 注册表。

用法示例
--------
from functions import REGISTRY

func = REGISTRY["deceptive_trap_func"]()   # 实例化
y = func(np.array([1.0, 2.0]))

# 或者直接按类导入
from functions import DeceptiveTrap
"""

from .deceptive_trap    import DeceptiveTrap
from .multipeak         import MultiPeak
from .flat_region       import FlatRegion
from .asymmetric        import Asymmetric
from .noisy             import Noisy
from .periodic_trap     import PeriodicTrap
from .needle_in_haystack import NeedleInHaystack
from .cliff             import Cliff
from .double_well       import DoubleWell
from .oscillating_decay import OscillatingDecay
from .step              import Step
from .valley_ridge      import ValleyRidge

# ------------------------------------------------------------------
# 注册表：name -> class（未实例化）
# ------------------------------------------------------------------
REGISTRY: dict = {
    cls.name: cls
    for cls in [
        DeceptiveTrap,
        MultiPeak,
        FlatRegion,
        Asymmetric,
        Noisy,
        PeriodicTrap,
        NeedleInHaystack,
        Cliff,
        DoubleWell,
        OscillatingDecay,
        Step,
        ValleyRidge,
    ]
}

__all__ = [
    "DeceptiveTrap", "MultiPeak", "FlatRegion", "Asymmetric", "Noisy",
    "PeriodicTrap", "NeedleInHaystack", "Cliff", "DoubleWell",
    "OscillatingDecay", "Step", "ValleyRidge",
    "REGISTRY",
]
