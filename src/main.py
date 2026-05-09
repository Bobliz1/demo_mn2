"""main.py
MN-BO 实验入口（滚雪球多视角搜索版本 v3.2）。

【核心架构】外层元GP在 8 维连续空间 [0,1]^8 智能选取变换配置，
每轮内层 BO 继承上一轮的完整数据池（滚雪球），而非从固定初始点重启。
  p[0]  → LogWarper 强度 g ∈ [0,1]
  p[1]  → LogWarper alpha ∈ [0.1, 10.0]
  p[2]  → PowerWarper 强度 g ∈ [0,1]
  p[3]  → PowerWarper index ∈ [0.1, 5.0]
  p[4]  → StandardScaler 强度 g ∈ [0,1]
  p[5]  → StandardScaler shift ∈ [-1σ, 1σ]
  p[6]  → StandardScaler scale ∈ [0.2, 5.0]
  p[7]  → MinMaxScaler 强度 g ∈ [0,1]

运行方式
--------
# 交互式菜单
python src/main.py

# 运行全部函数
python src/main.py --all

# 指定函数
python src/main.py cliff_func deceptive_trap_func

# 自定义参数
python src/main.py --all -M 10 -N 10 -R 3

# 快速验证
python src/main.py cliff_func -R 1 -M 5 -N 8 -I 8

参数说明
--------
  -M, --outer-iters  外层 GP 迭代次数（默认 8）
  -N, --inner-iters  内层 BO 步数（默认 12）
  -R, --repeats      每函数重复次数（默认 8）
  -I, --init-meta    外层初始拉丁超方点数（默认 2）
"""

import sys
import os
import time
import warnings
import argparse
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

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
#   - N_REPEATS=8：每次函数重复 8 次（并行）
#   - N_INIT_META：外层拉丁超方初始点数，8D 空间建议 ≥ 2
#   - M_OUTER：外层 GP 迭代次数
#   - N_INNER：内层 BO 步数
# ---------------------------------------------------------------------------
N_REPEATS    = 8
M_OUTER      = 8    # 外层迭代次数 (从 4 改为 8，增强视角搜索能力)
N_INNER      = 12   # 内层 BO 步数 (从 20 改为 12，平衡总预算 120 步)
XI           = 0.05
N_INIT_META  = 2    # 外层初始拉丁超方采样点


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

