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
| `multipeak_func` | **5.7323** | 多峰函数（4高斯叠加） |
| `flat_region_func` | 3.0 | 平坦区域+尖峰 |
| `asymmetric_func` | **8.6597** | 非对称函数 |
| `noisy_func` | 4.0 | 高噪声函数（信号峰值2.65） |
| `periodic_trap_func` | **6.8413** | 高频周期背景 + 隐藏全局尖峰 |
| `needle_in_haystack_func` | 10.0 | 极窄峰（σ≈0.01）被平坦区包围 |
| `cliff_func` | **8.1979** | x=1 处梯度悬崖，GP 难建模 |
| `double_well_func` | 4.0 | 两个等高对称全局峰 |
| `oscillating_decay_func` | 3.5 | 高斯包络×正弦振荡 |
| `step_func` | **5.1** | 阶梯跳变，破坏 GP 平滑性假设 |
| `valley_ridge_func` | **6.1267** | V 谷 + 远端山脊 |

> **注**：粗体值为 2026-04-25 数值扫描修正后的精确最大值（20万点网格+局部精扫）。原值因未考虑叠加峰/ripple/噪声等因素而偏低或偏高。

## 项目文件结构（重构后，2026-04-21）

```
demo_mn2/
├── .workbuddy/              # AI 工作记忆（勿删）
├── src/                      # 源码
│   ├── main.py              # 实验入口（交互菜单 / 命令行）
│   ├── benchmark.py         # BO 工具函数 + ExperimentLogger（无函数定义）
│   ├── bo_transform.py      # 变换算子（【稳定模式】4D 外层空间：StandardScaler + MinMaxScaler）
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

# 快速验证（单函数，最小参数，约 2-5 分钟）
# R=1（1次重复），M=5（外层迭代），N=8（内层步数），I=8（外层初始点）
D:\Miniconda3\envs\bo_env\python.exe src/main.py cliff_func -R 1 -M 5 -N 8 -I 8
```

## 实验设计（2026-04-25 更新：默认参数已下调）

> **重要**：`src/main.py` 硬编码默认值已从完整实验级别下调为轻量级别。直接运行（不加参数）将使用轻量默认值。

### 默认参数（代码硬编码，轻量级）
- 每个函数 **5 次重复**（seed 42-46），取均值±标准差
- 外层：4 维连续空间 `[0,1]^4`，拉丁超方采样初始化 **8** 个点，GP 搜索 **M=5** 次
- 内层：n_init=5 个初始点 + **N=8** 次 BO 迭代（EI 采集）
- **计算量估算（单 seed）**：5 + 8 + 8×8 + 5×8 = **117 次函数评估**
- **12 函数全跑（R=5）**：12 × 117 × 5 = **7,020 次评估**

### 快速验证模式（显式指定 `-R 1`）
```bash
python src/main.py --all -R 1 -M 5 -N 8 -I 8
```
- 参数与默认模式相同，仅重复 1 次
- **12 函数全跑**：12 × 117 = **1,404 次评估**

### 完整实验模式（需显式指定旧默认参数）
```bash
python src/main.py --all -R 5 -M 20 -N 12 -I 36
```
- 外层：4 维连续空间 `[0,1]^4`，拉丁超方采样初始化 **36** 个点，GP 搜索 **M=20** 次
- 内层：n_init=5 + **N=12** 次 BO 迭代
- **计算量估算（单 seed）**：5 + 12 + 36×12 + 20×12 = **689 次函数评估**
- **12 函数全跑（R=5）**：12 × 689 × 5 = **41,340 次评估**

## 外层搜索空间（稳定算子模式，4D 连续参数）

| 维度 | 算子 | 参数范围 | 说明 |
|------|------|---------|------|
| p[0] | StandardScaler | g ∈ [0,1] | 强度 gate |
| p[1] | StandardScaler | shift ∈ [-1σ, 1σ] | 均值偏移 |
| p[2] | StandardScaler | s ∈ [0.2, 5.0] | 方差缩放 |
| p[3] | MinMaxScaler | g ∈ [0,1] | 强度 gate |

### 待处理算子（已注释，待架构重构后恢复）
以下算子因 backward() 数值稳定性问题已禁用：
- **LogWarper**：`backward()` 含 `exp()`，大值溢出
- **PowerTransform**：`backward()` 含 `power(1/p)`，p→0 时爆炸
- **SigmoidWarper**：`backward()` 含 `log(y/(1-y))`，边界敏感
- **RankTransform**：离散非连续，GP 难建模

## 版本控制

- **Git 已初始化**（2026-04-22），初始 commit `10f1605`，tag `v1.0-bugfix`
- Tag `v1.1-defaults`（2026-04-25）：默认参数下调为轻量级（M=5, N=8, I=8）
- Tag `v1.2-docs-sync`（2026-04-25）：6函数最大值修正 + `--seed` 参数 + N/A格式化 + 文档同步
- `.gitignore` 排除：`results/`、`src/results/`、`__pycache__/`、`node_modules/`、`.workbuddy/`
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
