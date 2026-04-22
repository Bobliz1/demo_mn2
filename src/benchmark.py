"""benchmark.py
贝叶斯优化工具层：采集函数、下一采样点建议、实验日志记录。

基准函数全部移至 functions/ 包，本文件不再定义任何测试函数。
"""

import os
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.optimize import minimize

# 从 functions 包统一导入
from functions import REGISTRY

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
        plot_filename = f"plot_{ts}.png"
        plot_path     = os.path.join(self.plot_dir, plot_filename)
        fig.savefig(plot_path, dpi=120, bbox_inches="tight")
        plt.close(fig)

        md_path = os.path.join(self.results_dir, f"{self.func_name}_{ts}.md")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# 实验报告：{self.func_name}\n\n")
            f.write(f"> 记录时间：{datetime.now().strftime('%Y-%m-%d %H:%m:%S')}\n")
            f.write(f"> 重复次数：{n_repeats}\n\n")

            # 1. 统计结果
            f.write("## 1. 统计结果（多次重复均值）\n\n")
            f.write("| 指标 | 基线 BO | MN-BO（本方法） |\n")
            f.write("|------|---------|----------------|\n")
            f.write(f"| 理论最大值 | {self.global_max:.6f} | {self.global_max:.6f} |\n")
            f.write(f"| Gap（均值） | {baseline_gap:.6f} ± {baseline_std:.6f} | {mnbo_gap:.6f} ± {mnbo_std:.6f} |\n")
            f.write(f"| **Gap 缩减差值** | — | **{gap_diff_avg:.6f} ± {gap_diff_std:.6f}** |\n")
            f.write(f"| **Gap 缩减比** | — | **{reduction_avg:.2f}% ± {reduction_std:.2f}%** |\n")
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
        """向全局汇总表追加一行。"""
        write_header = not os.path.exists(summary_path)
        with open(summary_path, "a", encoding="utf-8") as f:
            if write_header:
                f.write("# 实验汇总报告\n\n")
                f.write("| 函数 | 理论最大值 | 基线 Gap | MN-BO Gap"
                        " | Gap 缩减差值 | Gap 缩减比 | 最佳配置"
                        " | 重复次数 | 耗时(s) |\n")
                f.write("|------|-----------|---------|----------|"
                        "-------------|-----------|---------|"
                        "---------|--------|\n")

            f.write(
                f"| {self.func_name} "
                f"| {self.global_max} "
                f"| {baseline_gap:.4f}±{baseline_std:.4f} "
                f"| {mnbo_gap:.4f}±{mnbo_std:.4f} "
                f"| {gap_diff:.4f}±{gap_diff_std:.4f} "
                f"| {reduction:.2f}%±{reduction_std:.2f}% "
                f"| {best_config} "
                f"| {n_repeats} "
                f"| {total_time:.1f} |\n"
            )