def _single_run(func_obj, m_outer, n_inner, n_init_meta, xi, seed):
    """执行一次完整的基线 BO + MN-BO（滚雪球多视角搜索）。

    新架构：每轮内层 BO 从当前累积池出发，元GP智能选取下一个变换参数。
    数据在各轮之间完全流转，不再有阶段二冲刺。
    """

    bounds = func_obj.np_bounds()
    gmax   = func_obj.global_max

    np.random.seed(seed)
    n_init = 5
    X_init = np.random.uniform(bounds[:, 0], bounds[:, 1], size=(n_init, 1))
    Y_init = func_obj(X_init.flatten()).reshape(-1, 1)

    outer_bounds = get_outer_bounds()

    # ---- 采样预算对齐 ----
    # MN-BO 总采样数 = (初始外层点数 + 外层迭代次数) × 内层步数
    total_budget = (n_init_meta + m_outer) * n_inner

    # ---- 基线 BO ----
    print(f"      [基线 BO] 分配公平采样预算: {total_budget} 步")
    base_max, x_base, y_base, gpr_base = run_inner_bo(
        TransformerPipeline([IdentityOperator()]),
        func_obj, total_budget, X_init, Y_init, bounds, gmax=gmax,
    )

    # ---- MN-BO（滚雪球多视角搜索）----
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

    # 初始化全局经验池（原始空间 y 值）
    global_X_pool = X_init.copy()
    global_Y_pool = Y_init.copy()   # shape (n, 1)

    X_meta, Y_meta = [], []
    max_found = -np.inf
    best_xs, best_ys, best_gpr = None, None, None

    # 外层初始点：拉丁超方采样
    X_meta_init = _latin_hypercube_init(n_init_meta, N_CONTINUOUS, seed=seed)

    print(f"      [MN-BO] 滚雪球搜索开始，初始池 {len(global_X_pool)} 点，"
          f"预填充 {n_init_meta} 个外层初始变换...")

    # ---- 外层初始点：每轮从当前累积池出发 ----
    for i, init_pt in enumerate(X_meta_init):
        pipe, ps = params_to_pipeline(init_pt, Y_init)
        pool_size_before = len(global_X_pool)

        found, xs, ys_raw, lgpr = run_inner_bo(
            pipe, func_obj, n_inner,
            global_X_pool, global_Y_pool, bounds, gmax=gmax)

        # 只追加本轮新采样的点
        new_X = xs[pool_size_before:]
        new_Y = ys_raw[pool_size_before:].reshape(-1, 1)
        global_X_pool = np.vstack((global_X_pool, new_X))
        global_Y_pool = np.vstack((global_Y_pool, new_Y))

        X_meta.append(init_pt)
        Y_meta.append(-found)

        if found > max_found:
            max_found = found
            best_xs, best_ys, best_gpr = xs, ys_raw, lgpr

        if (i + 1) % 4 == 0 or (i + 1) == n_init_meta:
            print(f"      初始点 {i+1}/{n_init_meta} 完成  "
                  f"最佳={max_found:.6f}  池子={len(global_X_pool)}点")

    # ---- 外层 GP 迭代：每轮继续从累积池出发 ----
    for m in range(m_outer):
        Xm = np.array(X_meta)
        Ym = np.array(Y_meta).reshape(-1, 1)
        meta_gpr.fit(Xm, Ym)
        params = propose_next_sample(meta_ei, Xm, Ym, meta_gpr, outer_bounds)

        pipe, ps = params_to_pipeline(params, Y_init)
        pool_size_before = len(global_X_pool)
        print(f"      外层GP {m+1}/{m_outer}  池子:{pool_size_before}点  "
              f"变换: {ps}")

        found, xs, ys_raw, lgpr = run_inner_bo(
            pipe, func_obj, n_inner,
            global_X_pool, global_Y_pool, bounds, gmax=gmax)

        new_X = xs[pool_size_before:]
        new_Y = ys_raw[pool_size_before:].reshape(-1, 1)
        global_X_pool = np.vstack((global_X_pool, new_X))
        global_Y_pool = np.vstack((global_Y_pool, new_Y))

        X_meta.append(params)
        Y_meta.append(-found)

        if found > max_found:
            max_found = found
            best_xs, best_ys, best_gpr = xs, ys_raw, lgpr

    # 最终结果：取全局池中的最大原始 y 值
    mnbo_max = float(np.max(global_Y_pool))

    return {
        "base_max":    base_max,
        "mnbo_max":    mnbo_max,
        "best_config": f"snowball_pool(size={len(global_X_pool)})",
        "x_base":      x_base,
        "y_base":      y_base,
        "gpr_base":    gpr_base,
        "final_data":  (best_xs, best_ys, best_gpr),
        "best_pipe":   TransformerPipeline([IdentityOperator()]),
    }


# ======================================================================
# 多次重复实验（取均值）
# ======================================================================

