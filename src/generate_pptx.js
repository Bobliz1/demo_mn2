/**
 * MN-BO 组会报告 PPTX 生成脚本
 * 基于 2026-04-22 最新架构（连续参数化 v2，12D 空间，6 个算子）
 *
 * 配色方案：Ocean Gradient（深蓝学术风格）
 *   主色: 1A3A5C (深海蓝)
 *   辅色: 2D6A8F (海洋蓝)
 *   强调: 4ECDC4 (青绿色)
 *   浅色: F0F7FF (冰蓝)
 *   深文字: 1E293B
 *   浅文字: FFFFFF
 */

const pptxgen = require("pptxgenjs");

// ============================================================
// 配色常量
// ============================================================
const C = {
  primary:   "1A3A5C",  // 深海蓝（标题、背景）
  secondary: "2D6A8F",  // 海洋蓝（副标题、分隔）
  accent:    "4ECDC4",  // 青绿色（强调色）
  light:     "F0F7FF",  // 冰蓝（内容页背景）
  dark:      "1E293B",  // 深文字
  white:     "FFFFFF",
  mid:       "94A3B8",  // 中灰（辅助文字）
  highlight: "F59E0B",  // 琥珀色（高亮）
  cardBg:    "E8F4FD",  // 卡片背景
  cardBg2:   "D1FAE5",  // 卡片背景2（绿色系）
};

// ============================================================
// 工厂函数（避免对象复用导致 PPTX 损坏）
// ============================================================
const mkShadow = () => ({
  type: "outer",
  color: "000000",
  blur: 8,
  offset: 3,
  angle: 135,
  opacity: 0.10,
});

const mkCardShadow = () => ({
  type: "outer",
  color: "000000",
  blur: 6,
  offset: 2,
  angle: 135,
  opacity: 0.08,
});

// ============================================================
// 辅助函数
// ============================================================

/** 添加页码（右下角） */
function addPageNum(slide, n, total) {
  slide.addText(`${n} / ${total}`, {
    x: 8.5, y: 5.2, w: 1.2, h: 0.3,
    fontSize: 10, color: C.mid, align: "right",
  });
}

/** 添加页眉标题栏 */
function addHeader(slide, title, subtitle) {
  // 深色背景条
  slide.addShape("rect", {
    x: 0, y: 0, w: 10, h: 1.05,
    fill: { color: C.primary },
  });
  // 强调线
  slide.addShape("rect", {
    x: 0, y: 1.05, w: 10, h: 0.04,
    fill: { color: C.accent },
  });
  // 标题
  slide.addText(title, {
    x: 0.4, y: 0.12, w: 8, h: 0.55,
    fontSize: 26, fontFace: "Arial", bold: true,
    color: C.white, margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.4, y: 0.65, w: 8, h: 0.32,
      fontSize: 13, fontFace: "Arial",
      color: C.accent, margin: 0,
    });
  }
}

/** 深色背景页面（封面/谢谢） */
function makeDarkSlide(pres, title, subtitle, note) {
  const slide = pres.addSlide();
  slide.background = { color: C.primary };

  // 装饰圆（右上角）
  slide.addShape("ellipse", {
    x: 7.5, y: -1.5, w: 4, h: 4,
    fill: { color: C.secondary, transparency: 60 },
  });
  slide.addShape("ellipse", {
    x: 8.5, y: 3.5, w: 2.5, h: 2.5,
    fill: { color: C.accent, transparency: 75 },
  });

  // 主标题
  slide.addText(title, {
    x: 0.6, y: 1.6, w: 8.8, h: 1.2,
    fontSize: 42, fontFace: "Arial", bold: true,
    color: C.white, align: "left", margin: 0,
  });
  // 副标题
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.6, y: 2.85, w: 8.8, h: 0.6,
      fontSize: 18, fontFace: "Arial",
      color: C.accent, align: "left", margin: 0,
    });
  }
  // 备注
  if (note) {
    slide.addText(note, {
      x: 0.6, y: 4.5, w: 8.8, h: 0.4,
      fontSize: 12, fontFace: "Arial",
      color: C.mid, align: "left", margin: 0,
    });
  }
  return slide;
}

// ============================================================
// 创建演示文稿
// ============================================================
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "LZ";
pres.title = "M×N 双层贝叶斯优化 — 组会报告 2026-04-22";
pres.subject = "MN-BO Architecture v2";

