# M×N 滚雪球多视角搜索（MN-BO）

验证 MN-BO 方法在欺骗性函数上的优化效果：外层元 GP 在 8D 连续空间智能搜索最优目标空间变换配置，内层 BO 采用"滚雪球"数据累积机制执行优化。

## 核心架构设计：有序算子链 (Ordered Operator Chain)

MN-BO 的核心创新在于将复杂的非线性空间变换分解为一个**有序的加工链条**，并通过元 GP 在连续搜索空间内对其进行参数化控制。

### 1. 执行顺序 (Execution Flow)
数据在 Pipeline 中遵循固定物理逻辑的加工顺序：
**LogWarper** (非线性定型) → **PowerWarper** (深度挖掘) → **StandardScaler** (均值/方差对齐) → **MinMaxScaler** (硬边界归一化)

### 2. 连续参数化表示 (Continuous Parameterization)
虽然执行是有序的，但元 GP 看到的搜索空间是一个**平行的 8D 向量**：
- `p[0,1]`：Log 强度控制 (Gate, Alpha)
- `p[2,3]`：Power 深度挖掘控制 (Gate, Index)
- `p[4,5,6]`：StandardScaler 线性对齐 (Gate, Shift, Scale)
- `p[7]`：MinMaxScaler 归一化 (Gate)

### 3. 设计哲学
*   **规避离散陷阱**：通过固定逻辑顺序，避免了搜索空间涉及离散排列组合，确保元 GP 能在连续空间高效建模。
*   **架构自动筛选**：通过 `Gate` 参数（0 到 1 连续变化），元 GP 可以平滑地关闭或开启某个算子，实现了"在连续空间中进行架构筛选"的效果。

## 预算计算机制 (滚雪球模式)

当前采用 **滚雪球 (Snowball)** 架构，数据池在各轮迭代间全量累积，不再区分海选与冲刺：
- **MN-BO 总预算**：`(I + M) × N` 步。
- **基线 BO 开销**：获得与 MN-BO 完全对等的总采样步数。

**当前默认配置 (High Intensity Comparison)**:
- 初始变换点 $I=2$, 外层元迭代轮数 $M=8$, 挖掘深度 $N=12, R=8$。
- **动态预算分配**：针对函数难度阶梯化配置 30~120 步总预算。
- **早停机制 (v3.4)**：引入“认知不确定性锁”，仅在模型置信度高（Max Std < 0.3）且收益递减时触发提前退出。

## 快速运行 (Standardized Environment)

本项目已规范化环境配置。你可以直接使用 `./.venv` 下的 Python，无需手动 `conda activate`。

```bash
# 1. 运行全部函数（使用默认高强度配置：120步，8次重复，并行执行）
./.venv/bin/python src/main.py --all

# 2. 交互式菜单（手动选择函数）
./.venv/bin/python src/main.py

# 3. 指定函数运行
./.venv/bin/python src/main.py cliff_func needle_in_haystack_func

# 4. 手动调整参数
./.venv/bin/python src/main.py --all -R 4 -M 10 -N 15
```


## 目录结构

```
demo_mn2/
├── src/                  # 源码
│   ├── main.py          # 实验入口（支持多进程并行、成功率统计）
│   ├── benchmark.py     # 核心工具层（ExperimentLogger、SuccessRate 逻辑）
│   ├── bo_transform.py  # 变换算子库（8D 连续空间参数化）
│   └── functions/        # 12 个基准测试函数
├── results/              # 实验输出
│   ├── _milestones/     # 核心实验成果归档（性能标杆）
│   ├── _summary_fixed/  # 固定预算模式报告
│   ├── _summary_adaptive/ # 自适应早停模式报告
│   └── <func_name>/     # 各函数的独立详细报告与绘图
├── reports/              # 汇报材料与组会 PPT
└── states.md             # 实验决策日志与 AI 记忆（上帝视角）
```

## 核心评价指标
1.  **Success Rate (成功率)**：找到理论最大值 90% 以上的次数占比。反映算法的**鲁棒性**。
2.  **Raw Data Sequence**：展示所有重复实验的原始 Max 值。反映算法的**真实波动情况**。
3.  **Max 差值**：MN-BO 与基线在同样预算下的绝对得分差距。
4.  **Step Saving Rate**：自适应模式下节省的步数百分比（v3.4 核心指标）。

---

## 项目里程碑 (Milestones)

*   **Gold Standard (2026-05-11)**: 在 `feat/hardcoded-mn-tuning` 分支下，通过对 `needle_in_haystack` 函数硬编码 M=4, N=20，成功实现了 **+2.72** 的性能压制（成功率 62.5%）。
*   **v3.4 Architecture (2026-05-10)**: 实装“认知不确定性门控”早停机制，解决了平原地形的误判问题。
