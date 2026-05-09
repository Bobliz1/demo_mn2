# MN-BO 实验框架（滚雪球多视角搜索）

## 记号说明

| 记号 | 含义 |
|------|------|
| $f(x)$ | 目标函数（黑箱） |
| $\mathcal{D}$ | 全局数据池，存储所有已评估的 $(x, f(x))$ 对 |
| $T(p)$ | 由参数 $p \in [0,1]^4$ 决定的 y 值变换算子（StandardScaler / MinMaxScaler 的混合） |
| $I$ | 预填充阶段的外层初始点数 |
| $M$ | 元GP驱动的外层迭代次数 |
| $N$ | 每轮内层 BO 的采样步数 |
| $\mathcal{M}$ | 外层元GP，在4维参数空间中建模"变换参数 → 搜索质量"的关系 |

---

## 核心流程

**初始化**：随机采样 5 个点，构成初始数据池 $\mathcal{D}_0$。

**预填充阶段**（共 $I$ 轮）：

用拉丁超方在 $[0,1]^4$ 中生成 $I$ 个变换参数 $\{p_1, \ldots, p_I\}$，逐一执行：

$$\mathcal{D}_i = \mathcal{D}_{i-1} \cup \text{InnerBO}\bigl(T(p_i),\ \mathcal{D}_{i-1},\ N\text{ steps}\bigr)$$

每轮内层 BO 以**当前完整池 $\mathcal{D}_{i-1}$ 为先验**，在变换 $T(p_i)$ 的视角下跑 $N$ 步，新采样点追加入池。将 $(p_i, \max f)$ 记录给元GP $\mathcal{M}$。

**元GP驱动阶段**（共 $M$ 轮）：

$$p_{I+m} = \arg\max_{p} \text{EI}_{\mathcal{M}}(p), \quad m = 1, \ldots, M$$

$$\mathcal{D}_{I+m} = \mathcal{D}_{I+m-1} \cup \text{InnerBO}\bigl(T(p_{I+m}),\ \mathcal{D}_{I+m-1},\ N\text{ steps}\bigr)$$

元GP根据历史观测智能选取下一个变换参数，内层BO同样继承完整历史池。

**输出**：

$$x^* = \arg\max_{x \in \mathcal{D}_{I+M}} f(x)$$

**总评估预算**：$(I + M) \times N$，基线标准 BO 获得同等预算进行对比。

---

## 默认参数

| 参数 | 默认值 |
|------|--------|
| $I$ | 8 |
| $M$ | 10 |
| $N$ | 10 |
| 总预算 | 180 次函数评估 |
