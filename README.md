# M×N 双层贝叶斯优化（MN-BO）

验证 MN-BO 方法在欺骗性函数上的优化效果：外层 GP 搜索最优目标空间变换配置，内层标准 BO 执行优化。


## 目录结构

```
demo_mn2/
├── .workbuddy/          # AI 工作记忆（自动生成，勿删）
├── src/                  # 源码
│   ├── main.py          # 实验入口（交互菜单 / 命令行）
│   ├── benchmark.py     # BO 工具函数 + ExperimentLogger
│   ├── bo_transform.py  # 变换算子（【稳定模式】4D 外层空间：StandardScaler + MinMaxScaler）
│   ├── generate_ppt.js   # PPT 生成脚本
│   ├── package.json      # npm 依赖
│   └── functions/        # 基准函数包（12 个函数）
│       ├── _base.py      # BenchmarkFunc 抽象基类
│       ├── __init__.py   # REGISTRY 注册表
│       └── *.py          # 各测试函数实现
├── results/              # 实验输出
│   ├── summary_report.md      # 汇总对比表
│   ├── archive/               # 历史图片归档
│   └── <func_name>/           # 按函数分目录
│       ├── *.md               # 单函数详细报告
│       └── plots/             # 可视化图
├── reports/              # 文档与汇报材料
│   ├── 思路.md
│   ├── 当前情况与架构.md
│   ├── 下一步安排.md
│   ├── agent_architecture.html
│   └── MN-BO组会报告.pptx
└── README.md
```

## 快速运行

```bash
# conda 环境
D:\Miniconda3\envs\bo_env\python.exe src/main.py

# 交互式菜单
python src/main.py

# 指定函数
python src/main.py deceptive_trap_func

# 默认模式（全部 12 个函数，M=5, N=8, I=8, R=5）
python src/main.py --all

# 快速验证（单函数，单次重复，约 2-5 分钟）
python src/main.py cliff_func -R 1 -M 5 -N 8 -I 8

# 快速验证（全部 12 个函数，单次重复）
python src/main.py --all -R 1 -M 5 -N 8 -I 8

# 指定随机种子（保证实验可复现）
python src/main.py --all --seed 42
python src/main.py multipeak_func --seed 100

# 完整实验（需显式指定旧默认参数）
python src/main.py --all -R 5 -M 20 -N 12 -I 36
```

## 待处理算子（已注释，待架构重构后恢复）

以下 4 个算子因 `backward()` 中存在 `exp` / `log` / `power(1/p)` 等数值不稳定操作，
在稳定算子模式下已注释。待外层架构引入预算控制或 backward 安全校验后恢复：

| 算子 | 风险点 | 状态 |
|------|--------|------|
| LogWarper | `backward()` 含 `exp()`，大值溢出 | 🔴 待处理 |
| PowerTransform | `backward()` 含 `power(1/p)`，p→0 时爆炸 | 🔴 待处理 |
| SigmoidWarper | `backward()` 含 `log(y/(1-y))`，边界敏感 | 🟡 待处理 |
| RankTransform | 离散非连续，GP 难建模但不溢出 | 🟡 待处理 |

当前启用的稳定算子：**StandardScaler**（线性标准化）+ **MinMaxScaler**（线性归一化）。

## 测试函数（12 个）

deceptive_trap / multipeak / flat_region / asymmetric / noisy /
periodic_trap / needle_in_haystack / cliff / double_well /
oscillating_decay / step / valley_ridge

## 核心参数

| 命令行参数 | 代码默认值 | 说明 |
|-----------|-----------|------|
| `-R` | 5 | 每个函数独立运行的重复次数（用于取均值消除随机性） |
| `-I` | **8** | 【阶段一】外层初始拉丁超方海选盲测点数（4D 空间推荐 12~36） |
| `-M` | **5** | 【阶段一】外层智能搜索 GP 迭代次数（推荐 10~20） |
| `-N` | **8** | 【阶段一】内层实地考察的 BO 步数（用于对选定的算子进行打分） |
| `-E` | **20**| 【阶段二】全局经验池终极爆发的冲刺步数 |
| 无 | 0.05 | EI 探索参数 |

> **计算机制说明**：阶段一（海选+搜索）会跑 `(I + M) × N` 步内层测试，阶段二跑 `E` 步冲刺。总采样预算为 `(I + M) × N + E` 步，基线 BO 会被赋予完全相等的总步数进行绝对公平对比。

### 核心评价指标
实验通过直接比对 `Max`（搜索找到的最高值）而非不直观的 `Gap`。
- **Max 差值(正优)**：`MN-BO Max - 基线 Max`。正数即代表 MN-BO 表现更优异。

### 计算量估算（公平预算对齐版）

> **绝对公平原则**：在所有模式下，基线 BO 被赋予了与 MN-BO 完全对等的总评估次数，确保两者获得同等的算力机会。

**默认模式**（直接运行 `python src/main.py --all`，不加参数）：
- **MN-BO 单次开销**：
  - 阶段一(外层初始 8 点)：8 × 8 = 64 步
  - 阶段一(外层搜索 5 次)：5 × 8 = 40 步
  - 阶段二(终极冲刺)：20 步
  - MN-BO 合计：124 步
- **基线 BO 开销**：获得等同的 124 步迭代机会。
- **12 函数全跑（R=5）总计：** 12 × (124 + 124 + 5(全局初始化)) × 5 = 15,180 次评估

**中等实验模式**（单次验证时间可控，约 15-20 分钟跑完）：
```bash
python src/main.py --all -R 1 -M 10 -N 10 -I 12 -E 20
```
- **MN-BO 单次开销**：`12×10 + 10×10 + 20` = 240 步
- **基线 BO 开销**：获得等同的 240 步。

**大实验模式**（全量深度搜索，预计耗时 >1 小时）：
```bash
python src/main.py --all -R 1 -M 20 -N 12 -I 36 -E 20
```
- **MN-BO 单次开销**：`36×12 + 20×12 + 20` = 692 步
- **基线 BO 开销**：获得等同的 692 步。
