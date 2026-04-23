"""benchmark.py
贝叶斯优化工具层：采集函数、下一采样点建议、实验日志记录。

基准函数全部移至 functions/ 包，本文件不再定义任何测试函数。
"""

import os
import math
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.optimize import minimize

# 从 functions 包统一导入
from functions import REGISTRY

# ------------------------------------------------------------------
# 科学计数法格式化（统一、有效数字）
# ------------------------------------------------------------------

def _fmt(val, sig=3):
    """将数值格式化为科学计数法，保留 sig 位有效数字。

    规则：
    - NaN / ±inf   → "nan" / "inf"
    - val < 0      → "N/A"（表示 backward 溢出，非合法结果）
    - |val| ≥ 1e4 或 0<|val|<1e-3 → 科学计数法
    - 否则          → 普通浮点数（最多 4 位有效数字）
    """
    try:
        float_val = float(val)
    except (TypeError, ValueError):
        return str(val)

    if math.isnan(float_val):
        return "nan"
    if math.isinf(float_val):
        return "inf" if float_val > 0 else "-inf"
    if float_val < 0:
        # 负值表示 backward 溢出（找到的值超过理论最大）→ 非合法结果
        return "N/A"

    abs_val = float_val
    if abs_val >= 1e4 or (abs_val != 0 and abs_val < 1e-3):
        return f"{float_val:.1e}" if sig == 3 else f"{float_val:.{sig-1}e}"
    else:
        return f"{float_val:.4g}"


def _fmt_gap_diff(val, base_gap):
    """格式化 Gap 缩减差值；若远超基线 Gap 则为溢出，标记 N/A。"""
    try:
        fv = float(val)
    except (TypeError, ValueError):
        return "N/A"
    if fv < 0:
        return "N/A"
    # 若 gap_diff 超过基线 Gap 的 100 倍，视为溢出传播
    if fv > abs(float(base_gap)) * 100:
        return "N/A"
    return _fmt(fv)

# ------------------------------------------------------------------
# 便利函数
# ------------------------------------------------------------------

def list_functions() -> list[str]:
    """返回所有已注册基准函数的名称列表。"""
    return list(REGISTRY.keys())


def get_func(name: str):
    """按名称实例化并返回基准函数对象。"""
    if name not in REGISTRY:
        raise KeyError(f"未知函数 '{name}'，可用函数：{list_functions()}")
    return REGISTRY[name]()


# ------------------------------------------------------------------
# 采集函数 & 下一采样点
# ------------------------------------------------------------------

