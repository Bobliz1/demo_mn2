"""bo_transform.py
目标空间变换算子库（连续参数化版本 v3.2）。

外层参数 ∈ [0,1]^8，每维控制一个连续自由度：
  - 强度参数（gate）：控制算子启用程度 (0=恒等, 1=全开启)
  - 形态参数：控制具体的变换程度（如对数压缩率、幂指数等）

有序加工链 (Ordered Operator Chain):
    LogWarper -> PowerWarper -> StandardScaler -> MinMaxScaler
"""

import numpy as np

# ---------------------------------------------------------------------------
# 基类
# ---------------------------------------------------------------------------

class BaseOperator:
    def forward(self, y): raise NotImplementedError
    def backward(self, y_prime): raise NotImplementedError


class IdentityOperator(BaseOperator):
    def forward(self, y): return y
    def backward(self, y_prime): return y_prime


# ---------------------------------------------------------------------------
# 连续算子
# ---------------------------------------------------------------------------

class LogWarper(BaseOperator):
    """广义对数变换：y' = sign(y) * log(1 + α * |y|)"""
    def __init__(self, alpha: float):
        self.alpha = float(alpha)

    def forward(self, y):
        return np.sign(y) * np.log1p(self.alpha * np.abs(y))

    def backward(self, y_prime):
        y_prime = np.clip(y_prime, -100, 100)
        alpha_safe = max(self.alpha, 1e-6)
        return np.sign(y_prime) * ((np.exp(np.abs(y_prime)) - 1) / alpha_safe)


class PowerWarper(BaseOperator):
    """对称幂变换：y' = sign(y) * |y|^p"""
    def __init__(self, p: float):
        self.p = float(p)

    def forward(self, y):
        # 加上微小偏移防止 0 的幂运算异常
        return np.sign(y) * np.power(np.abs(y) + 1e-12, self.p)

    def backward(self, y_prime):
        # 逆变换 y = sign(y') * |y'|^(1/p)
        p_safe = max(self.p, 1e-6)
        # 数值保护：防止 1/p 导致巨大的溢出，backward 阶段进行适度裁剪
        y_prime = np.clip(y_prime, -1e6, 1e6)
        return np.sign(y_prime) * np.power(np.abs(y_prime) + 1e-12, 1.0 / p_safe)


class StandardScaler(BaseOperator):
    """均值/方差对齐：y' = (y - μ - shift*σ) / (σ * s)"""
    def __init__(self, y_init: np.ndarray, shift: float, scale_factor: float):
        self.mu    = float(np.mean(y_init))
        self.sigma = float(np.std(y_init)) + 1e-8
        self.shift = float(shift)
        self.scale_factor = float(scale_factor)

    def forward(self, y):
        return (y - self.mu - self.shift * self.sigma) / (self.sigma * self.scale_factor)

    def backward(self, y_prime):
        return y_prime * (self.sigma * self.scale_factor) + self.mu + self.shift * self.sigma


class MinMaxScaler(BaseOperator):
    """硬边界归一化：将数据线性映射到 [0, target_high]"""
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
# 参数空间定义 (D = 8)
# ---------------------------------------------------------------------------

PARAM_SPEC = [
    # (索引, 名称,              物理最小, 物理最大,     是否为强度 gate)
    (0,  "log_gate",       0.0,    1.0,    True),   # g_log
    (1,  "log_alpha",      0.1,   10.0,   False),  # alpha (对数压缩)
    (2,  "pow_gate",       0.0,    1.0,    True),   # g_pow
    (3,  "pow_index",      0.1,    5.0,   False),  # p (幂指数)
    (4,  "scl_gate",       0.0,    1.0,    True),   # g_scl
    (5,  "scl_shift",     -1.0,    1.0,   False),  # shift (σ 单位)
    (6,  "scl_scale",      0.2,    5.0,   False),  # scale factor
    (7,  "mm_gate",        0.0,    1.0,    True),   # g_mm
]

N_CONTINUOUS = len(PARAM_SPEC)  # = 8


def _map(idx: int, p: float) -> float:
    """将 p ∈ [0,1] 映射到物理范围。"""
    lo, hi = PARAM_SPEC[idx][2], PARAM_SPEC[idx][3]
    return lo + p * (hi - lo)


# ---------------------------------------------------------------------------
# 流水线与核心逻辑
# ---------------------------------------------------------------------------

class TransformerPipeline:
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
    """包装后的目标函数：raw_func(x) → pipeline.forward(raw_func(x))"""
    def __init__(self, raw_func, pipeline):
        self.raw_func = raw_func
        self.pipeline = pipeline

    def __call__(self, x):
        y_raw = self.raw_func(x)
        return self.pipeline.forward(y_raw)


def params_to_pipeline(params: np.ndarray, y_init: np.ndarray):
    """将外层 8D 向量转换为加工流水线。顺序：Log -> Power -> Scl -> MM"""
    p = np.asarray(params).flatten()
    ops = []
    config_parts = []

    # 1. Log
    if p[0] > 0.01:
        alpha = _map(1, p[1])
        ops.append(LogWarper(alpha))
        config_parts.append(f"Log(g={p[0]:.2f},α={alpha:.2f})")

    # 2. Power
    if p[2] > 0.01:
        pow_idx = _map(3, p[3])
        ops.append(PowerWarper(pow_idx))
        config_parts.append(f"Pow(g={p[2]:.2f},p={pow_idx:.2f})")

    # 3. Scaler
    if p[4] > 0.01:
        shift = _map(5, p[5])
        scale = _map(6, p[6])
        ops.append(StandardScaler(y_init, shift, scale))
        config_parts.append(f"Scl(g={p[4]:.2f},s={scale:.2f})")

    # 4. MinMaxScaler
    if p[7] > 0.01:
        ops.append(MinMaxScaler(y_init, target_high=1.0))
        config_parts.append(f"MM(g={p[7]:.2f})")

    pipe = TransformerPipeline(ops)
    config_str = ", ".join(config_parts) if config_parts else "Identity"
    return pipe, config_str


def get_outer_bounds() -> np.ndarray:
    return np.array([[0.0, 1.0]] * N_CONTINUOUS)


OPERATOR_INFO = {
    "log_gate":   ("LogWarper",       "g ∈ [0,1]",        "对数算子强度"),
    "log_alpha":  ("LogWarper",       "α ∈ [0.1, 10.0]",  "压缩强度"),
    "pow_gate":   ("PowerWarper",     "g ∈ [0,1]",        "幂变换强度"),
    "pow_index":  ("PowerWarper",     "p ∈ [0.1, 5.0]",   "幂指数 (p>1拉伸, p<1压缩)"),
    "scl_gate":   ("StandardScaler",  "g ∈ [0,1]",        "标准化强度"),
    "scl_shift":  ("StandardScaler",  "shift ∈ [-1σ, 1σ]","均值偏移"),
    "scl_scale":  ("StandardScaler",  "s ∈ [0.2, 5.0]",   "方差缩放"),
    "mm_gate":    ("MinMaxScaler",    "g ∈ [0,1]",        "归一化强度"),
}
