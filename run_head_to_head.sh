#!/bin/bash

# MN-BO Head-to-Head Comparison Script
# ---------------------------------------------------------
# 该脚本将顺序启动两组实验：
# 1. 自适应早停版 (结果存放在 results/_summary_earlystop/)
# 2. 原始固定步数版 (结果存放在 results/_summary/)
# ---------------------------------------------------------

PYTHON_EXE="/opt/homebrew/Caskroom/miniconda/base/envs/bo_env/bin/python"
R_VALUE=8

echo "=========================================================="
echo "🚀 启动 MN-BO 对比实验：自适应早停 vs 原始固定步数"
echo "开始时间: $(date)"
echo "重复次数 (R): $R_VALUE"
echo "=========================================================="

# 第一阶段：自适应早停版
echo -e "\n[Phase 1/2] 正在运行：自适应早停版 (Moderate Borrowing)..."
caffeinate -i $PYTHON_EXE src/main.py --all -R $R_VALUE --borrow-policy moderate

# 第二阶段：原始固定步数版
echo -e "\n[Phase 2/2] 正在运行：原始固定步数版 (No Early Exit)..."
caffeinate -i $PYTHON_EXE src/main.py --all -R $R_VALUE --no-early-exit --borrow-policy moderate

echo -e "\n=========================================================="
echo "✅ 对比实验全部完成！"
echo "结束时间: $(date)"
echo "----------------------------------------------------------"
echo "报告位置："
echo "  - 早停版: results/_summary_adaptive/"
echo "  - 原版  : results/_summary_fixed/"
echo "=========================================================="
