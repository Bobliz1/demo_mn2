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

SUMMARY_PATH = "results/_summary/summary_report.md"

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
M_OUTER      = 8    # 默认外层迭代轮数
N_INNER      = 12   # 默认内层步数（会被梯度预算覆盖）
XI           = 0.05
N_INIT_META  = 2    # 外层初始点

# 难度阶梯预算分配 (针对各函数难度设计的名义总步数)
TARGET_BUDGETS = {
    "needle_in_haystack_func": 120,
    "flat_region_func": 100,
    "noisy_func": 120,
    "deceptive_trap_func": 75,
    "periodic_trap_func": 60,
    "cliff_func": 50,
    "multipeak_func": 40,
    "valley_ridge_func": 35,
    "asymmetric_func": 25,
    "oscillating_decay_func": 25,
    "double_well_func": 20,
    "step_func": 20,
}


# 针对每个函数优化的 (M, N) 配置
# M: 外层视角数, N: 内层每视角步数
# 规则：对于低预算函数，减少 M 以保证 N 足够深。
FUNCTION_SPECIFIC_MN = {
    "needle_in_haystack_func": (8, 12),   # 120步: 保持视角广度
    "flat_region_func": (6, 15),          # 100步: 增加深度
    "noisy_func": (5, 20),                # 120步: 噪声需要更深挖掘
    "deceptive_trap_func": (5, 12),       # 75步
    "periodic_trap_func": (6, 8),         # 60步
    "cliff_func": (4, 10),                # 50步
    "multipeak_func": (4, 8),             # 40步
    "valley_ridge_func": (3, 8),          # 35步
    "asymmetric_func": (2, 10),           # 25步
    "oscillating_decay_func": (2, 10),    # 25步
    "double_well_func": (2, 8),           # 20步
    "step_func": (2, 8),                  # 20步
}


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

# ======================================================================
# 早停控制器 (Early Stop Controller)
# ======================================================================

class EarlyStopController:
    """
    动态预算控制器：实现三大场景判定。
    - 场景A (止损)：长时间无成果且EI耗尽，切换到下一个视角。
    - 场景B (追加)：正处于爬坡阶段，允许突破 N 限制继续挖掘。
    - 场景C (见好就收)：已有成果但增益趋于零，提前切换视角。

    所有判断均在「原始物理空间」进行，EI 使用归一化值以消除量纲偏差。
    """
    def __init__(self, patience=3, ei_exit_thresh=0.005, convergence_eps=0.001,
                 min_steps=3, borrow_policy='moderate', uncertainty_thresh=0.3):
        self.patience = patience
        self.ei_exit_thresh = ei_exit_thresh
        self.convergence_eps = convergence_eps
        self.min_steps = min_steps
        self.borrow_policy = borrow_policy
        self.uncertainty_thresh = uncertainty_thresh  # v3.4 核心锁：只有看清了（不确定性低）才准走
        self.reset()

    def reset(self):
        """每进入新的视角前调用。"""
        self.y_history = []
        self.stagnant_count = 0
        self.current_max = -np.inf
        self.extra_steps = 0

    def update(self, y_pool_raw: np.ndarray, ei_norm: float, max_std: float) -> str:
        """
        根据物理空间反馈、归一化 EI 和最大不确定性决定决策。
        """
        y_max_now = float(np.max(y_pool_raw))
        self.y_history.append(y_max_now)
        n_steps = len(self.y_history)

        # 更新改善状态
        if y_max_now > self.current_max + 1e-8:
            self.current_max = y_max_now
            self.stagnant_count = 0
        else:
            self.stagnant_count += 1

        # 不足最少步数，强制继续
        if n_steps < self.min_steps:
            return 'continue'

        # 场景 B：正在爬坡（最近有改善），且 EI 依然充裕 -> 允许追加（借贷）
        if self.stagnant_count == 0 and ei_norm > self.ei_exit_thresh * 5:
            self.extra_steps += 1
            return 'extend'

        # v3.4 核心安全锁：如果当前区域探测不充分（方差依然很高），禁止任何早停动作
        if max_std > self.uncertainty_thresh:
            return 'continue'

        # 场景 C：见好就收 - 有历史成果但增益趋零
        if len(self.y_history) >= 2:
            y_range = max(abs(self.current_max), 1e-8)
            rel_improvement = (y_max_now - self.y_history[-2]) / y_range
            if rel_improvement < self.convergence_eps and ei_norm < self.ei_exit_thresh:
                return 'stop'

        # 场景 A：止损 - 长时间停滞且 EI 耗尽
        if self.stagnant_count >= self.patience and ei_norm < self.ei_exit_thresh:
            return 'stop'

        return 'continue'


