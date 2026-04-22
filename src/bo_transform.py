"""bo_transform.py
目标空间变换算子库（连续参数化版本 v2）。

外层参数 ∈ [0,1]^D，每维控制一个连续自由度：
  - 强度参数（gate）：∈ [0,1]，控制该算子的启用程度
    gate=0 → 算子退化为恒等（不选）
    gate=1 → 算子全强度应用
  - 部分算子有额外连续参数（alpha、power 等），独立控制变换形态

参数约定：
    - 所有参数 ∈ [0,1]，由 _map() 映射到物理范围
"""

import numpy as np


# ---------------------------------------------------------------------------
# 基类
# ---------------------------------------------------------------------------

class BaseOperator:
    def forward(self, y): raise NotImplementedError
    def backward(self, y_prime): raise NotImplementedError


class IdentityOperator(BaseOperator):
    """恒等算子（gate=0 时的fallback）。"""
    def forward(self, y): return y
    def backward(self, y_prime): return y_prime


# ---------------------------------------------------------------------------
# 连续算子
# ---------------------------------------------------------------------------

class LogWarper(BaseOperator):
    r"""
    广义对数变换：y' = sign(y) * log(1 + α * |y|)

    当 alpha→0 时退化为恒等。
    当 alpha=1 时为经典 log(1+|y|)。
    """
    def __init__(self, alpha: float):
        self.alpha = float(alpha)

    def forward(self, y):
        return np.sign(y) * np.log1p(self.alpha * np.abs(y))

    def backward(self, y_prime):
        # 数值稳定性：裁剪极端值，防止 exp() 溢出
        y_prime = np.clip(y_prime, -700, 700)
        return np.sign(y_prime) * ((np.exp(np.abs(y_prime)) - 1) / (self.alpha + 1e-12))


class StandardScaler(BaseOperator):
    r"""
    可缩放的标准化：y' = (y - μ - shift*σ) / (σ * s)

    当 shift→0 且 s→1 时退化为标准标准化（不一定是恒等，但形态固定）。
    当 s 极大时方差压缩 → 接近恒等映射。
    """
    def __init__(self, y_init: np.ndarray, shift: float, scale_factor: float):
        self.mu    = float(np.mean(y_init))
        self.sigma = float(np.std(y_init)) + 1e-8
        self.shift = float(shift)
        self.scale_factor = float(scale_factor)

    def forward(self, y):
        return (y - self.mu - self.shift * self.sigma) / (self.sigma * self.scale_factor)

    def backward(self, y_prime):
        return y_prime * (self.sigma * self.scale_factor) + self.mu + self.shift * self.sigma


class PowerTransform(BaseOperator):
    r"""
    幂变换：y' = sign(y) * |y|^p

    当 p→1 时退化为恒等。
    当 p<1 压缩大值，p>1 拉伸大值。
    """
    def __init__(self, power: float):
        self.power = float(power)

    def forward(self, y):
        return np.sign(y) * np.power(np.abs(y) + 1e-12, self.power)

    def backward(self, y_prime):
        p = self.power
        if abs(p) < 1e-8:
            p = 1e-8
        return np.sign(y_prime) * np.power(np.abs(y_prime) + 1e-12, 1.0 / p)


class SigmoidWarper(BaseOperator):
    r"""
    Sigmoid 压缩：y' = 1 / (1 + exp(-k * (y - c)))

    当 k→0 时退化为恒等（输出≈0.5 常数）。
    当 k 极大时趋于阶跃函数。
    中心 c 决定「中间区间」的位置。
    """
    def __init__(self, steepness: float, center: float):
        self.steepness = float(steepness)
        self.center    = float(center)

    def _safe_sigmoid(self, z):
        return np.where(z >= 0,
                        1.0 / (1.0 + np.exp(-z)),
                        np.exp(z) / (1.0 + np.exp(z)))

    def forward(self, y):
        z = self.steepness * (y - self.center)
        return self._safe_sigmoid(z)

    def backward(self, y_prime):
        y_prime = np.clip(y_prime, 1e-10, 1 - 1e-10)
        return self.center + np.log(y_prime / (1.0 - y_prime)) / (self.steepness + 1e-12)


class MinMaxScaler(BaseOperator):
    r"""
    Min-Max 线性映射：y' = (y - lo) / (hi - lo) * target_range

    当 target_high → 1 且 lo/hi 覆盖数据范围时为标准归一化。
    target_high 极大时 y' 整体压缩 → 接近恒等。
    """
    def __init__(self, y_init: np.ndarray, target_high: float):
        self.low  = float(np.min(y_init))
        self.high = float(np.max(y_init))
        self.range_val = self.high - self.low + 1e-12
        self.target_high = float(target_high)

    def forward(self, y):
        normalized = (y - self.low) / self.range_val
        return normalized * self.target_high

    def backward(self, y_prime):
        return y_prime / self.target_high * self.range_val + self.low


