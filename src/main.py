"""main.py
MN-BO 实验入口（连续参数化版本 v2，带 gate）。

【稳定算子模式】外层在 4 维连续空间 [0,1]^4 搜索最优变换配置：
  p[0]  → StandardScaler 强度 g ∈ [0,1]
  p[1]  → StandardScaler shift ∈ [-1σ, 1σ]
  p[2]  → StandardScaler scale ∈ [0.2, 5.0]
  p[3]  → MinMaxScaler 强度 g ∈ [0,1]

【待处理算子】以下算子因数值稳定性问题已禁用，待架构重构后恢复：
  LogWarper / PowerTransform / SigmoidWarper / RankTransform

运行方式
--------
# 交互式菜单
python src/main.py

# 运行全部函数（默认 M=20, N=12, R=5）
python src/main.py --all

# 指定函数
python src/main.py cliff_func deceptive_trap_func

# 自定义 M/N/R 参数
python src/main.py --all -M 30 -N 15 -R 3
python src/main.py multipeak_func -M 10 -N 20 -R 1

# 快速验证（稳定算子，4D 空间）
python src/main.py --all -R 1 -M 5 -N 8 -I 8

参数说明
--------
  -M, --outer-iters  外层 GP 迭代次数（默认 20，4D 空间建议 5~10）
  -N, --inner-iters  内层 BO 步数（默认 12）
  -R, --repeats      每函数重复次数（默认 5）
  -I, --init-meta    外层初始拉丁超方点数（默认 36，4D 空间建议 8~12）
"""

import sys
import os
import time
import warnings
import argparse

# 确保 src/ 目录在 Python 路径中，使 benchmark / bo_transform 可被导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, Matern
from scipy.stats import norm, qmc

warnings.filterwarnings("ignore", category=UserWarning)

from benchmark import (
    expected_improvement,
    propose_next_sample,
    ExperimentLogger,
    list_functions,
    get_func,
)
from bo_transform import (
    TransformerPipeline, WrappedTarget,
    params_to_pipeline, get_outer_bounds,
    N_CONTINUOUS, OPERATOR_INFO,
    IdentityOperator,
)

SUMMARY_PATH = "results/summary_report.md"

# ---------------------------------------------------------------------------
# 实验参数（可被命令行覆盖）
# ---------------------------------------------------------------------------
# 默认值说明：
#   - N_REPEATS=5：每次函数重复5次（seed 42-46）
#   - N_INIT_META：外层拉丁超方初始点数，建议 ≥ 3 × 维度数（12D → ≥36）
#   - M_OUTER：外层 GP 迭代次数，12D 建议 20~30
#   - N_INNER：内层 BO 步数
# ---------------------------------------------------------------------------
N_REPEATS    = 5
M_OUTER      = 5    # 外层迭代（12D 空间需要足够探索）
N_INNER      = 8    # 内层迭代（略微降低，省时间给外层）
XI           = 0.05
N_INIT_META  = 8    # 外层初始拉丁超方采样点  现在是4D；


# ======================================================================
# 外层初始点生成（拉丁超方采样）
# ======================================================================

def _latin_hypercube_init(n_points: int, n_dims: int, seed: int = 42) -> np.ndarray:
    """生成 n_points 个 n_dims 维拉丁超方样本，值域 [0,1]。"""
    sampler = qmc.LatinHypercube(d=n_dims, seed=seed)
    return sampler.random(n=n_points)


# ======================================================================
# 内层 BO
# ======================================================================

def run_inner_bo(pipeline, target_func, n_iter, x_init, y_init, bounds, gmax=None):
    wrapped = WrappedTarget(target_func, pipeline)
    X   = x_init.copy()
    Y_t = pipeline.forward(y_init)

    gpr = GaussianProcessRegressor(
        kernel=C(1.0) * RBF(1.0),
        n_restarts_optimizer=3,   # 从 10 降到 3，精度几乎不变，速度快 3×
        alpha=1e-5,
    )
    for _ in range(n_iter):
        gpr.fit(X, Y_t)
        nx  = propose_next_sample(expected_improvement, X, Y_t, gpr, bounds)
        ny  = wrapped(nx)
        X   = np.vstack((X, nx))
        Y_t = np.vstack((Y_t, ny))

    # 全局安全 clamp：防止 backward 变换数值溢出。
    # 宽松 clamp 避免裁剪正常值，_fmt 会把负 Gap（溢出）显示为 "N/A"。
    # 仅在发现绝对数值异常（>1e6）时才 clip。
    y_min = float(np.min(y_init))
    y_max = float(np.max(y_init))
    Y_raw = np.array([pipeline.backward(y) for y in Y_t])
    # 宽松上界：允许 backward 适度超出初始范围（最多到 max(100×y_max, 1e6)）
    y_max_safe = max(y_max * 100.0, 1e6)
    Y_raw = np.clip(Y_raw, y_min, y_max_safe)
    return np.max(Y_raw), X, Y_raw, gpr