// ============================================================
// 第1页：封面
// ============================================================
{
  const slide = makeDarkSlide(
    pres,
    "M×N 双层贝叶斯优化",
    "MN-BO: Meta-Normalization Bayesian Optimization",
    "组会报告 | 2026-04-22 | 架构版本 v2（连续参数化）"
  );

  // 版本标签
  slide.addShape("rect", {
    x: 0.6, y: 3.6, w: 2.2, h: 0.45,
    fill: { color: C.accent },
  });
  slide.addText("v2 连续参数化", {
    x: 0.6, y: 3.6, w: 2.2, h: 0.45,
    fontSize: 13, bold: true, color: C.primary,
    align: "center", valign: "middle", margin: 0,
  });

  // 关键特性标签
  const tags = ["6 个变换算子", "12D 连续搜索空间", "Gate 机制", "Latin Hypercube 初始化"];
  tags.forEach((t, i) => {
    slide.addShape("rect", {
      x: 0.6 + i * 2.1, y: 4.2, w: 2.0, h: 0.36,
      fill: { color: C.secondary, transparency: 40 },
      line: { color: C.accent, width: 1 },
    });
    slide.addText(t, {
      x: 0.6 + i * 2.1, y: 4.2, w: 2.0, h: 0.36,
      fontSize: 11, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
  });
}

// ============================================================
// 第2页：问题背景
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.light };
  addHeader(slide, "问题背景", "为什么需要目标空间变换？");
  addPageNum(slide, 2, 10);

  // 左侧：问题描述
  slide.addShape("rect", {
    x: 0.4, y: 1.25, w: 4.4, h: 2.2,
    fill: { color: C.white }, shadow: mkCardShadow(),
  });
  slide.addShape("rect", {
    x: 0.4, y: 1.25, w: 0.07, h: 2.2,
    fill: { color: "EF4444" },  // 红色强调
  });
  slide.addText("GP 建模的困难", {
    x: 0.65, y: 1.32, w: 4, h: 0.38,
    fontSize: 15, bold: true, color: C.dark, margin: 0,
  });
  slide.addText([
    { text: "目标值分布不均匀：", options: { bold: true, breakLine: true } },
    { text: "  · 少数极端值主导协方差估计", options: { breakLine: true } },
    { text: "  · 采集函数被极端值绑架", options: { breakLine: true } },
    { text: "  · 预测时在密集区波动过大", options: { breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "欺骗性函数陷阱：", options: { bold: true, breakLine: true } },
    { text: "  · GP 误判全局最优点位置", options: { breakLine: true } },
    { text: "  · 收敛到局部最优", options: {} },
  ], {
    x: 0.65, y: 1.75, w: 4.0, h: 1.6,
    fontSize: 12, color: C.dark, valign: "top", margin: 0,
  });

  // 右侧：解决思路
  slide.addShape("rect", {
    x: 5.1, y: 1.25, w: 4.5, h: 2.2,
    fill: { color: C.white }, shadow: mkCardShadow(),
  });
  slide.addShape("rect", {
    x: 5.1, y: 1.25, w: 0.07, h: 2.2,
    fill: { color: C.accent },
  });
  slide.addText("核心思路", {
    x: 5.35, y: 1.32, w: 4, h: 0.38,
    fontSize: 15, bold: true, color: C.dark, margin: 0,
  });
  slide.addText([
    { text: "在目标空间引入可学习的", options: { breakLine: true } },
    { text: "变换算子（Transformation）", options: { bold: true, breakLine: true } },
    { text: "", options: { breakLine: true } },
    { text: "将目标值 y 映射为 y'：", options: { breakLine: true } },
    { text: "  · 压缩极端值", options: { breakLine: true } },
    { text: "  · 平衡值域分布", options: { breakLine: true } },
    { text: '  \u00b7 \u8ba9 GP \u770b\u5230\u66f4\u300c\u597d\u300d\u66f2\u9762', options: {} },
  ], {
    x: 5.35, y: 1.75, w: 4.1, h: 1.6,
    fontSize: 12, color: C.dark, valign: "top", margin: 0,
  });

  // 底部示例
  slide.addText("示例：对数变换   y' = sign(y) · log(1 + α|y|)", {
    x: 0.4, y: 3.6, w: 9.2, h: 0.35,
    fontSize: 12, color: C.secondary, italic: true, margin: 0,
  });
  slide.addText("α 大 → 强压缩 | α→0 → 恒等（无变换）", {
    x: 0.4, y: 3.95, w: 9.2, h: 0.3,
    fontSize: 11, color: C.mid, margin: 0,
  });

  // 数学示意（手绘风格框）
  const eqs = [
    { y: "y", yp: "y'", note: "α=0.1（弱）" },
    { y: "y", yp: "y'", note: "α=1.0（经典）" },
    { y: "y", yp: "y'", note: "α=10（强）" },
  ];
  eqs.forEach((eq, i) => {
    const x = 1.5 + i * 2.8;
    slide.addShape("rect", {
      x, y: 4.35, w: 2.4, h: 0.95,
      fill: { color: i === 2 ? C.primary : C.cardBg },
      shadow: mkCardShadow(),
    });
    slide.addText(eq.note, {
      x, y: 4.38, w: 2.4, h: 0.3,
      fontSize: 10, bold: true,
      color: i === 2 ? C.white : C.secondary,
      align: "center", margin: 0,
    });
    slide.addText(`y' = log(1+${eq.note.split("=")[1].replace("（", "(").replace("）", ")")}y)`, {
      x, y: 4.7, w: 2.4, h: 0.55,
      fontSize: 12,
      color: i === 2 ? C.accent : C.primary,
      align: "center", valign: "middle", margin: 0,
    });
  });
}

// ============================================================
// 第3页：双层BO架构
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.light };
  addHeader(slide, "核心架构", "M×N 双层贝叶斯优化");
  addPageNum(slide, 3, 10);

  // ---- 外层卡片 ----
  slide.addShape("rect", {
    x: 0.5, y: 1.25, w: 9.0, h: 1.5,
    fill: { color: C.primary }, shadow: mkShadow(),
  });
  slide.addText("外层 Meta-Level（M 次）", {
    x: 0.7, y: 1.3, w: 4, h: 0.38,
    fontSize: 14, bold: true, color: C.accent, margin: 0,
  });
  slide.addText([
    { text: "GP 在 [0,1]¹² 连续空间中搜索最优变换配置", options: { breakLine: true } },
    { text: "Latin Hypercube 初始化 36 个点 + GP-EI 迭代 20 次 = 56 次外层评估", options: { breakLine: true } },
    { text: "目标：最小化 Gap（理论最大值 − 找到的最大值）", options: {} },
  ], {
    x: 0.7, y: 1.7, w: 8.6, h: 0.9,
    fontSize: 12, color: C.white, valign: "top", margin: 0,
  });

  // 箭头
  slide.addShape("rect", {
    x: 4.7, y: 2.75, w: 0.08, h: 0.35,
    fill: { color: C.accent },
  });
  slide.addText("▼", {
    x: 4.55, y: 2.7, w: 0.4, h: 0.4,
    fontSize: 16, color: C.accent, align: "center", margin: 0,
  });

  // ---- 内层卡片 ----
  slide.addShape("rect", {
    x: 0.5, y: 3.1, w: 9.0, h: 1.5,
    fill: { color: C.white }, shadow: mkShadow(),
  });
  slide.addShape("rect", {
    x: 0.5, y: 3.1, w: 0.07, h: 1.5,
    fill: { color: C.accent },
  });
  slide.addText("内层 Standard BO（N 次）", {
    x: 0.75, y: 3.15, w: 4, h: 0.38,
    fontSize: 14, bold: true, color: C.primary, margin: 0,
  });
  slide.addText([
    { text: "输入：x ∈ [0,1]¹（1D 基准函数）→ 原始目标值 y = f(x)", options: { breakLine: true } },
    { text: "变换：y' = Pipeline(y) → GP + EI 在变换空间搜索", options: { breakLine: true } },
    { text: "输出：该变换配置下的最优值 y*_trans", options: {} },
  ], {
    x: 0.75, y: 3.55, w: 8.6, h: 0.9,
    fontSize: 12, color: C.dark, valign: "top", margin: 0,
  });

  // 流水线示意
  const ops = ["LogWarper", "StandardScaler", "PowerTransform", "SigmoidWarper", "MinMax", "Rank"];
  ops.forEach((op, i) => {
    slide.addShape("rect", {
      x: 0.7 + i * 1.45, y: 4.75, w: 1.3, h: 0.5,
      fill: { color: C.secondary },
    });
    slide.addText(op, {
      x: 0.7 + i * 1.45, y: 4.75, w: 1.3, h: 0.5,
      fontSize: 9, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    if (i < ops.length - 1) {
      slide.addText("→", {
        x: 0.7 + i * 1.45 + 1.3, y: 4.75, w: 0.15, h: 0.5,
        fontSize: 14, color: C.accent, align: "center", valign: "middle", margin: 0,
      });
    }
  });
  slide.addText("（gate=0 的算子自动跳过，等价于恒等）", {
    x: 0.7, y: 5.28, w: 8.6, h: 0.28,
    fontSize: 10, color: C.mid, italic: true, margin: 0,
  });
}

// ============================================================
// 第4页：外层GP搜索
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.light };
  addHeader(slide, "外层搜索", "GP 在 12D 连续空间中的探索过程");
  addPageNum(slide, 4, 10);

  // 步骤流
  const steps = [
    { n: "1", title: "初始化", desc: "Latin Hypercube 采样\n36 个点覆盖 12D 空间" },
    { n: "2", title: "评估", desc: "每个点跑内层 BO\n获取最优值 y*" },
    { n: "3", title: "拟合", desc: "GP 拟合\np → y* 曲面" },
    { n: "4", title: "采集", desc: "EI 推荐\n下一个候选点" },
    { n: "5", title: "迭代", desc: "重复步骤 2-4\n共 M=20 次" },
  ];
  steps.forEach((s, i) => {
    const x = 0.35 + i * 1.92;
    // 圆形编号
    slide.addShape("ellipse", {
      x: x + 0.7, y: 1.28, w: 0.42, h: 0.42,
      fill: { color: C.accent },
    });
    slide.addText(s.n, {
      x: x + 0.7, y: 1.28, w: 0.42, h: 0.42,
      fontSize: 15, bold: true, color: C.primary,
      align: "center", valign: "middle", margin: 0,
    });
    // 卡片
    slide.addShape("rect", {
      x, y: 1.8, w: 1.82, h: 1.35,
      fill: { color: C.white }, shadow: mkCardShadow(),
    });
    slide.addText(s.title, {
      x, y: 1.85, w: 1.82, h: 0.35,
      fontSize: 13, bold: true, color: C.primary,
      align: "center", margin: 0,
    });
    slide.addText(s.desc, {
      x: x + 0.08, y: 2.22, w: 1.66, h: 0.88,
      fontSize: 10, color: C.dark,
      align: "center", valign: "top", margin: 0,
    });
    // 连接箭头
    if (i < steps.length - 1) {
      slide.addText("→", {
        x: x + 1.82, y: 2.25, w: 0.1, h: 0.5,
        fontSize: 16, color: C.accent, align: "center", valign: "middle", margin: 0,
      });
    }
  });

  // 底部说明
  slide.addShape("rect", {
    x: 0.4, y: 3.35, w: 9.2, h: 1.85,
    fill: { color: C.cardBg },
  });
  slide.addText("外层 vs 内层：对偶优化结构", {
    x: 0.6, y: 3.42, w: 4, h: 0.35,
    fontSize: 13, bold: true, color: C.primary, margin: 0,
  });
  const compRows = [
    ["", "外层 Meta-Level", "内层 Standard BO"],
    ["搜索目标", "最优变换配置 p*", "给定变换下的 x*"],
    ["搜索空间", "[0,1]¹²（连续）", "[0,1]¹（原始函数）"],
    ["目标函数", "黑盒：内层 BO 最优值", "f(x) 经过变换后的值"],
    ["采样策略", "GP + EI", "GP + EI"],
  ];
  const tableData = compRows.map((row, ri) =>
    row.map((cell, ci) => ({
      text: cell,
      options: {
        bold: ri === 0 || ci === 0,
        fill: { color: ri === 0 ? C.primary : (ci === 0 ? C.cardBg : C.white) },
        color: ri === 0 ? C.white : (ci === 0 ? C.primary : C.dark),
        align: ci === 0 ? "center" : "center",
        fontSize: 11,
      },
    }))
  );
  slide.addTable(tableData, {
    x: 0.6, y: 3.8, w: 8.8, h: 1.3,
    border: { pt: 0.5, color: "CBD5E1" },
    colW: [1.5, 3.65, 3.65],
  });
}