def _compute_metrics(gpr, X_observed, Y_t, bounds, n_samples: int = 200):
    """
    在变换空间采样，计算归一化 EI 指标和最大不确定性（标准差）。
    [v3.4] 引入 max_std 作为不确定性门控。
    """
    state = np.random.get_state()
    X_test = np.random.uniform(bounds[:, 0], bounds[:, 1], size=(n_samples, bounds.shape[0]))
    np.random.set_state(state)

    # 同时获取均值和标准差
    mu, std = gpr.predict(X_test, return_std=True)
    ei_vals = expected_improvement(X_test, X_observed, Y_t, gpr, xi=0.0)
    
    return float(np.max(ei_vals)), float(np.max(std))


def run_inner_bo(pipeline, target_func, n_iter, x_init, y_init, bounds,
                 gmax=None, controller: EarlyStopController = None,
                 global_y_pool: np.ndarray = None,
                 max_allowed_steps: int = 999):
    """
    内层 BO 循环。
    max_allowed_steps: 强制硬上限，防止总预算超支。
    """
    wrapped = WrappedTarget(target_func, pipeline)
    X   = x_init.copy()
    Y_t = pipeline.forward(y_init)

    gpr = GaussianProcessRegressor(
        kernel=C(1.0) * RBF(1.0),
        n_restarts_optimizer=3,
        alpha=1e-5,
    )

    steps_used = 0
    # 强制硬上限由调用方计算得出，此处直接使用
    max_steps_this_run = max_allowed_steps

    for step in range(max_steps_this_run):
        if step >= n_iter and controller is None:
            break  # 无控制器时严格遵守 n_iter

        gpr.fit(X, Y_t)
        nx  = propose_next_sample(expected_improvement, X, Y_t, gpr, bounds)
        ny  = wrapped(nx)
        X   = np.vstack((X, nx))
        Y_t = np.vstack((Y_t, ny))
        steps_used += 1

        # ---- 早停控制器逻辑（每步结束后执行）----
        if controller is not None and step >= controller.min_steps - 1:
            # 计算物理空间 y 范围（用于归一化 EI）
            ref_pool = global_y_pool if global_y_pool is not None else y_init
            y_range = float(np.max(ref_pool)) - float(np.min(ref_pool))
            y_range = max(y_range, 1e-6)  # 防止除零

            ei_raw, max_std = _compute_metrics(gpr, X, Y_t, bounds)
            ei_norm = ei_raw / y_range

            # 向控制器汇报当前物理池状态，增加不确定性指标
            Y_raw_now = np.array([pipeline.backward(y) for y in Y_t])
            signal = controller.update(Y_raw_now, ei_norm, max_std)

            if signal == 'stop':
                break
            elif signal == 'extend':
                pass  # extra_steps 已在 controller 内部递增，循环自然延伸
            # 普通情况：如果已达原定 n_iter 且非追加，则停止
            elif step >= n_iter - 1:
                break

    # 全局安全 clamp
    y_min = float(np.min(y_init))
    y_max = float(np.max(y_init))
    Y_raw = np.array([pipeline.backward(y) for y in Y_t])
    y_max_safe = max(y_max * 100.0, 1e6)
    Y_raw = np.clip(Y_raw, y_min, y_max_safe)
    return np.max(Y_raw), X, Y_raw, gpr, steps_used