# ======================================================================
# 单次实验（一次 seed）
# ======================================================================

def _single_run(func_obj, m_outer, n_inner, xi, seed):
    """执行一次完整的基线 BO + MN-BO（连续参数），返回详细结果。"""

    bounds = func_obj.np_bounds()
    gmax   = func_obj.global_max

    np.random.seed(seed)
    n_init = 5
    X_init = np.random.uniform(bounds[:, 0], bounds[:, 1], size=(n_init, 1))
    Y_init = func_obj(X_init.flatten()).reshape(-1, 1)

    outer_bounds = get_outer_bounds()

    # ---- 基线 BO ----
    base_max, x_base, y_base, gpr_base = run_inner_bo(
        TransformerPipeline([IdentityOperator()]),
        func_obj, n_inner, X_init, Y_init, bounds, gmax=gmax,
    )
    base_gap = gmax - base_max

    # ---- MN-BO（连续参数空间）----
    # 外层 GP：4D 空间，适当增大 length_scale
    meta_gpr = GaussianProcessRegressor(
        kernel=C(1.0) * RBF(np.ones(N_CONTINUOUS) * 0.5, length_scale_bounds=(0.1, 2.0)),
        n_restarts_optimizer=5,
    )

    def meta_ei(X_test, X_s, Y_s, g, xi=0.01):
        mu, sigma = g.predict(X_test, return_std=True)
        cur_min   = np.min(Y_s)
        sigma     = sigma.reshape(-1, 1)
        with np.errstate(divide="ignore", invalid="ignore"):
            imp = cur_min - mu - xi
            Z   = imp / sigma
            ei  = imp * norm.cdf(Z) + sigma * norm.pdf(Z)
            ei[sigma <= 0.0] = 0.0
        return ei

    # 外层初始点：拉丁超方采样
    X_meta_init = _latin_hypercube_init(N_INIT_META, N_CONTINUOUS, seed=seed)
    X_meta, Y_meta = [], []
    best_pipe, best_pipe_str, min_gap = None, "", np.inf
    final_data = None

    print(f"      [外层预填充 {N_INIT_META} 个初始点...]")

    for i, init_pt in enumerate(X_meta_init):
        pipe, ps = params_to_pipeline(init_pt, Y_init)
        found, xs, ys, lgpr = run_inner_bo(
            pipe, func_obj, n_inner, X_init, Y_init, bounds, gmax=gmax)
        gap = gmax - found
        X_meta.append(init_pt)
        Y_meta.append(gap)
        if gap < min_gap:
            min_gap, best_pipe, best_pipe_str = gap, pipe, ps
            final_data = (xs, ys, lgpr)
        if (i + 1) % 4 == 0:
            print(f"      初始点 {i+1}/{N_INIT_META} 完成  当前最佳 Gap={min_gap:.6f}")

    # 外层 GP 搜索（连续优化）
    for m in range(m_outer):
        Xm = np.array(X_meta)
        Ym = np.array(Y_meta).reshape(-1, 1)
        meta_gpr.fit(Xm, Ym)
        params = propose_next_sample(meta_ei, Xm, Ym, meta_gpr, outer_bounds)

        pipe, ps = params_to_pipeline(params, Y_init)
        print(f"      外层 GP {m+1}/{m_outer}  最佳配置: {ps[:60]}...")
        found, xs, ys, lgpr = run_inner_bo(
            pipe, func_obj, n_inner, X_init, Y_init, bounds, gmax=gmax)
        gap = gmax - found
        X_meta.append(params)
        Y_meta.append(gap)
        if gap < min_gap:
            min_gap, best_pipe, best_pipe_str = gap, pipe, ps
            final_data = (xs, ys, lgpr)

    return {
        "base_gap":    base_gap,
        "mnbo_gap":    min_gap,
        "best_config": best_pipe_str,
        "x_base":      x_base,
        "y_base":      y_base,
        "gpr_base":    gpr_base,
        "final_data":  final_data,
        "best_pipe":   best_pipe,
    }