// ============================================================
// 第5页：6个变换算子
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.light };
  addHeader(slide, "6 个变换算子", "每个算子由 gate(强度) + 形态参数共同控制");
  addPageNum(slide, 5, 10);

  const ops = [
    {
      name: "LogWarper",
      formula: "y' = sign(y)·log(1+α|y|)",
      gate: "g ∈ [0,1]  →  0=恒等",
      param: "α ∈ [0.1, 10.0]",
      effect: "压缩正值，α 越大压缩越强",
      color: "3B82F6",
    },
    {
      name: "StandardScaler",
      formula: "y' = (y-μ-shift·σ)/(σ·s)",
      gate: "g ∈ [0,1]  →  0=恒等",
      param: "shift ∈ [-1σ,1σ]  s ∈ [0.2,5.0]",
      effect: "均值偏移 + 方差缩放",
      color: "8B5CF6",
    },
    {
      name: "PowerTransform",
      formula: "y' = sign(y)·|y|^p",
      gate: "g ∈ [0,1]  →  0=恒等",
      param: "p ∈ [-1, 3]  →  p=1 恒等",
      effect: "p<1 压缩大值，p>1 拉伸大值",
      color: "EC4899",
    },
    {
      name: "SigmoidWarper",
      formula: "y' = 1/(1+exp(-k(y-c)))",
      gate: "g ∈ [0,1]  →  0=恒等",
      param: "k ∈ [0.01, 10]  c ∈ [-5σ, 5σ]",
      effect: "k→0 恒等，k 大趋向阶跃",
      color: "F59E0B",
    },
    {
      name: "MinMaxScaler",
      formula: "y' = (y-lo)/(hi-lo)·t",
      gate: "g ∈ [0,1]  →  0=恒等",
      param: "目标上界 t",
      effect: "线性映射到 [0, t]",
      color: "10B981",
    },
    {
      name: "RankTransform",
      formula: "y' = rank(y)/(N-1)",
      gate: "离散 gate  →  g>0.5 启用",
      param: "无形态参数",
      effect: "完全消除异常值，非连续可微",
      color: "6366F1",
    },
  ];

  ops.forEach((op, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.4 + col * 3.1;
    const y = 1.22 + row * 2.05;

    // 卡片背景
    slide.addShape("rect", {
      x, y, w: 2.95, h: 1.9,
      fill: { color: C.white }, shadow: mkCardShadow(),
    });
    // 顶部色条
    slide.addShape("rect", {
      x, y, w: 2.95, h: 0.06,
      fill: { color: op.color },
    });
    // 算子名
    slide.addText(op.name, {
      x: x + 0.1, y: y + 0.1, w: 2.75, h: 0.3,
      fontSize: 13, bold: true, color: op.color, margin: 0,
    });
    // 公式
    slide.addText(op.formula, {
      x: x + 0.1, y: y + 0.42, w: 2.75, h: 0.28,
      fontSize: 9, color: C.secondary, italic: true, margin: 0,
    });
    // 分隔线
    slide.addShape("rect", {
      x: x + 0.1, y: y + 0.72, w: 2.75, h: 0.015,
      fill: { color: "E2E8F0" },
    });
    // gate
    slide.addText(op.gate, {
      x: x + 0.1, y: y + 0.78, w: 2.75, h: 0.25,
      fontSize: 9, bold: true, color: C.dark, margin: 0,
    });
    // 形态参数
    slide.addText(op.param, {
      x: x + 0.1, y: y + 1.02, w: 2.75, h: 0.25,
      fontSize: 9, color: C.mid, margin: 0,
    });
    // 效果
    slide.addText(op.effect, {
      x: x + 0.1, y: y + 1.28, w: 2.75, h: 0.55,
      fontSize: 9, color: C.secondary, margin: 0,
    });
  });
}

