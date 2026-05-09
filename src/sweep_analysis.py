import os
import sys
import time

# 确保 src/ 目录在 Python 路径中，以便能够导入 main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import run_experiment
from benchmark import list_functions

def run_sweep():
    # 设定实验基准
    FIXED_R = 80
    FIXED_SEED = 1012
    
    # 细化黄金鲁棒区 (M ∈ [4, 9], Budget ≈ 120, I=2)
    combinations = [
        (4, 20, "M4-Balanced"),
        (5, 17, "M5-Step"),
        (6, 15, "M6-Step"),
        (7, 13, "M7-Step"),
        (8, 12, "M8-Robust"),
        (9, 11, "M9-Limit"),
    ]
    
    # 运行全部 12 个基准函数
    test_funcs = list_functions()
    
    results_summary = []
    
    print(f"开始全量 M/N 扫参实验 | R={FIXED_R} | Seed={FIXED_SEED}")
    print("=" * 70)
    
    ts = time.strftime("%Y%m%d_%H%M%S")
    summary_dir = "results/summary"
    os.makedirs(summary_dir, exist_ok=True)
    sweep_report_path = os.path.join(summary_dir, f"sweep_report_{ts}.md")
    
    for m, n, desc in combinations:
        print(f"\n>>> 正在运行组合: M={m}, N={n} ({desc})")
        
        combo_results = {"m": m, "n": n, "desc": desc, "data": {}}
        
        for func in test_funcs:
            print(f"    - 测试函数: {func}")
            res = run_experiment(
                func, 
                m_outer=m, 
                n_inner=n, 
                n_init_meta=2, 
                n_repeats=FIXED_R, 
                seed_base=FIXED_SEED,
                summary_path=os.path.join(summary_dir, f"sweep_raw_{ts}.md")
            )
            combo_results["data"][func] = {
                "avg_max": res["avg_mnbo_max"],
                "success": res["mnbo_success"]
            }
        
        results_summary.append(combo_results)
    
    # 生成最终 Markdown 报告
    with open(sweep_report_path, "w", encoding="utf-8") as f:
        f.write(f"# 全量 M/N 策略扫参报告 (Budget≈120, R={FIXED_R})\n\n")
        f.write(f"- **实验时间**: {ts}\n")
        f.write(f"- **固定种子**: {FIXED_SEED}\n\n")
        
        for func in test_funcs:
            f.write(f"## 函数: {func}\n\n")
            f.write("| 策略描述 | M (视角) | N (深度) | 成功率 | 平均 Max |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for item in results_summary:
                d = item["data"][func]
                f.write(f"| {item['desc']} | {item['m']} | {item['n']} | {d['success']*100:.1f}% | {d['avg_max']:.4f} |\n")
            f.write("\n")
            
    print("\n" + "=" * 70)
    print(f"全量扫参任务完成！报告已生成至: {sweep_report_path}")
    print("=" * 70)

if __name__ == "__main__":
    run_sweep()