# ======================================================================
# 多次重复实验（取均值）
# ======================================================================

def run_experiment(func_name: str,
                   m_outer: int = M_OUTER,
                   n_inner: int = N_INNER,
                   xi: float    = XI,
                   n_repeats: int = N_REPEATS):
    """对单个函数运行 n_repeats 次独立实验，取均值输出报告。"""

    func_obj = get_func(func_name)
    gmax     = func_obj.global_max
    seeds    = list(range(42, 42 + n_repeats))

    # 打印外层参数维度说明
    param_names = list(OPERATOR_INFO.keys())
    print(f"\n{'='*60}")
    print(f"  函数: {func_name}  |  理论最大值: {gmax}")
    print(f"  外层维度: {N_CONTINUOUS}D  |  外层 M={m_outer}  内层 N={n_inner}")
    print(f"  外层参数:")
    for k, (op, rng, desc) in OPERATOR_INFO.items():
        print(f"    [{k}] {op}  {rng}  — {desc}")
    print(f"  重复次数: {n_repeats}")
    print(f"{'='*60}")

    # ---- 逐次运行 ----
    run_results = []
    for i, seed in enumerate(seeds):
        print(f"\n  ── 第 {i+1}/{n_repeats} 次（seed={seed}）──")
        r = _single_run(func_obj, m_outer, n_inner, xi, seed)
        run_results.append(r)
        red = ((r["base_gap"] - r["mnbo_gap"]) / r["base_gap"] * 100
               if r["base_gap"] > 0 else float("nan"))
        print(f"     基线 Gap={r['base_gap']:.6f}  "
              f"MN-BO Gap={r['mnbo_gap']:.6f}  "
              f"缩减比: {red:.1f}%")

    # ---- 统计汇总 ----
    base_gaps  = np.array([r["base_gap"]  for r in run_results])
    mnbo_gaps  = np.array([r["mnbo_gap"]  for r in run_results])
    reductions = (base_gaps - mnbo_gaps) / base_gaps * 100
    gap_diffs  = base_gaps - mnbo_gaps

    avg_base, std_base = base_gaps.mean(), base_gaps.std()
    avg_mnbo, std_mnbo = mnbo_gaps.mean(), mnbo_gaps.std()
    avg_red,  std_red  = reductions.mean(), reductions.std()
    avg_diff, std_diff = gap_diffs.mean(), gap_diffs.std()

    print(f"\n{'─'*60}")
    print(f"  汇总（{n_repeats} 次均值）")
    print(f"  基线 Gap    : {avg_base:.6f} ± {std_base:.6f}")
    print(f"  MN-BO Gap   : {avg_mnbo:.6f} ± {std_mnbo:.6f}")
    print(f"  Gap 缩减差值: {avg_diff:.6f} ± {std_diff:.6f}")
    print(f"  Gap 缩减比  : {avg_red:.2f}% ± {std_red:.2f}%")
    print(f"{'─'*60}")

    # ---- 选取表现最接近均值的一次，绘制可视化 ----
    median_idx = np.argmin(np.abs(mnbo_gaps - mnbo_gaps.mean()))
    best_run   = run_results[median_idx]

    xs_f, ys_f, gpr_f = best_run["final_data"]
    gpr_base           = best_run["gpr_base"]
    x_base             = best_run["x_base"]
    y_base             = best_run["y_base"]
    best_pipe          = best_run["best_pipe"]
    best_pipe_str      = best_run["best_config"]
    med_base_gap       = best_run["base_gap"]
    med_mnbo_gap       = best_run["mnbo_gap"]
    bounds             = func_obj.np_bounds()

    x_plot = np.linspace(bounds[0, 0], bounds[0, 1], 1000).reshape(-1, 1)
    y_gt   = func_obj(x_plot.flatten())

    mu_base, _  = gpr_base.predict(x_plot, return_std=True)
    mu_trans, _ = gpr_f.predict(x_plot, return_std=True)
    mu_raw      = np.array(
        [best_pipe.backward(np.array([[v]])) for v in mu_trans.flatten()]
    ).flatten()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    for ax, mu, xs, ys, title, gap_val in [
        (ax1, mu_base, x_base, y_base.flatten(),
         f"Baseline BO\n(Gap={med_base_gap:.4f})", med_base_gap),
        (ax2, mu_raw,  xs_f,   ys_f.flatten(),
         f"MN-BO  \n(Gap={med_mnbo_gap:.4f})", med_mnbo_gap),
    ]:
        ax.plot(x_plot, y_gt,   "r:", lw=1.5, label="Ground Truth", alpha=0.85)
        ax.plot(x_plot, mu,     "b-", lw=1.5, label="GP Mean",      alpha=0.85)
        ax.scatter(xs.flatten(), ys, c="black", marker="x", s=40, label="Samples")
        ax.axhline(gmax, color="gray", ls="--", alpha=0.5,
                   label=f"Theoretical Max ({gmax})")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("x")
        ax.set_ylabel("f(x)")
        ax.legend(fontsize=8)

    # 截断 best_pipe_str 避免标题过长
    pipe_short = best_pipe_str[:80] + ("..." if len(best_pipe_str) > 80 else "")
    plt.suptitle(
        f"{func_name}  |  {n_repeats} runs avg  "
        f"Baseline Gap={avg_base:.4f}±{std_base:.4f}  "
        f"MN-BO Gap={avg_mnbo:.4f}±{std_mnbo:.4f}  "
        f"(↓{avg_red:.1f}%)",
        fontsize=10, fontweight="bold",
    )
    plt.tight_layout()

    # ---- 写日志 ----
    logger  = ExperimentLogger(func_obj)
    md_path = logger.log_experiment(
        m_iter=m_outer, n_iter=n_inner, xi=xi,
        baseline_gap=avg_base, mnbo_gap=avg_mnbo,
        baseline_std=std_base, mnbo_std=std_mnbo,
        gap_diff_avg=avg_diff, gap_diff_std=std_diff,
        reduction_avg=avg_red, reduction_std=std_red,
        n_repeats=n_repeats,
        best_config=best_pipe_str,
        samples_x=xs_f, samples_y=ys_f,
        best_x=float(xs_f[np.argmax(ys_f)][0]),
        best_y=float(ys_f.max()),
        fig=fig,
    )
    logger.append_summary_row(
        SUMMARY_PATH,
        baseline_gap=avg_base, baseline_std=std_base,
        mnbo_gap=avg_mnbo, mnbo_std=std_mnbo,
        gap_diff=avg_diff, gap_diff_std=std_diff,
        reduction=avg_red, reduction_std=std_red,
        best_config=best_pipe_str,
        n_repeats=n_repeats,
        total_time=0,
    )
    print(f"  报告已写入: {md_path}")

    return {
        "avg_base_gap": avg_base, "std_base_gap": std_base,
        "avg_mnbo_gap": avg_mnbo, "std_mnbo_gap": std_mnbo,
        "avg_reduction": avg_red, "std_reduction": std_red,
        "avg_gap_diff": avg_diff, "std_gap_diff": std_diff,
        "best_config": best_pipe_str,
    }