# ---------------------------------------------------------------------------
# 离散算子（无自然连续退化路径，用独立 gate 控制）
# ---------------------------------------------------------------------------

class RankTransform(BaseOperator):
    r"""
    百分位秩变换：y' = rank(y) / (N-1)

    完全离散（非连续可微），无连续退化路径。
    由独立 gate 参数控制「是否启用」。
    优势：完全消除异常值和分布偏态。
    """
    def __init__(self, y_init: np.ndarray):
        self.y_init_flat = np.asarray(y_init).flatten()
        self.n = len(self.y_init_flat)
        self.ranks = np.argsort(np.argsort(self.y_init_flat)) / max(1, self.n - 1)

    def forward(self, y):
        y = np.asarray(y).flatten()
        ranks = np.zeros_like(y)
        for i, val in enumerate(y):
            ranks[i] = np.searchsorted(np.sort(self.y_init_flat), val) / max(1, self.n - 1)
        return ranks.reshape(-1, 1)

    def backward(self, y_prime):
        y_prime = np.asarray(y_prime).flatten()
        idx = np.clip(y_prime * (self.n - 1), 0, self.n - 1).astype(int)
        return np.array([self.y_init_flat[min(i, self.n - 1)] for i in idx]).reshape(-1, 1)


# ---------------------------------------------------------------------------
# 参数空间定义（外层维度 D = 12）
# ---------------------------------------------------------------------------
# 外层参数向量含义：
#   p[0]  → LogWarper 强度 g_log  ∈ [0,1]         （0=恒等）
#   p[1]  → LogWarper alpha      ∈ [0.1, 10.0]   （连续形态参数）
#   p[2]  → StandardScaler 强度 g_scl ∈ [0,1]
#   p[3]  → StandardScaler shift ∈ [-1.0, 1.0]σ
#   p[4]  → StandardScaler s     ∈ [0.2, 5.0]
#   p[5]  → PowerTransform 强度 g_pow ∈ [0,1]
#   p[6]  → PowerTransform power  ∈ [-1.0, 3.0]
#   p[7]  → SigmoidWarper 强度 g_sig ∈ [0,1]
#   p[8]  → SigmoidWarper k    ∈ [0.01, 10.0]
#   p[9]  → SigmoidWarper c    ∈ [-5.0, 5.0]σ
#   p[10] → MinMaxScaler 强度 g_mm  ∈ [0,1]
#   p[11] → RankTransform 启用 gate ∈ [0,1]      （离散，0=禁用，1=启用）

PARAM_SPEC = [
    # (维度索引, 名称,              物理最小, 物理最大,     是否为强度 gate)
    (0,  "log_gate",       0.0,    1.0,    True),   # g_log
    (1,  "log_alpha",      0.1,   10.0,   False),  # alpha
    (2,  "scl_gate",       0.0,    1.0,    True),   # g_scl
    (3,  "scl_shift",     -1.0,    1.0,   False),  # shift (σ 单位)
    (4,  "scl_scale",      0.2,    5.0,   False),  # scale
    (5,  "pow_gate",       0.0,    1.0,    True),   # g_pow
    (6,  "pow_power",     -1.0,    3.0,   False),  # power
    (7,  "sig_gate",       0.0,    1.0,    True),   # g_sig
    (8,  "sig_steep",      0.01,  10.0,   False),  # k
    (9,  "sig_center",    -5.0,    5.0,   False),  # c (σ 单位)
    (10, "mm_gate",        0.0,    1.0,    True),   # g_mm
    (11, "rank_gate",      0.0,    1.0,    True),   # rank 离散 gate
]

N_CONTINUOUS = len(PARAM_SPEC)  # = 12


def _map(idx: int, p: float) -> float:
    """将 p ∈ [0,1] 映射到物理范围。"""
    lo = PARAM_SPEC[idx][2]
    hi = PARAM_SPEC[idx][3]
    return lo + p * (hi - lo)


# ---------------------------------------------------------------------------
# 流水线
# ---------------------------------------------------------------------------

class TransformerPipeline:
    """按顺序执行多个算子的流水线。"""
    def __init__(self, operators):
        self.operators = list(operators)

    def forward(self, y):
        y_t = np.asarray(y).copy()
        for op in self.operators:
            y_t = op.forward(y_t)
        return y_t

    def backward(self, y_prime):
        y_r = np.asarray(y_prime).copy()
        for op in reversed(self.operators):
            y_r = op.backward(y_r)
        return y_r


