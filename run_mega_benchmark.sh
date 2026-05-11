#!/bin/bash

# MN-BO Mega Benchmark Script (R=80)
# 目标：全量对比 Fixed, Conservative, Moderate, Aggressive 四种调度模式

PYTHON_EXE="/opt/homebrew/Caskroom/miniconda/base/envs/bo_env/bin/python"
REPEATS=80

echo "🚀 开始大规模实验计划 (R=$REPEATS)..."
echo "估计总优化轮数: $((REPEATS * 12 * 4)) 轮"

# 创建输出目录
mkdir -p results/_summary_adaptive
mkdir -p results/_summary_fixed

# 1. 运行固定预算版 (Fixed/Baseline)
echo "------------------------------------------------"
echo "[Stage 1/4] 运行 Fixed (No Early Exit) 模式..."
$PYTHON_EXE src/main.py --all -R $REPEATS --no-early-exit

# 2. 运行保守借贷版 (Conservative)
echo "------------------------------------------------"
echo "[Stage 2/4] 运行 Adaptive (Conservative) 模式..."
$PYTHON_EXE src/main.py --all -R $REPEATS --borrow-policy conservative

# 3. 运行稳健借贷版 (Moderate)
echo "------------------------------------------------"
echo "[Stage 3/4] 运行 Adaptive (Moderate) 模式..."
$PYTHON_EXE src/main.py --all -R $REPEATS --borrow-policy moderate

# 4. 运行激进借贷版 (Aggressive)
echo "------------------------------------------------"
echo "[Stage 4/4] 运行 Adaptive (Aggressive) 模式..."
$PYTHON_EXE src/main.py --all -R $REPEATS --borrow-policy aggressive

echo "------------------------------------------------"
echo "✅ 大规模实验全部完成！请在 results/ 目录下查阅各时间戳报告。"