def run_experiment(func_name: str,
                   m_outer: int = M_OUTER,
                   n_inner: int = N_INNER,
                   n_init_meta: int = N_INIT_META, xi: float = XI,
                   n_repeats: int = N_REPEATS,
                   summary_path: str = SUMMARY_PATH,
                   seed_base: int = 42):
    """对单个函数运行 n_repeats 次独立实验，取均值输出报告。"""

    func_obj = get_func(func_name)
    gmax     = func_obj.global_max
    seeds    = list(range(seed_base, seed_base + n_repeats))

    # 并行执行多个重复
    print(f"\n    [并行执行] 启动 {n_repeats} 个进程处理 {n_repeats} 次重复...")
    run_results = []
    
    # 限制最大进程数为 CPU 核心数
    max_workers = min(n_repeats, multiprocessing.cpu_count())
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 将参数打包提交给并行池
        futures = [
            executor.submit(_single_run, func_obj, m_outer, n_inner, n_init_meta, xi, s)
            for s in seeds
        ]
        for f in futures:
            run_results.append(f.result())

    # 打印外层参数维度说明
    param_names = list(OPERATOR_INFO.keys())
    print(f"\n{'='*60}")
    print(f"  函数: {func_name}  |  理论最大值: {gmax}")
    total_budget = (N_INIT_META + m_outer) * n_inner
    print(f"  外层维度: {N_CONTINUOUS}D  |  外层初始={N_INIT_META}  外层迭代M={m_outer}  内层N={n_inner}  |  总预算: {total_budget}")
    print(f"  外层参数:")
    for k, (op, rng, desc) in OPERATOR_INFO.items():
        print(f"    [{k}] {op}  {rng}  — {desc}")
    print(f"  重复次数: {n_repeats}")
    print(f"{'='*60}")

    # ---- 统计汇总 ----
    # ---- 统计汇总 ----
    base_maxes = np.array([r["base_max"]  for r in run_results])
    mnbo_maxes = np.array([r["mnbo_max"]  for r in run_results])
    max_diffs  = mnbo_maxes - base_maxes

    # 成功率统计：y > 90% * gmax
    threshold = 0.9 * gmax
    base_success_count = np.sum(base_maxes > threshold)
    mnbo_success_count = np.sum(mnbo_maxes > threshold)
    base_success_rate  = base_success_count / n_repeats
    mnbo_success_rate  = mnbo_success_count / n_repeats

    avg_base, std_base = base_maxes.mean(), base_maxes.std()
    avg_mnbo, std_mnbo = mnbo_maxes.mean(), mnbo_maxes.std()
    avg_diff, std_diff = max_diffs.mean(), max_diffs.std()

    print(f"\n{'─'*60}")
    print(f"  原始数据 (Raw Data):")
    print(f"    基线  : {[round(float(x), 4) for x in base_maxes]}")
    print(f"    MN-BO : {[round(float(x), 4) for x in mnbo_maxes]}")
    print(f"  汇总（{n_repeats} 次统计）")
    print(f"  基线成功率 : {base_success_rate*100:.1f}% ({base_success_count}/{n_repeats})")
    print(f"  MN-BO成功率 : {mnbo_success_rate*100:.1f}% ({mnbo_success_count}/{n_repeats})")
    print(f"  基线 Max    : {avg_base:.6f} ± {std_base:.6f}")
    print(f"  MN-BO Max   : {avg_mnbo:.6f} ± {std_mnbo:.6f}")
    print(f"  Max 差值    : {avg_diff:.6f} ± {std_diff:.6f}")
    print(f"{'─'*60}")

    # ---- 选出中位次绘图 ----
    median_idx = np.argmin(np.abs(mnbo_maxes - mnbo_maxes.mean()))
    best_run   = run_results[median_idx]
    
    x_base, y_base     = best_run["x_base"], best_run["y_base"]
    gpr_base           = best_run["gpr_base"]
    xs_best, ys_best   = best_run["final_data"][0], best_run["final_data"][1]
    gpr_best           = best_run["final_data"][2]
    med_base_max       = best_run["base_max"]
    med_mnbo_max       = best_run["mnbo_max"]
    best_pipe          = best_run["best_pipe"]
    best_pipe_str      = best_run["best_config"]
    bounds             = func_obj.np_bounds()

    x_plot = np.linspace(bounds[0, 0], bounds[0, 1], 1000).reshape(-1, 1)
    y_gt   = func_obj(x_plot.flatten())

    mu_base, _  = gpr_base.predict(x_plot, return_std=True)
    mu_trans, _ = gpr_best.predict(x_plot, return_std=True)
    mu_raw      = np.array(
        [best_pipe.backward(np.array([[v]])) for v in mu_trans.flatten()]
    ).flatten()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    for ax, mu, xs, ys, title, max_val in [
        (ax1, mu_base, x_base, y_base, 
         f"Baseline BO\n(Max={med_base_max:.4f})", med_base_max),
        (ax2, mu_raw, xs_best, ys_best, 
         f"MN-BO  \n(Max={med_mnbo_max:.4f})", med_mnbo_max),
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

    plt.tight_layout()

    # ---- 写日志 ----
    logger  = ExperimentLogger(func_obj)
    md_path = logger.log_experiment(
        m_iter=m_outer, n_iter=n_inner, xi=xi,
        baseline_max=avg_base, mnbo_max=avg_mnbo,
        baseline_std=std_base, mnbo_std=std_mnbo,
        max_diff_avg=avg_diff, max_diff_std=std_diff,
        baseline_success=base_success_rate,
        mnbo_success=mnbo_success_rate,
        n_repeats=n_repeats,
        best_config=best_pipe_str,
        samples_x=xs_best, samples_y=ys_best,
        best_x=float(xs_best[np.argmax(ys_best)][0]),
        best_y=float(ys_best.max()),
        fig=fig,
    )
    logger.append_summary_row(
        summary_path,
        baseline_max=avg_base, baseline_std=std_base,
        mnbo_max=avg_mnbo, mnbo_std=std_mnbo,
        max_diff=avg_diff, max_diff_std=std_diff,
        baseline_success=base_success_rate,
        mnbo_success=mnbo_success_rate,
        best_config=best_pipe_str,
        n_repeats=n_repeats,
        total_time=0,
    )
    # 额外在 md 中记录原始数据供查看（保留4位小数）
    raw_base_str = ", ".join([f"{x:.4f}" for x in base_maxes])
    raw_mnbo_str = ", ".join([f"{x:.4f}" for x in mnbo_maxes])
    with open(md_path, "a", encoding="utf-8") as f:
        f.write("\n## 4. 原始数据 (Raw Data)\n\n")
        f.write(f"- 基线 Max 序列: `[{raw_base_str}]`\n")
        f.write(f"- MN-BO Max 序列: `[{raw_mnbo_str}]`\n")

    # 将结果返回，用于最后大汇总（保留原始精度，仅展示层控制）
    return {
        "avg_base_max": avg_base, "std_base_max": std_base,
        "avg_mnbo_max": avg_mnbo, "std_mnbo_max": std_mnbo,
        "avg_max_diff": avg_diff, "std_max_diff": std_diff,
        "base_success": base_success_rate,
        "mnbo_success": mnbo_success_rate,
        "raw_mnbo_str": f"[{raw_mnbo_str}]",
        "total_time":   0
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
        description="MN-BO 实验入口（v3.2 滚雪球多视角搜索）",
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

    parser.add_argument(
        "--seed", type=int, default=2024,
        help="随机种子基值（默认：2024）"
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
    print(f"\n生效参数：初始点={_IM} × 外层迭代M={_M} × 内层步数N={_N} × 重复={_R}次"
          f"  |  总预算/函数={(_IM + _M) * _N}步")

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
    print(f"架构：滚雪球多视角搜索  |  外层{N_CONTINUOUS}D  |  初始{_IM}点  |  "
          f"M={_M}×N={_N}  |  总预算={(_IM + _M) * _N}步")

    # 路径准备
    summary_dir = "results/summary"
    log_dir = "results/logs"
    os.makedirs(summary_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = os.path.join(summary_dir, f"summary_report_{ts}.md")
    execution_log_path = os.path.join(log_dir, f"run_{ts}.log")

    # 简单的日志重定向：同时输出到终端和文件
    class Logger:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "w", encoding="utf-8")
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
        def flush(self):
            self.terminal.flush()
            self.log.flush()

    sys.stdout = Logger(execution_log_path)
    print(f"日志将实时保存至: {execution_log_path}")

    _SEED = args.seed
    t_total = time.time()
    results = {}
    for name in chosen:
        r = run_experiment(name, m_outer=_M, n_inner=_N, n_repeats=_R,
                           summary_path=summary_path, seed_base=_SEED)
        results[name] = r

    print(f"\n\n{'#'*60}")
    print(f"  批量实验完成 — 汇总（{_R} 次均值）")
    print(f"{'#'*60}")
    print(f"  {'函数':<28}  {'基线Max':>14}  {'MN-BO Max':>14}  "
          f"{'Max差值(正优)':>14}")
    print(f"  {'─'*72}")
    
    # 终端打印
    for name, r in results.items():
        print(f"  {name:<28}  "
              f"{r['avg_base_max']:.4f}±{r['std_base_max']:.4f}  "
              f"{r['avg_mnbo_max']:.4f}±{r['std_mnbo_max']:.4f}  "
              f"{r['avg_max_diff']:.4f}±{r['std_max_diff']:.4f}")
              
    total_time = time.time() - t_total
    print(f"\n  总耗时: {total_time:.1f}s")
    print(f"  累计汇总报告：{summary_path}")

    # 生成带时间戳的批次汇总文件
    batch_summary_path = os.path.join(summary_dir, f"batch_summary_{ts}.md")
    with open(batch_summary_path, "w", encoding="utf-8") as f:
        f.write(f"# 批量实验汇总报告（滚雪球多视角搜索）\n\n")
        f.write(f"- **生成时间**: {ts}\n")
        f.write(f"- **参数配置**: 外层初始点={_IM}, 外层迭代M={_M}, 内层N={_N}, 重复={_R}次\n")
        f.write(f"- **基线/MN-BO总预算**: {(_IM + _M) * _N} 步\n")
        sys.stdout.flush()
        f.write("| 函数 | 基线 Max | MN-BO Max | 基线成功率 | MN-BO 成功率 | 原始数据 (MN-BO) |\n")
        f.write("|------|-----------|-----------|------------|--------------|-------------------|\n")
        for name, r in results.items():
            f.write(f"| {name} | {r['avg_base_max']:.4f}±{r['std_base_max']:.4f} | "
                    f"{r['avg_mnbo_max']:.4f}±{r['std_mnbo_max']:.4f} | "
                    f"{r['base_success']*100:.1f}% | "
                    f"{r['mnbo_success']*100:.1f}% | "
                    f"`{r['raw_mnbo_str']}` |\n")
    print(f"  单次批次汇总：{batch_summary_path}")