# ======================================================================
# 交互式菜单
# ======================================================================

def interactive_menu() -> list[str]:
    """展示函数列表，让用户选择要跑的函数，返回函数名列表。"""
    funcs = list_functions()

    print("\n" + "═" * 60)
    print("  MN-BO 实验 — 请选择要测试的基准函数（连续参数版）")
    print("═" * 60)
    for i, name in enumerate(funcs, 1):
        obj = get_func(name)
        print(f"  {i:>2}. {name:<28}  max={obj.global_max}")
    print(f"  {'0':>2}. 全部运行")
    print("═" * 60)

    raw = input("请输入编号（多个用空格分隔，0=全部）：").strip()
    if not raw or raw == "0":
        return funcs

    selected = []
    for token in raw.split():
        try:
            idx = int(token) - 1
            if 0 <= idx < len(funcs):
                selected.append(funcs[idx])
            else:
                print(f"  忽略无效编号: {token}")
        except ValueError:
            if token in funcs:
                selected.append(token)
            else:
                print(f"  忽略未知函数名: {token}")
    return selected or funcs


# ======================================================================
# 入口
# ======================================================================

if __name__ == "__main__":
    # ---- 命令行参数解析 ----
    parser = argparse.ArgumentParser(
        description="MN-BO 实验入口（v2 连续参数化）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python src/main.py                                    # 交互式菜单
  python src/main.py --all                              # 全部函数（默认参数）
  python src/main.py cliff_func deceptive_trap_func     # 指定函数
  python src/main.py --all -M 30 -N 15 -R 3            # 自定义 M/N/R
  python src/main.py multipeak_func -M 10 -N 20         # 快速测试
        """
    )
    parser.add_argument(
        "functions", nargs="*", default=[],
        help="要运行的函数名（如 cliff_func），留空则进入交互菜单"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="运行全部函数"
    )
    parser.add_argument(
        "-M", "--outer-iters", type=int, default=None,
        help=f"外层 GP 迭代次数（默认：{M_OUTER}）"
    )
    parser.add_argument(
        "-N", "--inner-iters", type=int, default=None,
        help=f"内层 BO 步数（默认：{N_INNER}）"
    )
    parser.add_argument(
        "-R", "--repeats", type=int, default=None,
        help=f"每个函数重复次数（默认：{N_REPEATS}）"
    )
    parser.add_argument(
        "-I", "--init-meta", type=int, default=None,
        help=f"外层初始拉丁超方点数（默认：{N_INIT_META}）"
    )
    args = parser.parse_args()

    # ---- 覆盖全局参数 ----
    if args.outer_iters is not None:
        globals()["M_OUTER"] = args.outer_iters
    if args.inner_iters is not None:
        globals()["N_INNER"] = args.inner_iters
    if args.repeats is not None:
        globals()["N_REPEATS"] = args.repeats
    if args.init_meta is not None:
        globals()["N_INIT_META"] = args.init_meta

    # 打印当前生效的参数（从 globals 读取，确保一致）
    _M  = globals()["M_OUTER"]
    _N  = globals()["N_INNER"]
    _R  = globals()["N_REPEATS"]
    _IM = globals()["N_INIT_META"]
    print(f"\n生效参数：M={_M}（外层迭代） × N={_N}（内层步数） × "
          f"初始点={_IM} × 重复={_R}次")

    # ---- 确定要运行的函数 ----
    all_funcs = list_functions()
    if args.all:
        chosen = all_funcs
    elif args.functions:
        chosen = [f for f in args.functions if f in all_funcs]
        missed = [f for f in args.functions if f not in all_funcs]
        if missed:
            print(f"⚠ 未知函数：{missed}，可用：{all_funcs}")
        if not chosen:
            sys.exit(1)
    else:
        chosen = interactive_menu()

    if not chosen:
        sys.exit(1)

    print(f"\n将运行 {len(chosen)} 个函数（每个 {_R} 次取均值）：{chosen}")
    print(f"外层搜索空间：{N_CONTINUOUS}D  |  初始 {_IM} 点  |  "
          f"M={_M}（外层迭代） × N={_N}（内层步数）")

    # 批量实验前清空旧汇总报告，避免追加污染
    if os.path.exists(SUMMARY_PATH):
        os.remove(SUMMARY_PATH)

    t_total = time.time()
    results = {}
    for name in chosen:
        r = run_experiment(name, m_outer=_M, n_inner=_N, n_repeats=_R)
        results[name] = r

    # 最终汇总打印
    print(f"\n\n{'#'*60}")
    print(f"  批量实验完成 — 汇总（{_R} 次均值）")
    print(f"{'#'*60}")
    print(f"  {'函数':<28}  {'基线Gap':>14}  {'MN-BO Gap':>14}  "
          f"{'Gap缩减差值':>14}  {'缩减比':>10}")
    print(f"  {'─'*82}")
    for name, r in results.items():
        print(f"  {name:<28}  "
              f"{r['avg_base_gap']:.4f}±{r['std_base_gap']:.4f}  "
              f"{r['avg_mnbo_gap']:.4f}±{r['std_mnbo_gap']:.4f}  "
              f"{r['avg_gap_diff']:.4f}±{r['std_gap_diff']:.4f}  "
              f"{r['avg_reduction']:.1f}%±{r['std_reduction']:.1f}%")
    print(f"\n  总耗时: {time.time()-t_total:.1f}s")
    print(f"  汇总报告：{SUMMARY_PATH}")
