# M×N 滚雪球多视角搜索（MN-BO）
**Version: v3.4 (Information-Gated Evolution) | 2026-05-10**

验证 MN-BO 方法在复杂地形上的优化效果：外层元 GP 在 8D 连续空间智能搜索最优目标空间变换配置，内层 BO 采用"滚雪球"数据累积机制。**当前版本引入了基于不确定性门控的自适应资源调度系统。**

## 核心架构设计：自适应有序算子链

### 1. 有序算子流水线
**LogWarper** → **PowerWarper** → **StandardScaler** → **MinMaxScaler** (8D 参数化控制)

### 2. 自适应资源调度 (Adaptive Scheduling)
MN-BO 具备动态预算分配能力，通过以下两大核心机制平衡“效率”与“覆盖”：

#### A. 三分支借贷体系 (Borrowing Policies) - v3.3
通过 `--borrow-policy` 参数控制视角间的预算流转：
*   **Conservative (诚信派)**：仅允许使用先前视角节省下的预算，严禁透支未来。
*   **Moderate (稳健派 - 默认)**：允许预支未来预算，但单视角上限封顶为 $2N$。
*   **Aggressive (激进派)**：允许单视角吃掉绝大部分剩余预算，仅保留最低限度保底。

#### B. 认知不确定性锁 (Uncertainty Lock) - v3.4
针对“针尖函数”等稀疏奖励场景的数学保护：
*   **机制**：监控 GP 模型在搜索空间内的 **最大后验标准差 ($\sigma_{max}$)**。
*   **逻辑**：即使 EI 趋于零，只要 $\sigma_{max} > 0.3$（探测覆盖率不足），系统将强制锁定“早停”动作，确保完成保底的物理空间覆盖。
*   **权衡 (Trade-off)**：v3.4 在提升稳健性的同时，会因强制探索而增加步数消耗，导致分配给高潜力视角的“借贷红利”有所减少。这体现了探索安全性与资源利用效率之间的博弈。

---

## 架构演进史 (Architecture Evolution)

| 版本 | 核心特性 | 解决的问题 |
| :--- | :--- | :--- |
| **v3.2** | 8D 算子链 + 滚雪球继承 | 实现跨视角的经验累积与多维空间对齐。 |
| **v3.3** | `EarlyStopController` + 借贷体系 | 引入“及时止损”与“潜力追加”，实现约 30-50% 资源节省。 |
| **v3.4** | **不确定性门控 (Uncertainty Gate)** | 解决稀疏奖励下 EI 误判导致的假性收敛，提升搜索稳健性。 |

---

## 运行指南

```bash
# 激活环境
source /opt/homebrew/Caskroom/miniconda/base/bin/activate bo_env

# 1. 运行自适应版（推荐，使用稳健借贷策略）
python src/main.py --all -R 8 --borrow-policy moderate

# 2. 运行保守版（严禁透支，最高资源节省）
python src/main.py --all -R 8 --borrow-policy conservative

# 3. 运行固定预算版（基线对比）
python src/main.py --all -R 8 --no-early-exit
```

## 目录结构说明
*   `src/main.py`: 实验入口，支持 `--borrow-policy` 和全量耗时统计。
*   `results/_summary_adaptive/`: 累计汇总报告，包含策略标注与总执行时长。
*   `states.md`: 详细的实验决策日志与技术迭代记录。
*   `RULES.md`: AI 协作与版本维护规范。

## 核心评价指标
1.  **Success Rate (成功率)**：找到理论最大值 90% 以上的次数占比。
2.  **Resource Efficiency**：相比固定预算（120步）节省的百分比。
3.  **Execution Time**：包含单函数并行耗时与全量实验总时长。
