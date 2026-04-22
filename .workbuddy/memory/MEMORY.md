# MEMORY.md - 项目持久记忆

## 项目背景

- **项目名称**：M×N 双层贝叶斯优化（MN-BO）
- **项目路径**：`d:\2602-stu\paper\demo_mn2`
- **目标**：验证 MN-BO 方法在欺骗性函数上的优化效果
- **备份路径**：`d:\2602-stu\paper\demo_mn`（原始代码备份）

## Python 环境

- **conda 环境**：`D:\Miniconda3\envs\bo_env`
- **运行命令**：`D:\Miniconda3\envs\bo_env\python.exe src/main.py`

## 测试函数（共 12 个）

| 函数名 | 理论最大值 | 特点 |
|--------|-----------|------|
| `deceptive_trap_func` | 4.9048 | 欺骗性陷阱函数 |
| `multipeak_func` | 5.0 | 多峰函数 |
| `flat_region_func` | 3.0 | 平坦区域+尖峰 |
| `asymmetric_func` | 10.0 | 非对称函数 |
| `noisy_func` | 4.0 | 高噪声函数 |
| `periodic_trap_func` | 7.0 | 高频周期背景 + 隐藏全局尖峰 |
| `needle_in_haystack_func` | 10.0 | 极窄峰（σ≈0.01）被平坦区包围 |
| `cliff_func` | 8.0 | x=1 处梯度悬崖，GP 难建模 |
| `double_well_func` | 4.0 | 两个等高对称全局峰 |
| `oscillating_decay_func` | 3.5 | 高斯包络×正弦振荡 |
| `step_func` | 5.0 | 阶梯跳变，破坏 GP 平滑性假设 |
| `valley_ridge_func` | 6.0 | V 谷 + 远端山脊 |

## 项目文件结构（重构后，2026-04-21）

```
demo_mn2/
├── .workbuddy/              # AI 工作记忆（勿删）
├── src/                      # 源码
│   ├── main.py              # 实验入口（交互菜单 / 命令行）
│   ├── benchmark.py         # BO 工具函数 + ExperimentLogger（无函数定义）
│   ├── bo_transform.py      # 变换算子（连续参数化，6D 外层空间）
│   ├── generate_ppt.js      # PPT 生成脚本
│   ├── package.json          # npm 依赖
│   └── functions/           # 基准函数包（14 个文件）
│       ├── _base.py         # BenchmarkFunc 抽象基类
│       ├── __init__.py      # REGISTRY 注册表，统一导出
│       ├── deceptive_trap.py / multipeak.py / flat_region.py
│       ├── asymmetric.py / noisy.py / periodic_trap.py
│       ├── needle_in_haystack.py / cliff.py / double_well.py
│       ├── oscillating_decay.py / step.py / valley_ridge.py
├── results/                  # 实验输出
│   ├── summary_report.md    # 汇总对比表
│   ├── archive/             # 历史图片归档
│   └── <func_name>/         # 按函数分目录
│       ├── <func_name>_<ts>.md   # 单函数报告
│       └── plots/plot_<ts>.png    # 可视化图
├── reports/                  # 文档与汇报材料
│   ├── 思路.md
│   ├── 当前情况与架构.md
│   ├── 下一步安排.md
│   ├── agent_architecture.html
│   └── MN-BO组会报告.pptx
├── README.md
└── node_modules/            # npm 依赖
```

## 运行方式

```bash
# 交互式菜单（推荐）
D:\Miniconda3\envs\bo_env\python.exe src/main.py

# 指定函数
D:\Miniconda3\envs\bo_env\python.exe src/main.py cliff_func double_well_func

# 全部函数
D:\Miniconda3\envs\bo_env\python.exe src/main.py --all
```

## 实验设计

- 每个函数默认 **5 次重复**（seed 42-46），取均值±标准差
- 外层：6 维连续空间 `[0,1]^6`，拉丁超方采样初始化 12 个点，GP 搜索 M=8 次
- 内层 N=15 次标准 BO（EI 采集）
- 汇总报告含：基线 Gap、MN-BO Gap、Gap 缩减差值、Gap 缩减比

## 外层搜索空间（12D 连续参数，v2 带 gate）

| 维度 | 算子 | 参数范围 | 说明 |
|------|------|---------|------|
| p[0] | LogWarper | g ∈ [0,1] | 强度 gate，0=恒等 |
| p[1] | LogWarper | α ∈ [0.1, 10.0] | 对数压缩强度 |
| p[2] | StandardScaler | g ∈ [0,1] | 强度 gate |
| p[3] | StandardScaler | shift ∈ [-1σ, 1σ] | 均值偏移 |
| p[4] | StandardScaler | s ∈ [0.2, 5.0] | 方差缩放 |
| p[5] | PowerTransform | g ∈ [0,1] | 强度 gate |
| p[6] | PowerTransform | p ∈ [-1, 3] | 幂指数 |
| p[7] | SigmoidWarper | g ∈ [0,1] | 强度 gate |
| p[8] | SigmoidWarper | k ∈ [0.01, 10] | Sigmoid 陡度 |
| p[9] | SigmoidWarper | c ∈ [-5σ, 5σ] | Sigmoid 中心 |
| p[10] | MinMaxScaler | g ∈ [0,1] | 强度 gate |
| p[11] | RankTransform | g ∈ [0,1] | 离散 gate，>0.5 启用 |

## 版本控制

- **Git 已初始化**（2026-04-22），初始 commit `10f1605`，tag `v1.0-bugfix`
- `.gitignore` 排除：`results/`、`src/results/`、`__pycache__/`、`node_modules/`
- 惯例：每次实验前打 tag：`git -c user.email="lz@demo" -c user.name="LZ" tag -a v1.x-<描述> HEAD -m "..."`

## 已修复 Bug（2026-04-22）

| 文件 | 行号 | 问题 | 修复 |
|------|------|------|------|
| `src/main.py` | 189 | `range(N_INIT_META, m_outer)` = `range(36,20)` = 空循环，外层GP从未执行 | 改为 `range(m_outer)` |
## 变换算子（连续参数化版本 v2）



| 算子 | 公式 | 特点 |
|------|------|------|
| `LogWarper` | y' = sign(y)·log(1+α\|y\|) | g×α 双重控制，g=0 恒等 |
| `StandardScaler` | y' = (y-μ-shift·σ)/(σ·s) | g×shift×scale 联合控制 |
| `PowerTransform` | y' = sign(y)·\|y\|^p | g=0 恒等，p→1 恒等 |
| `SigmoidWarper` | y' = 1/(1+exp(-k(y-c))) | g=0 恒等，k→0 恒等 |
| `MinMaxScaler` | y' = (y-lo)/(hi-lo) | g=0 恒等 |
| `RankTransform` | y' = rank(y)/N | 离散，g>0.5 启用 |
