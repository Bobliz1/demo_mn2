# M×N 双层贝叶斯优化（MN-BO）

验证 MN-BO 方法在欺骗性函数上的优化效果：外层 GP 搜索最优目标空间变换配置，内层标准 BO 执行优化。

## 目录结构

```
demo_mn2/
├── .workbuddy/          # AI 工作记忆（自动生成，勿删）
├── src/                  # 源码
│   ├── main.py          # 实验入口（交互菜单 / 命令行）
│   ├── benchmark.py     # BO 工具函数 + ExperimentLogger
│   ├── bo_transform.py  # 变换算子（LogWarper / StandardScaler / IdentityOperator）
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
```

## 测试函数（12 个）

deceptive_trap / multipeak / flat_region / asymmetric / noisy /
periodic_trap / needle_in_haystack / cliff / double_well /
oscillating_decay / step / valley_ridge

## 核心参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| N_REPEATS | 5 | 每个函数独立运行次数 |
| M_OUTER | 5 | 外层迭代（搜索变换配置） |
| N_INNER | 15 | 内层迭代（标准 BO） |
| XI | 0.05 | EI 探索参数 |