// ============================================================
// 第6页：连续参数化详解
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.light };
  addHeader(slide, "连续参数化详解", "12D 搜索空间如何映射到物理算子");
  addPageNum(slide, 6, 10);

  // 左侧维度分配表
  slide.addText("12 维空间分配", {
    x: 0.4, y: 1.22, w: 4.5, h: 0.35,
    fontSize: 13, bold: true, color: C.primary, margin: 0,
  });

  const dimRows = [
    ["维度", "算子", "参数", "范围"],
    ["p[0]",  "LogWarper",       "强度 g",     "∈ [0,1]"],
    ["p[1]",  "LogWarper",       "α",          "∈ [0.1, 10.0]"],
    ["p[2]",  "StandardScaler",  "强度 g",     "∈ [0,1]"],
    ["p[3]",  "StandardScaler",  "shift",      "∈ [-1σ, 1σ]"],
    ["p[4]",  "StandardScaler",  "s",          "∈ [0.2, 5.0]"],
    ["p[5]",  "PowerTransform",  "强度 g",     "∈ [0,1]"],
    ["p[6]",  "PowerTransform",  "power p",   "∈ [-1, 3]"],
    ["p[7]",  "SigmoidWarper",   "强度 g",     "∈ [0,1]"],
    ["p[8]",  "SigmoidWarper",   "陡度 k",    "∈ [0.01, 10]"],
    ["p[9]",  "SigmoidWarper",   "中心 c",    "∈ [-5σ, 5σ]"],
    ["p[10]", "MinMaxScaler",    "强度 g",     "∈ [0,1]"],
    ["p[11]", "RankTransform",   "离散 gate",  "∈ [0,1]"],
  ];
  const dimTable = dimRows.map((row, ri) =>
    row.map((cell, ci) => ({
      text: cell,
      options: {
        bold: ri === 0 || ci === 0,
        fill: {
          color: ri === 0 ? C.primary
            : ri % 2 === 0 ? "F1F5F9" : C.white,
        },
        color: ri === 0 ? C.white
          : (ci === 0 ? C.secondary : C.dark),
        fontSize: 9,
        align: ci === 0 ? "center" : "left",
      },
    }))
  );
  slide.addTable(dimTable, {
    x: 0.4, y: 1.6, w: 4.4, h: 3.6,
    border: { pt: 0.4, color: "CBD5E1" },
    colW: [0.7, 1.6, 0.9, 1.2],
  });

  // 右侧：映射示例
  slide.addText("GP 看到的 vs 实际效果", {
    x: 5.1, y: 1.22, w: 4.5, h: 0.35,
    fontSize: 13, bold: true, color: C.primary, margin: 0,
  });

  // 示例框
  slide.addShape("rect", {
    x: 5.1, y: 1.6, w: 4.5, h: 3.6,
    fill: { color: C.white }, shadow: mkCardShadow(),
  });
  slide.addText("以 p = [0.7, 0.5, 0, 0, 1, 0, 1, 0, 0.1, 0, 0, 0] 为例", {
    x: 5.25, y: 1.68, w: 4.2, h: 0.3,
    fontSize: 10, bold: true, color: C.secondary, margin: 0,
  });
  slide.addShape("rect", {
    x: 5.25, y: 2.02, w: 4.1, h: 0.015,
    fill: { color: "E2E8F0" },
  });

  const examples = [
    { dim: "p[0]=0.7", meaning: "LogWarper 强度 70%" },
    { dim: "p[1]=0.5", meaning: "α = 0.1 + 0.5×9.9 = 5.05（强压缩）" },
    { dim: "p[4]=1.0", meaning: "StandardScaler scale = 5.0（强方差压缩）" },
    { dim: "p[6]=1.0", meaning: "PowerTransform p = 3（拉伸大值）" },
    { dim: "p[11]=0", meaning: "RankTransform 未启用" },
  ];
  examples.forEach((ex, i) => {
    slide.addShape("rect", {
      x: 5.25, y: 2.12 + i * 0.54, w: 1.3, h: 0.42,
      fill: { color: C.cardBg },
    });
    slide.addText(ex.dim, {
      x: 5.25, y: 2.12 + i * 0.54, w: 1.3, h: 0.42,
      fontSize: 9, bold: true, color: C.secondary,
      align: "center", valign: "middle", margin: 0,
    });
    slide.addText(ex.meaning, {
      x: 6.65, y: 2.12 + i * 0.54, w: 2.75, h: 0.42,
      fontSize: 9, color: C.dark,
      valign: "middle", margin: 0,
    });
  });

  slide.addText("GP 独立探索每个维度，自动发现最优组合", {
    x: 5.25, y: 4.92, w: 4.2, h: 0.25,
    fontSize: 10, italic: true, color: C.accent, margin: 0,
  });
}