class WrappedTarget:
    """包装后的目标函数：raw_func(x) → pipeline.forward()"""
    def __init__(self, raw_func, pipeline):
        self.raw_func = raw_func
        self.pipeline = pipeline

    def __call__(self, x):
        y_raw = self.raw_func(x)
        return self.pipeline.forward(y_raw)


# ---------------------------------------------------------------------------
# 核心：参数向量 → 算子流水线
# ---------------------------------------------------------------------------

def params_to_pipeline(params: np.ndarray, y_init: np.ndarray):
    """
    将外层参数向量 params ∈ [0,1]^12 映射为 TransformerPipeline。

    策略：
    - 每个带 gate 的算子：gate > 0.01 时实例化，否则跳过（→ 恒等）
    - 所有算子按固定顺序串联：Log → Scl → Pow → Sig → MinMax → Rank
    - 算子强度通过 forward() 输出的缩放隐式控制（不改变 forward 本身，
      强度控制的是「是否应用」，但形态参数保持）

    参数：
        params : np.ndarray  shape=(12,)，每个分量 ∈ [0,1]
        y_init : np.ndarray  内层 BO 的初始观测，用于 StandardScaler 等

    返回：
        (TransformerPipeline, config_str)
    """
    p = np.asarray(params).flatten()
    ops = []
    config_parts = []

    # ---- LogWarper ----
    g_log = float(p[0])
    if g_log > 0.01:
        alpha = _map(1, float(p[1]))
        ops.append(LogWarper(alpha))
        config_parts.append(f"Log(g={g_log:.2f},α={alpha:.2f})")

    # ---- StandardScaler ----
    g_scl = float(p[2])
    if g_scl > 0.01:
        shift = _map(3, float(p[3]))
        scale = _map(4, float(p[4]))
        ops.append(StandardScaler(y_init, shift, scale))
        config_parts.append(f"Scaler(g={g_scl:.2f},s={scale:.2f})")

    # ---- PowerTransform ----
    g_pow = float(p[5])
    if g_pow > 0.01:
        power = _map(6, float(p[6]))
        ops.append(PowerTransform(power))
        config_parts.append(f"Power(g={g_pow:.2f},p={power:.2f})")

    # ---- SigmoidWarper ----
    g_sig = float(p[7])
    if g_sig > 0.01:
        k = _map(8, float(p[8]))
        c = _map(9, float(p[9]))
        ops.append(SigmoidWarper(k, c))
        config_parts.append(f"Sigmoid(g={g_sig:.2f},k={k:.2f})")

    # ---- MinMaxScaler ----
    g_mm = float(p[10])
    if g_mm > 0.01:
        ops.append(MinMaxScaler(y_init, target_high=1.0))
        config_parts.append(f"MinMax(g={g_mm:.2f})")

    # ---- RankTransform ----
    g_rank = float(p[11])
    if g_rank > 0.5:  # 离散门控：阈值 0.5
        ops.append(RankTransform(y_init))
        config_parts.append("Rank(启用)")

    pipe = TransformerPipeline(ops)
    config_str = ", ".join(config_parts) if config_parts else "Identity"
    return pipe, config_str


def get_outer_bounds() -> np.ndarray:
    """返回外层连续搜索空间边界，shape=(12, 2)。"""
    return np.array([[0.0, 1.0]] * N_CONTINUOUS)


# ---------------------------------------------------------------------------
# 算子一览
# ---------------------------------------------------------------------------
OPERATOR_INFO = {
    "log_gate":   ("LogWarper",       "g ∈ [0,1]",        "强度，0=恒等"),
    "log_alpha":  ("LogWarper",       "α ∈ [0.1, 10.0]",  "对数压缩强度"),
    "scl_gate":   ("StandardScaler",  "g ∈ [0,1]",        "强度，0=恒等"),
    "scl_shift":  ("StandardScaler",  "shift ∈ [-1σ, 1σ]","均值偏移"),
    "scl_scale":  ("StandardScaler",  "s ∈ [0.2, 5.0]",   "方差缩放"),
    "pow_gate":   ("PowerTransform",  "g ∈ [0,1]",        "强度，0=恒等"),
    "pow_power":  ("PowerTransform",  "p ∈ [-1, 3]",      "幂指数"),
    "sig_gate":   ("SigmoidWarper",   "g ∈ [0,1]",        "强度，0=恒等"),
    "sig_steep":  ("SigmoidWarper",   "k ∈ [0.01, 10.0]","陡度"),
    "sig_center": ("SigmoidWarper",   "c ∈ [-5σ, 5σ]",    "中心"),
    "mm_gate":    ("MinMaxScaler",    "g ∈ [0,1]",        "强度，0=恒等"),
    "rank_gate":  ("RankTransform",    "g ∈ [0,1]",        "离散gate，>0.5启用"),
}
