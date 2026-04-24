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

# 全部函数
python src/main.py --all

# 快速验证（单函数，最小参数，约 2-5 分钟）
# R=1（1次重复），M=5（外层迭代），N=8（内层步数），I=8（外层初始点）
python src/main.py cliff_func -R 1 -M 5 -N 8 -I 8

# 完整实验（全部 12 个函数，稳定算子模式）
python src/main.py --all -R 1 -M 5 -N 8 -I 8
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

| 参数 | 默认值 | 说明 |
|------|--------|------|
| N_REPEATS | 5 | 每个函数独立运行次数（seed 42-46） |
| N_INIT_META | 36 | 外层初始拉丁超方采样点数（4D 空间建议 8~12） |
| M_OUTER | 20 | 外层迭代次数（4D 空间建议 5~10） |
| N_INNER | 12 | 内层迭代次数（标准 BO） |
| XI | 0.05 | EI 探索参数 |

### 计算量估算（默认参数，单 seed）
- 全局初始化：5 次（一次性，所有内层 BO 共享）
- 基线 BO：12 次
- 外层初始 36 点：36 × 12 = 432 次
- 外层搜索 20 次：20 × 12 = 240 次
- **单次实验总计：5 + 12 + 432 + 240 = 689 次函数评估**

### 快速实验参数（稳定算子模式，4D 空间）
使用 `-R 1 -M 5 -N 8 -I 8`：
- 全局初始化：5 次
- 基线 BO：8 次
- 外层初始 8 点：8 × 8 = 64 次
- 外层搜索 5 次：5 × 8 = 40 次
- **单次实验总计：5 + 8 + 64 + 40 = 117 次函数评估**
- **12 个函数全跑：12 × 117 = 1,404 次评估**