// ============================================================
// 第7页：实验配置
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.light };
  addHeader(slide, "实验配置", "M / N 参数设置建议");
  addPageNum(slide, 7, 10);

  // 两列对比
  const configs = [
    {
      title: "方案 A：均衡型（默认）",
      color: C.secondary,
      bg: "EFF6FF",
      rows: [
        ["外层迭代 M", "20"],
        ["拉丁超方初始点", "36"],
        ["总外层评估数", "56"],
        ["内层步数 N", "12"],
        ["重复次数 R", "5"],
      ],
    },
    {
      title: "方案 B：外层探索型",
      color: C.accent,
      bg: "ECFDF5",
      rows: [
        ["外层迭代 M", "30"],
        ["拉丁超方初始点", "30"],
        ["总外层评估数", "60"],
        ["内层步数 N", "10"],
        ["重复次数 R", "5"],
      ],
    },
  ];

  configs.forEach((cfg, i) => {
    const x = 0.4 + i * 4.8;
    slide.addShape("rect", {
      x, y: 1.25, w: 4.5, h: 2.6,
      fill: { color: cfg.bg }, shadow: mkCardShadow(),
    });
    slide.addShape("rect", {
      x, y: 1.25, w: 4.5, h: 0.06,
      fill: { color: cfg.color },
    });
    slide.addText(cfg.title, {
      x: x + 0.2, y: 1.35, w: 4.1, h: 0.38,
      fontSize: 13, bold: true, color: C.primary, margin: 0,
    });

    cfg.rows.forEach(([k, v], ri) => {
      slide.addText(k, {
        x: x + 0.2, y: 1.78 + ri * 0.38, w: 2.5, h: 0.35,
        fontSize: 12, color: C.dark, margin: 0,
      });
      slide.addText(v, {
        x: x + 2.7, y: 1.78 + ri * 0.38, w: 1.6, h: 0.35,
        fontSize: 12, bold: true, color: cfg.color,
        align: "right", margin: 0,
      });
    });
  });

  // 命令行示例
  slide.addShape("rect", {
    x: 0.4, y: 4.05, w: 9.2, h: 1.3,
    fill: { color: "1E293B" },
  });
  slide.addText("命令行使用示例", {
    x: 0.6, y: 4.12, w: 4, h: 0.3,
    fontSize: 11, bold: true, color: C.accent, margin: 0,
  });
  const cmds = [
    "# 默认参数",
    "python src/main.py --all",
    "",
    "# 自定义 M/N",
    "python src/main.py --all -M 30 -N 10 -R 3",
  ];
  slide.addText(cmds.join("\n"), {
    x: 0.6, y: 4.42, w: 8.8, h: 0.88,
    fontSize: 10, fontFace: "Consolas",
    color: C.white, margin: 0,
  });
}