# ======================================================================
# 单次实验（一次 seed）
# ======================================================================

def _single_run(func_obj, m_outer, n_inner, n_init_meta, xi, seed,
                base_history_precomputed=None, use_early_exit=True,
                borrow_policy: str = 'moderate'):
    """执行一次完整的基线 BO + MN-BO（滚雪球多视角搜索）。"""

    bounds = func_obj.np_bounds()
    gmax   = func_obj.global_max

    np.random.seed(seed)
    n_init = 5
    X_init = np.random.uniform(bounds[:, 0], bounds[:, 1], size=(n_init, 1))
    Y_init = func_obj(X_init.flatten()).reshape(-1, 1)

    # MN-BO 总采样数
    total_budget = (n_init_meta + m_outer) * n_inner

    # ---- 基线 BO ----
    if base_history_precomputed is not None:
        # 核心逻辑：从预计算的全量历史中截取当前预算对应的步数
        # 注意：precomputed 历史包含初始化的 5 个点，所以总长度应为 n_init + budget
        y_slice = base_history_precomputed[:n_init + total_budget]
        base_max = float(np.max(y_slice))
        y_base_full = base_history_precomputed # 保持引用用于继续传递
        x_base, y_base, gpr_base = None, None, None
    else:
        print(f"      [基线 BO] 分配公平采样预算: {total_budget} 步")
        base_max, x_base, y_base, gpr_base, _ = run_inner_bo(
            TransformerPipeline([IdentityOperator()]),
            func_obj, total_budget, X_init, Y_init, bounds, gmax=gmax,
        )
        y_base_full = y_base.flatten().tolist()

    outer_bounds = get_outer_bounds()

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

    # 初始化早停控制器
    if use_early_exit:
        controller = EarlyStopController(
            patience=max(3, n_inner // 2),
            ei_exit_thresh=0.005, 
            convergence_eps=0.001,
            min_steps=3, 
            borrow_policy=borrow_policy,
            uncertainty_thresh=0.3  # v3.4 认知不确定性锁
        )
    else:
        controller = None

    total_steps_used = 0   # 统计实际消耗步数
    total_steps_budget = (n_init_meta + m_outer) * n_inner  # 名义总预算
    remaining_budget = total_steps_budget

    # ---- 外层初始点循环 ----
    for i, init_pt in enumerate(X_meta_init):
        pipe, ps = params_to_pipeline(init_pt, Y_init)
        pool_size_before = len(global_X_pool)
        if controller:
            controller.reset()

        # [v3.3] 三分支信贷调度逻辑
        remaining_views = (n_init_meta - 1 - i) + m_outer
        hard_limit = remaining_budget - (remaining_views * 3) # 全局硬保底
        
        if borrow_policy == 'conservative':
            nominal_so_far = (i + 1) * n_inner
            max_allowed = nominal_so_far - total_steps_used
        elif borrow_policy == 'moderate':
            max_allowed = 2 * n_inner
        else:
            max_allowed = hard_limit
        
        max_allowed = min(max(3, max_allowed), hard_limit)

        found, xs, ys_raw, lgpr, steps = run_inner_bo(
            pipe, func_obj, n_inner,
            global_X_pool, global_Y_pool, bounds, gmax=gmax,
            controller=controller, global_y_pool=global_Y_pool,
            max_allowed_steps=int(max_allowed))
        
        total_steps_used += steps
        remaining_budget -= steps

        # 更新池子与 Meta-GP 观测
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
            print(f"      初始点 {i+1}/{n_init_meta} 完成  最佳={max_found:.6f}  步数={steps}/{n_inner}")
        
        if remaining_budget <= 0: break

    # ---- 外层 GP 迭代 ----
    for m in range(m_outer):
        if remaining_budget <= 0: break
        
        Xm = np.array(X_meta)
        Ym = np.array(Y_meta).reshape(-1, 1)
        meta_gpr.fit(Xm, Ym)
        params = propose_next_sample(meta_ei, Xm, Ym, meta_gpr, outer_bounds)

        pipe, ps = params_to_pipeline(params, Y_init)
        pool_size_before = len(global_X_pool)
        if controller:
            controller.reset()

        # [v3.3] 三分支信贷调度逻辑
        remaining_views = (m_outer - 1 - m)
        hard_limit = remaining_budget - (remaining_views * 3) # 全局硬保底
        
        if borrow_policy == 'conservative':
            nominal_so_far = n_init_meta * n_inner + (m + 1) * n_inner
            max_allowed = nominal_so_far - total_steps_used
        elif borrow_policy == 'moderate':
            max_allowed = 2 * n_inner
        else:
            max_allowed = hard_limit
        
        max_allowed = min(max(3, max_allowed), hard_limit)

        print(f"      外层GP {m+1}/{m_outer}  池子:{pool_size_before}点  MaxAllowed={int(max_allowed)}")

        found, xs, ys_raw, lgpr, steps = run_inner_bo(
            pipe, func_obj, n_inner,
            global_X_pool, global_Y_pool, bounds, gmax=gmax,
            controller=controller, global_y_pool=global_Y_pool,
            max_allowed_steps=int(max_allowed))
        
        total_steps_used += steps
        remaining_budget -= steps

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
    steps_saved = max(0, total_steps_budget - total_steps_used)

    return {
        "base_max":    base_max,
        "mnbo_max":    mnbo_max,
        "y_base_full": y_base_full,
        "steps_used":  total_steps_used,
        "steps_budget": total_steps_budget,
        "steps_saved": steps_saved,
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
                   detailed_results_dir: str = "results/_detailed_reports",
                   seed_base: int = 42,
                   base_histories_precomputed: list = None,
                   use_early_exit: bool = True,
                   borrow_policy: str = 'moderate'):
    """对单个函数运行 n_repeats 次独立实验，取均值输出报告。"""
    func_start_time = time.time()

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
        futures = []
        for i, s in enumerate(seeds):
            p_base = base_histories_precomputed[i] if base_histories_precomputed is not None else None
            futures.append(
                executor.submit(_single_run, func_obj, m_outer, n_inner, n_init_meta, xi, s, p_base, use_early_exit, borrow_policy)
            )
        for f in futures:
            run_results.append(f.result())

    # ---- 统计汇总 ----
    base_maxes = np.array([r["base_max"]  for r in run_results])
    mnbo_maxes = np.array([r["mnbo_max"]  for r in run_results])
    base_histories = [r["y_base_full"] for r in run_results]
    steps_used_list = np.array([r["steps_used"]  for r in run_results])
    steps_budget    = run_results[0]["steps_budget"] if run_results else 0
    avg_steps_used  = float(steps_used_list.mean())
    avg_steps_saved = float(steps_budget - avg_steps_used)
    steps_save_pct  = avg_steps_saved / max(steps_budget, 1) * 100
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
    print(f"  步数节省    : {avg_steps_saved:.1f}/{steps_budget} 步 ({steps_save_pct:.1f}%)")
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

    # 安全检查：如果基线被复用，这些可能为 None
    if gpr_base is not None:
        mu_base, _ = gpr_base.predict(x_plot, return_std=True)
    else:
        mu_base = np.zeros_like(y_gt)
        
    mu_trans, _ = gpr_best.predict(x_plot, return_std=True)
    mu_raw      = np.array(
        [best_pipe.backward(np.array([[v]])) for v in mu_trans.flatten()]
    ).flatten()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # 绘制基线图（如果可用）
    ax1.plot(x_plot, y_gt, "r:", lw=1.5, label="Ground Truth", alpha=0.85)
    if gpr_base is not None:
        ax1.plot(x_plot, mu_base, "b-", lw=1.5, label="GP Mean", alpha=0.85)
        ax1.scatter(x_base.flatten(), y_base, c="black", marker="x", s=40, label="Samples")
        ax1.set_title(f"Baseline BO\n(Max={med_base_max:.4f})")
    else:
        ax1.text(0.5, 0.5, "Baseline Reused\n(See previous report)", ha='center', va='center')
        ax1.set_title(f"Baseline BO (Cached)\n(Max={med_base_max:.4f})")
    ax1.legend()

    # 绘制 MN-BO 图
    ax2.plot(x_plot, y_gt, "r:", lw=1.5, label="Ground Truth", alpha=0.85)
    ax2.plot(x_plot, mu_raw, "b-", lw=1.5, label="GP Mean", alpha=0.85)
    ax2.scatter(xs_best.flatten(), ys_best, c="black", marker="x", s=40, label="Samples")
    ax2.set_title(f"MN-BO\n(Max={med_mnbo_max:.4f})")
    ax2.legend()
    # 公共修饰
    for ax in [ax1, ax2]:
        ax.axhline(gmax, color="gray", ls="--", alpha=0.5, label=f"Theoretical Max ({gmax})")
        ax.set_xlabel("x")
        ax.set_ylabel("f(x)")
        ax.legend(fontsize=8)

    plt.tight_layout()

    # ---- 写日志 ----
    
    # 构造显示的策略名称
    if not use_early_exit:
        display_policy = "Fixed (No Early Stop)"
    else:
        display_policy = f"Adaptive ({borrow_policy.capitalize()})"

    # 在保存汇总前计算耗时
    func_duration = time.time() - func_start_time

    # 所有的详细报告和图片现在统一放入 _detailed_reports 子目录中
    logger  = ExperimentLogger(func_obj, results_dir=detailed_results_dir)
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
        total_time=func_duration,
        m_val=m_outer,
        n_val=n_inner,
        total_budget=steps_budget,
        policy=display_policy
    )
    # 额外在 md 中记录原始数据供查看（保留4位小数）
    raw_base_str = ", ".join([f"{x:.4f}" for x in base_maxes])
    raw_mnbo_str = ", ".join([f"{x:.4f}" for x in mnbo_maxes])
    with open(md_path, "a", encoding="utf-8") as f:
        f.write("\n## 4. 原始数据 (Raw Data)\n\n")
        f.write(f"- 基线 Max 序列: `[{raw_base_str}]`\n")
        f.write(f"- MN-BO Max 序列: `[{raw_mnbo_str}]`\n")
        f.write(f"- 步数节省: 平均 {avg_steps_saved:.1f}/{steps_budget} 步 ({steps_save_pct:.1f}% 节省)\n")

    # 将结果返回，用于最后大汇总
    return {
        "avg_base_max": avg_base, "std_base_max": std_base,
        "avg_mnbo_max": avg_mnbo, "std_mnbo_max": std_mnbo,
        "avg_max_diff": avg_diff, "std_max_diff": std_diff,
        "base_success": base_success_rate,
        "mnbo_success": mnbo_success_rate,
        "base_histories": base_histories,
        "avg_steps_saved": avg_steps_saved,
        "steps_budget":    steps_budget,
        "steps_save_pct":  steps_save_pct,
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
        "--no-early-exit", action="store_true",
        help="关闭自适应早停机制（始终跑满固定步数）"
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
    parser.add_argument(
        "--borrow-policy", type=str, choices=['conservative', 'moderate', 'aggressive'],
        default='moderate',
        help="自适应信贷策略：conservative (仅限存款), moderate (限额贷款2N), aggressive (无限授信)"
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

    # 路径准备 (v3.3 五大分类体系)
    if not args.no_early_exit:
        # 早停版
        summary_dir = "results/_summary_adaptive"
        detailed_results_dir = "results/_detailed_reports/adaptive"
        log_dir = "results/_summary_adaptive/logs"
    else:
        # 非早停版
        summary_dir = "results/_summary_fixed"
        detailed_results_dir = "results/_detailed_reports/fixed"
        log_dir = "results/_summary_fixed/logs"

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
        # ---- 动态参数确定逻辑 ----
        # 优先级：1. 命令行参数 (--outer-iters, --inner-iters)
        #        2. 函数特定配置 (FUNCTION_SPECIFIC_MN)
        #        3. 默认全局值 + 梯度预算 (TARGET_BUDGETS)
        
        current_m = _M
        current_n = _N
        
        # 如果用户没有显式指定 M 和 N，则尝试使用硬编码配置
        if args.outer_iters is None and args.inner_iters is None:
            if name in FUNCTION_SPECIFIC_MN:
                current_m, current_n = FUNCTION_SPECIFIC_MN[name]
                print(f"\n[策略适配] 函数: {name} | 使用硬编码优化配置: M={current_m}, N={current_n}")
            else:
                # 回退到原本的梯度预算逻辑
                target_b = TARGET_BUDGETS.get(name, 120)
                current_n = max(1, target_b // (_IM + _M))
                print(f"\n[梯度预算] 函数: {name} | 目标预算: {target_b} | 动态计算 N = {current_n}")
        else:
            # 如果用户指定了其中之一，则使用全局覆盖
            if args.inner_iters is None:
                target_b = TARGET_BUDGETS.get(name, 120)
                current_n = max(1, target_b // (_IM + current_m))
            print(f"\n[全局覆盖] 函数: {name} | 使用参数: M={current_m}, N={current_n}")

        r = run_experiment(name, m_outer=current_m, n_inner=current_n, n_repeats=_R,
                           summary_path=summary_path,
                           detailed_results_dir=detailed_results_dir,
                           seed_base=_SEED,
                           use_early_exit=not args.no_early_exit,
                           borrow_policy=args.borrow_policy)
        r['m_val'] = current_m
        r['n_val'] = current_n
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
    m, s = divmod(int(total_time), 60)
    time_str = f"{total_time:.1f}s ({m}分{s}秒)"
    
    print(f"\n  全量总耗时: {time_str}")
    print(f"  累计汇总报告：{summary_path}")

    # 向累计报告追加总时长信息
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(f"\n\n---")
        f.write(f"\n**全量总实验时长**：{time_str}  \n")
        f.write(f"**平均单函数耗时**：{total_time/len(chosen):.1f}s")

    # 生成带时间戳的批次汇总文件（用于快照）
    batch_summary_path = os.path.join(summary_dir, f"batch_summary_{ts}.md")
    with open(batch_summary_path, "w", encoding="utf-8") as f:
        f.write(f"# 批量实验汇总报告 (Snapshot)\n\n")
        f.write(f"- **生成时间**: {ts}\n")
        f.write(f"- **策略模式**: `{args.borrow_policy.capitalize()}`\n")
        f.write(f"- **总实验时长**: {time_str}\n")
        f.write(f"- **平均单函数耗时**: {total_time/len(chosen):.1f}s\n")
        f.write(f"- **核心参数**: M={_M}, N(Nominal)={_N}, R={_R}, Init={_IM}\n\n")
        
        f.write("| 函数 | 基线 Max | MN-BO Max | Max 差值 | MN-BO 成功率 | M/N 配置 |\n")
        f.write("|------|----------|-----------|----------|-------------|---------|\n")
        for name, r in results.items():
            diff_str = f"**{r['avg_max_diff']:.4f}**" if r['avg_max_diff'] > 0 else f"{r['avg_max_diff']:.4f}"
            mn_cfg = f"({r['m_val']}, {r['n_val']})"
            f.write(f"| {name} | {r['avg_base_max']:.4f} | {r['avg_mnbo_max']:.4f} | {diff_str} | {r['mnbo_success']*100:.1f}% | {mn_cfg} |\n")
        
    print(f"  批次快照已生成：{batch_summary_path}")
    sys.stdout.flush()
