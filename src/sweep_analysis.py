import os
import sys
import time

# 确保 src/ 目录在 Python 路径中，以便能够导入 main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import run_experiment
from benchmark import list_functions, get_func

def run_sweep():
    start_time = time.time()
    # 设定实验基准
    FIXED_R = 8
    FIXED_SEED = 506
    N_INIT_META = 2
    
    # 难度阶梯预算分配 (Targeting ~90% Baseline Success)
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
    
    # 扫描的外层迭代轮数 M
    m_values = [4, 5, 6, 7, 8, 9]
    
    # 运行全部 12 个基准函数
    test_funcs = list_functions()
    
    results_summary = []
    baseline_cache = {}    # 缓存全量基线历史 {func: [[y1,y2,...], [y1,y2,...], ...]} (R 个序列)
    
    print(f"开始梯度化预算 M/N 扫参实验 | R={FIXED_R} | Seed={FIXED_SEED}")
    print("=" * 70)
    
    ts = time.strftime("%Y%m%d_%H%M%S")
    summary_dir = "results/summary"
    os.makedirs(summary_dir, exist_ok=True)
    sweep_report_path = os.path.join(summary_dir, f"sweep_report_{ts}.md")
    
    for m in m_values:
        print(f"\n>>> 正在运行外层维度: M={m}")
        
        combo_results = {"m": m, "data": {}}
        
        for func in test_funcs:
            # 动态计算当前函数在该 M 下的 N
            target_b = TARGET_BUDGETS.get(func, 120)
            n_inner = max(1, target_b // (N_INIT_META + m))
            actual_b = (N_INIT_META + m) * n_inner
            
            # 检查是否有缓存的基线全量历史
            precomputed_histories = baseline_cache.get(func)
            if precomputed_histories:
                print(f"    - 函数: {func:25} | Budget: {actual_b} (N={n_inner}) [基线历史切片复用]")
            else:
                print(f"    - 函数: {func:25} | Budget: {actual_b} (N={n_inner})")
            
            res = run_experiment(
                func, 
                m_outer=m, 
                n_inner=n_inner, 
                n_init_meta=N_INIT_META, 
                n_repeats=FIXED_R, 
                seed_base=FIXED_SEED,
                summary_path=os.path.join(summary_dir, f"sweep_raw_{ts}.md"),
                base_histories_precomputed=precomputed_histories
            )
            
            # 如果是第一次跑该函数，缓存其全量历史
            if precomputed_histories is None:
                baseline_cache[func] = res["base_histories"]
            
            combo_results["data"][func] = {
                "n": n_inner,
                "actual_budget": actual_b,
                "avg_max": res["avg_mnbo_max"],
                "success": res["mnbo_success"],
                "base_avg": res["avg_base_max"],
                "base_success": res["base_success"]
            }
        
        results_summary.append(combo_results)
    
    # 生成最终 Markdown 报告
    duration = time.time() - start_time
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    
    with open(sweep_report_path, "w", encoding="utf-8") as f:
        f.write(f"# 梯度化预算 M/N 扫参报告 (History-Sliced, R={FIXED_R})\n\n")
        f.write(f"- **实验时间**: {ts}\n")
        f.write(f"- **总耗时**: {minutes}分{seconds}秒\n")
        f.write(f"- **说明**: 基线结果通过全量历史切片得出，确保了每一行对比的预算公平性。\n\n")
        
        for func in test_funcs:
            f_obj = get_func(func)
            f.write(f"## 函数: {func} (GlobalMax: {f_obj.global_max})\n\n")
            f.write("| 策略描述 | M | N | 预算 | 基线成功率 | MN-BO成功率 | 基线平均Max | MN-BO平均Max |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
            
            for combo in results_summary:
                m = combo["m"]
                data = combo["data"][func]
                
                win_tag = " ⭐" if data["avg_max"] > data["base_avg"] else ""
                
                f.write(f"| M{m}-Adaptive | {m} | {data['n']} | {data['actual_budget']} | "
                        f"{data['base_success']*100:.1f}% | {data['success']*100:.1f}% | "
                        f"{data['base_avg']:.4f} | {data['avg_max']:.4f}{win_tag} |\n")
            f.write("\n")

    print(f"\n扫参任务完成！报告已生成至: {sweep_report_path}")

if __name__ == "__main__":
    run_sweep()