// ============================================================
// 第8页：近期成果
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.light };
  addHeader(slide, "近期成果", "v2 架构升级已完成");
  addPageNum(slide, 8, 10);

  const achievements = [
    {
      icon: "✓",
      title: "连续参数化 v2",
      desc: "6 个算子全部支持连续参数，搜索空间从 4 种组合扩展为 [0,1]¹² 连续空间",
      tag: "已完成",
      tagColor: "10B981",
    },
    {
      icon: "✓",
      title: "Gate 机制",
      desc: "每个算子独立 gate 参数，GP 自动决定「用多少」和「用什么形态」",
      tag: "已完成",
      tagColor: "10B981",
    },
    {
      icon: "✓",
      title: "Latin Hypercube 初始化",
      desc: "36 个均匀分布初始点，替代旧版 4 角点，更高效覆盖 12D 空间",
      tag: "已完成",
      tagColor: "10B981",
    },
    {
      icon: "✓",
      title: "新增 3 个算子",
      desc: "PowerTransform / SigmoidWarper / MinMaxScaler / RankTransform",
      tag: "已完成",
      tagColor: "10B981",
    },
    {
      icon: "~",
      title: "全函数批量实验",
      desc: "12 个欺骗性函数有待完整跑通（部分完成）",
      tag: "进行中",
      tagColor: C.highlight,
    },
    {
      icon: "~",
      title: "收敛曲线可视化",
      desc: "需要新增「采样次数 vs 最优值」曲线图",
      tag: "进行中",
      tagColor: C.highlight,
    },
  ];

  achievements.forEach((a, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.4 + col * 4.75;
    const y = 1.25 + row * 1.4;

    slide.addShape("rect", {
      x, y, w: 4.5, h: 1.25,
      fill: { color: C.white }, shadow: mkCardShadow(),
    });
    slide.addShape("ellipse", {
      x: x + 0.15, y: y + 0.12, w: 0.38, h: 0.38,
      fill: { color: a.tagColor },
    });
    slide.addText(a.icon, {
      x: x + 0.15, y: y + 0.12, w: 0.38, h: 0.38,
      fontSize: 14, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0,
    });
    slide.addText(a.title, {
      x: x + 0.65, y: y + 0.12, w: 2.8, h: 0.35,
      fontSize: 13, bold: true, color: C.primary, margin: 0,
    });
    slide.addShape("rect", {
      x: x + 3.55, y: y + 0.15, w: 0.8, h: 0.28,
      fill: { color: a.tagColor, transparency: 20 },
    });
    slide.addText(a.tag, {
      x: x + 3.55, y: y + 0.15, w: 0.8, h: 0.28,
      fontSize: 9, bold: true, color: a.tagColor,
      align: "center", valign: "middle", margin: 0,
    });
    slide.addText(a.desc, {
      x: x + 0.65, y: y + 0.52, w: 3.7, h: 0.68,
      fontSize: 10, color: C.dark, valign: "top", margin: 0,
    });
  });
}