def expected_improvement(X, X_sample, Y_sample, gpr, xi=0.01):
    """期望改进采集函数 (EI)。"""
    if Y_sample.ndim == 1:
        Y_sample = Y_sample.reshape(-1, 1)
    mu, sigma = gpr.predict(X, return_std=True)
    mu_opt    = np.max(Y_sample)
    sigma     = sigma.reshape(-1, 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        imp = mu - mu_opt - xi
        Z   = imp / sigma
        ei  = imp * norm.cdf(Z) + sigma * norm.pdf(Z)
        ei[sigma <= 0.0] = 0.0
    return ei


def propose_next_sample(acquisition, X_sample, Y_sample, gpr, bounds,
                        n_restarts: int = 25):
    """多重随机重启 L-BFGS-B，最大化采集函数，返回下一候选点。"""
    best_x, best_val = None, -np.inf

    def neg_acq(x):
        return -acquisition(x.reshape(1, -1), X_sample, Y_sample, gpr)

    starts = np.random.uniform(
        bounds[:, 0], bounds[:, 1],
        size=(n_restarts, bounds.shape[0])
    )
    for x0 in starts:
        res = minimize(neg_acq, x0=x0, bounds=bounds, method="L-BFGS-B")
        if -res.fun > best_val:
            best_val = -res.fun
            best_x   = res.x
    return best_x


# ------------------------------------------------------------------
# 实验日志 & 可视化
# ------------------------------------------------------------------

class ExperimentLogger:
    """将实验结果写入独立 Markdown 文件，并保存可视化图像。

    输出文件路径：results/<func_name>/<func_name>_<timestamp>.md
    图像路径    ：results/<func_name>/plots/plot_<timestamp>.png
    """

    def __init__(self, func_obj, results_dir: str = "results"):
        self.func_name   = func_obj.name
        self.global_max  = func_obj.global_max
        self.results_dir = os.path.join(results_dir, self.func_name)
        self.plot_dir    = os.path.join(self.results_dir, "plots")
        os.makedirs(self.plot_dir, exist_ok=True)

    # ------------------------------------------------------------------
    def log_experiment(
        self, *,
        m_iter, n_iter, xi,
        baseline_gap, mnbo_gap,
        baseline_std=0.0, mnbo_std=0.0,
        gap_diff_avg=0.0, gap_diff_std=0.0,
        reduction_avg=0.0, reduction_std=0.0,
        n_repeats=1,
        best_config,
        samples_x, samples_y,
        best_x, best_y,
        fig,
        outer_time=0, inner_time=0,
        kernel_info="RBF",
    ):
        """记录实验结果（含多次重复统计）到独立 md 文件。"""
        ts            = datetime.now().strftime("%Y%m%d_%H%M%S")
        now_str       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        plot_filename = f"plot_{ts}.png"
        plot_path     = os.path.join(self.plot_dir, plot_filename)
        fig.savefig(plot_path, dpi=120, bbox_inches="tight")
        plt.close(fig)

        md_path = os.path.join(self.results_dir, f"{self.func_name}_{ts}.md")

        with open(md_path, "w", encoding="utf-8") as f:
            # 标题含日期时间
            f.write(f"# 实验报告：{self.func_name}\n\n")
            f.write(f"> **运行时间**：{now_str}\n")
            f.write(f"> **重复次数**：{n_repeats}\n\n")

            # 1. 核心结果表（无方差，科学计数法）
            f.write("## 1. 核心结果\n\n")
            f.write("| 指标 | 值 |\n")
            f.write("|------|----|\n")
            f.write(f"| 理论最大值 | {_fmt(self.global_max)} |\n")
            f.write(f"| 基线 Gap | {_fmt(baseline_gap)} |\n")
            f.write(f"| MN-BO Gap | {_fmt(mnbo_gap)} |\n")
            f.write(f"| Gap 缩减差值 | {_fmt_gap_diff(gap_diff_avg, baseline_gap)} |\n")
            # Gap 缩减比：仅当分母有意义且 mnbo_gap>=0 时才计算
            red_str = f"{_fmt(reduction_avg)}%" if (math.isfinite(reduction_avg) and mnbo_gap >= 0) else "N/A"
            f.write(f"| Gap 缩减比 | {red_str} |\n")
            f.write(f"\n- **最佳变换配置**：{best_config}\n\n")

            # 2. 可视化
            rel_plot = os.path.join("plots", plot_filename).replace("\\", "/")
            f.write("## 2. 可视化（选取中位数次）\n\n")
            f.write(f"![优化结果]({rel_plot})\n\n")

            # 3. 实验配置
            f.write("## 3. 实验配置\n\n")
            f.write(f"| 参数 | 值 |\n")
            f.write(f"|------|----|\n")
            f.write(f"| 重复次数 | {n_repeats} |\n")
            f.write(f"| 外层迭代 M | {m_iter} |\n")
            f.write(f"| 内层迭代 N | {n_iter} |\n")
            f.write(f"| 探索参数 xi | {xi} |\n")
            f.write(f"| GP 内核 | {kernel_info} |\n")

        return md_path

    # ------------------------------------------------------------------
    def append_summary_row(self, summary_path: str, *,
                           baseline_gap, baseline_std,
                           mnbo_gap, mnbo_std,
                           gap_diff, gap_diff_std,
                           reduction, reduction_std,
                           best_config,
                           n_repeats,
                           total_time):
        """向全局汇总表追加一行（无方差，科学计数法，标题含日期时间）。"""
        write_header = not os.path.exists(summary_path)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Gap 缩减比格式化（inf/NaN → N/A，mnbo_gap<0 视为溢出 → N/A）
        if not math.isfinite(reduction) or mnbo_gap < 0 or gap_diff < 0:
            red_str = "N/A"
        else:
            red_str = f"{_fmt(reduction)}%"
        gap_diff_fmt = _fmt_gap_diff(gap_diff, baseline_gap)

        with open(summary_path, "a", encoding="utf-8") as f:
            if write_header:
                f.write("# 实验汇总报告\n\n")
                f.write(f"> **报告生成时间**：{now_str}\n\n")
                f.write("| 函数 | 理论最大值 | 基线 Gap | MN-BO Gap"
                        " | Gap 缩减差值 | Gap 缩减比 |"
                        " 重复次数 | 耗时(s) |\n")
                f.write("|------|-----------|---------|----------|"
                        "-------------|-----------|"
                        "--------|-------|\n")

            f.write(
                f"| {self.func_name} "
                f"| {_fmt(self.global_max)} "
                f"| {_fmt(baseline_gap)} "
                f"| {_fmt(mnbo_gap)} "
                f"| {gap_diff_fmt} "
                f"| {red_str} "
                f"| {n_repeats} "
                f"| {total_time:.1f} |\n"
            )