// ============================================================
// 第9页：下一步计划
// ============================================================
{
  const slide = pres.addSlide();
  slide.background = { color: C.light };
  addHeader(slide, "下一步计划", "四个方向 · 按优先级推进");
  addPageNum(slide, 9, 10);

  const plans = [
    {
      priority: "⭐⭐⭐",
      title: "可视化增强",
      color: "3B82F6",
      items: [
        "新增收敛曲线（采样次数 vs 最优值）",
        "多函数对比热力图（Gap 缩减比）",
        "最佳变换配置分布统计",
      ],
    },
    {
      priority: "⭐⭐",
      title: "实验完整性",
      color: "8B5CF6",
      items: [
        "跑完全部 12 个欺骗性函数",
        "按 Gap 缩减比排序，标注「有效/无效」",
        "分析 MN-BO 失败的案例（局限性）",
      ],
    },
    {
      priority: "⭐⭐",
      title: "算子扩充",
      color: "EC4899",
      items: [
        "探索算子流水线顺序的优化",
        "添加自适应算子选择机制",
        "EI / UCB / PI 采集函数对比",
      ],
    },
    {
      priority: "⭐",
      title: "理论扩展",
      color: "F59E0B",
      items: [
        "2D / 3D 函数扩展",
        "消融实验（固定算子 vs 自适应）",
        "GP 在不同目标分布下的建模误差分析",
      ],
    },
  ];

  plans.forEach((p, i) => {
    const x = 0.35 + (i % 2) * 4.8;
    const y = 1.22 + Math.floor(i / 2) * 2.1;

    slide.addShape("rect", {
      x, y, w: 4.5, h: 1.95,
      fill: { color: C.white }, shadow: mkCardShadow(),
    });
    slide.addShape("rect", {
      x, y, w: 0.06, h: 1.95,
      fill: { color: p.color },
    });
    slide.addText(p.priority, {
      x: x + 0.2, y: y + 0.1, w: 1.2, h: 0.3,
      fontSize: 11, color: p.color, bold: true, margin: 0,
    });
    slide.addText(p.title, {
      x: x + 1.4, y: y + 0.1, w: 2.9, h: 0.3,
      fontSize: 14, bold: true, color: C.primary, margin: 0,
    });
    p.items.forEach((item, ri) => {
      slide.addText(`· ${item}`, {
        x: x + 0.2, y: y + 0.48 + ri * 0.38, w: 4.1, h: 0.35,
        fontSize: 10, color: C.dark, margin: 0,
      });
    });
  });
}

// ============================================================
// 第10页：谢谢
// ============================================================
{
  makeDarkSlide(
    pres,
    "谢谢",
    "欢迎提问与讨论",
    "MN-BO v2 | 2026-04-22"
  );
  addPageNum(pres.slides[pres.slides.length - 1], 10, 10);
}

// ============================================================
// 输出文件
// ============================================================
const path = require("path");
const outPath = path.join(__dirname, "..", "reports", "MN-BO组会报告_v2.pptx");
pres.writeFile({ fileName: outPath })
  .then(() => console.log("PPT 生成成功: " + outPath))
  .catch(err => {
    console.error("生成失败:", err);
    process.exit(1);
  });
