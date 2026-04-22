const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "LZ";
pres.title = "MN-BO: M×N 双层贝叶斯优化";

// ─── 色板：Charcoal Minimal 风格 ───
const C = {
  dark:    "2B2D42",   // 深蓝灰（标题背景）
  accent:  "8D99AE",   // 灰蓝（辅助色）
  orange:  "EF8354",   // 暖橙（强调色）
  white:   "FFFFFF",
  light:   "EDF2F4",   // 浅灰白（内容背景）
  text:    "2B2D42",   // 正文
  muted:   "6C757D",   // 次要文字
};

// ─── 通用工厂 ───
const makeShadow = () => ({
  type: "outer", blur: 6, offset: 2, angle: 135,
  color: "000000", opacity: 0.10,
});

// ============================================================
// Slide 1 — 封面
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.dark };

  // 左侧装饰条
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.12, h: 5.625,
    fill: { color: C.orange },
  });

  // 标题
  s.addText("MN-BO", {
    x: 0.8, y: 1.2, w: 8.5, h: 1.2,
    fontSize: 52, fontFace: "Arial Black",
    color: C.white, margin: 0,
  });
  s.addText("M\u00d7N \u53cc\u5c42\u8d1d\u53f6\u6570\u4f18\u5316\u6846\u67b6", {
    x: 0.8, y: 2.3, w: 8.5, h: 0.8,
    fontSize: 28, fontFace: "Microsoft YaHei",
    color: C.accent, margin: 0,
  });

  // 分隔线
  s.addShape(pres.shapes.LINE, {
    x: 0.8, y: 3.3, w: 3, h: 0,
    line: { color: C.orange, width: 3 },
  });

  // 信息
  s.addText("\u7ec4\u4f1a\u62a5\u544a  |  2026.04", {
    x: 0.8, y: 3.6, w: 8, h: 0.5,
    fontSize: 16, fontFace: "Microsoft YaHei",
    color: C.accent, margin: 0,
  });
  s.addText("LZ", {
    x: 0.8, y: 4.1, w: 8, h: 0.4,
    fontSize: 14, fontFace: "Microsoft YaHei",
    color: C.muted, margin: 0,
  });
}

// ============================================================
// Slide 2 — 目录
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("\u62a5\u544a\u63d0\u7eb2", {
    x: 0.7, y: 0.35, w: 8, h: 0.7,
    fontSize: 32, fontFace: "Microsoft YaHei",
    color: C.dark, bold: true, margin: 0,
  });

  // 左侧装饰条
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 0.35, w: 0.06, h: 0.7,
    fill: { color: C.orange },
  });

  const items = [
    ["01", "\u7814\u7a76\u80cc\u666f\u4e0e\u52a8\u673a"],
    ["02", "\u65b9\u6cd5\u6846\u67b6\uff1aM\u00d7N \u53cc\u5c42\u67b6\u6784"],
    ["03", "\u53d8\u6362\u7b97\u5b50\u4e0e\u5916\u5c42\u641c\u7d22\u7a7a\u95f4"],
    ["04", "\u57fa\u51c6\u6d4b\u8bd5\u51fd\u6570"],
    ["05", "\u5b9e\u9a8c\u8bbe\u8ba1\u4e0e\u8bc4\u4f30\u6307\u6807"],
    ["06", "\u5f53\u524d\u8fdb\u5c55\u4e0e\u4e0b\u4e00\u6b65\u8ba1\u5212"],
  ];

  items.forEach(([num, text], i) => {
    const y = 1.4 + i * 0.65;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 1.0, y, w: 0.55, h: 0.45,
      fill: { color: C.orange },
      shadow: makeShadow(),
    });
    s.addText(num, {
      x: 1.0, y, w: 0.55, h: 0.45,
      fontSize: 16, fontFace: "Arial Black",
      color: C.white, align: "center", valign: "middle",
      margin: 0,
    });
    s.addText(text, {
      x: 1.8, y, w: 7, h: 0.45,
      fontSize: 18, fontFace: "Microsoft YaHei",
      color: C.text, valign: "middle", margin: 0,
    });
  });
}

// ============================================================
// Slide 3 — 研究背景与动机
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("\u7814\u7a76\u80cc\u666f\u4e0e\u52a8\u673a", {
    x: 0.7, y: 0.35, w: 8, h: 0.6,
    fontSize: 30, fontFace: "Microsoft YaHei",
    color: C.dark, bold: true, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 0.35, w: 0.06, h: 0.6,
    fill: { color: C.orange },
  });

  // 左栏：BO 基本原理
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 4.2, h: 3.8,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addText("\u8d1d\u53f6\u4f18\u5316 (BO) \u57fa\u672c\u6d41\u7a0b", {
    x: 0.7, y: 1.4, w: 3.8, h: 0.45,
    fontSize: 16, fontFace: "Microsoft YaHei",
    color: C.orange, bold: true, margin: 0,
  });
  s.addText([
    { text: "1. \u7528\u5df2\u77e5\u6570\u636e\u8bad\u7ec3 GP \u4ee3\u7406\u6a21\u578b", options: { bullet: true, breakLine: true } },
    { text: "2. \u901a\u8fc7\u91c7\u96c6\u51fd\u6570\uff08\u5982 EI\uff09\u786e\u5b9a\u4e0b\u4e00\u4e2a\u91c7\u6837\u70b9", options: { bullet: true, breakLine: true } },
    { text: "3. \u91c7\u6837\u5e76\u66f4\u65b0\u6a21\u578b\uff0c\u5faa\u73af\u76f4\u81f3\u6536\u655b", options: { bullet: true, breakLine: true } },
  ], {
    x: 0.7, y: 2.0, w: 3.8, h: 1.5,
    fontSize: 13, fontFace: "Microsoft YaHei",
    color: C.text, lineSpacingMultiple: 1.6, margin: 0,
  });

  // 右栏：GP 的局限
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.3, y: 1.3, w: 4.2, h: 3.8,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addText("GP \u5efa\u6a21\u7684\u56f0\u96be\u573a\u666f", {
    x: 5.5, y: 1.4, w: 3.8, h: 0.45,
    fontSize: 16, fontFace: "Microsoft YaHei",
    color: C.orange, bold: true, margin: 0,
  });
  s.addText([
    { text: "\u6b3a\u9a97\u6027\u51fd\u6570\uff1a\u5c40\u90e8\u5cf0\u5f15\u5bfc GP \u8ff7\u5931\u65b9\u5411", options: { bullet: true, breakLine: true } },
    { text: "\u591a\u5cf0\u51fd\u6570\uff1aGP \u96be\u4ee5\u8986\u76d6\u6240\u6709\u5cf0\u503c", options: { bullet: true, breakLine: true } },
    { text: "\u68af\u5ea6\u60ac\u5d16\uff1a\u4e0d\u8fde\u7eed\u6027\u7834\u574f GP \u5e73\u6ed1\u5047\u8bbe", options: { bullet: true, breakLine: true } },
    { text: "\u9ad8\u566a\u58f0\uff1a\u4fe1\u54d9\u6bd4\u4f4e\uff0c\u6a21\u578b\u4e0d\u53ef\u9760", options: { bullet: true, breakLine: true } },
    { text: "\u2192 \u6838\u5fc3\u95ee\u9898\uff1a\u5982\u4f55\u8ba9 GP \u5728\u56f0\u96be\u573a\u666f\u4e0b\u66f4\u597d\u5730\u5de5\u4f5c\uff1f", options: { bold: true, breakLine: true } },
  ], {
    x: 5.5, y: 2.0, w: 3.8, h: 2.8,
    fontSize: 13, fontFace: "Microsoft YaHei",
    color: C.text, lineSpacingMultiple: 1.6, margin: 0,
  });
}

// ============================================================
// Slide 4 — 方法框架：M×N 双层架构
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("\u65b9\u6cd5\u6846\u67b6\uff1aM\u00d7N \u53cc\u5c42\u67b6\u6784", {
    x: 0.7, y: 0.35, w: 8, h: 0.6,
    fontSize: 30, fontFace: "Microsoft YaHei",
    color: C.dark, bold: true, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 0.35, w: 0.06, h: 0.6,
    fill: { color: C.orange },
  });

  // 核心思路
  s.addText("\u6838\u5fc3\u601d\u8def\uff1a\u5728\u4f18\u5316\u524d\u5bf9\u76ee\u6807\u51fd\u6570\u505a\u7a7a\u95f4\u53d8\u6362\uff0c\u8ba9 GP \u66f4\u5bb9\u6613\u5efa\u6a21", {
    x: 0.7, y: 1.15, w: 9, h: 0.4,
    fontSize: 15, fontFace: "Microsoft YaHei",
    color: C.muted, italic: true, margin: 0,
  });

  // 外层卡片
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.8, w: 4.2, h: 3.3,
    fill: { color: C.dark }, shadow: makeShadow(),
  });
  s.addText("\u5916\u5c42\uff1aM \u6b21\u8fed\u4ee3", {
    x: 0.7, y: 1.9, w: 3.8, h: 0.45,
    fontSize: 18, fontFace: "Microsoft YaHei",
    color: C.orange, bold: true, margin: 0,
  });
  s.addText("\u641c\u7d22\u6700\u4f18\u53d8\u6362\u914d\u7f6e", {
    x: 0.7, y: 2.35, w: 3.8, h: 0.35,
    fontSize: 13, fontFace: "Microsoft YaHei",
    color: C.accent, margin: 0,
  });
  s.addText([
    { text: "\u2022 \u8f93\u5165\uff1a\u53d8\u6362\u53c2\u6570\u914d\u7f6e", options: { breakLine: true } },
    { text: "\u2022 \u641c\u7d22\u65b9\u5f0f\uff1a\u5916\u5c42 GP + EI \u91c7\u96c6\u51fd\u6570", options: { breakLine: true } },
    { text: "\u2022 \u8f93\u51fa\uff1a\u5185\u5c42 BO \u7684 Gap\uff08\u4e0e\u6700\u4f18\u503c\u7684\u5dee\u8ddd\uff09", options: { breakLine: true } },
    { text: "\u2022 \u7ed3\u679c\uff1aGap \u6700\u5c0f\u7684\u53d8\u6362\u914d\u7f6e", options: { breakLine: true } },
  ], {
    x: 0.7, y: 2.85, w: 3.8, h: 2.0,
    fontSize: 12, fontFace: "Microsoft YaHei",
    color: C.white, lineSpacingMultiple: 1.8, margin: 0,
  });

  // 箭头
  s.addText("\u25B6", {
    x: 4.7, y: 3.0, w: 0.6, h: 0.6,
    fontSize: 28, color: C.orange, align: "center", valign: "middle",
    margin: 0,
  });

  // 内层卡片
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.3, y: 1.8, w: 4.2, h: 3.3,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addText("\u5185\u5c42\uff1aN \u6b21\u8fed\u4ee3", {
    x: 5.5, y: 1.9, w: 3.8, h: 0.45,
    fontSize: 18, fontFace: "Microsoft YaHei",
    color: C.orange, bold: true, margin: 0,
  });
  s.addText("\u5728\u53d8\u6362\u540e\u7a7a\u95f4\u6267\u884c\u6807\u51c6 BO", {
    x: 5.5, y: 2.35, w: 3.8, h: 0.35,
    fontSize: 13, fontFace: "Microsoft YaHei",
    color: C.muted, margin: 0,
  });
  s.addText([
    { text: "\u2022 \u5bf9\u76ee\u6807\u503c y \u5148\u505a\u53d8\u6362\uff08Log/\u6807\u51c6\u5316\uff09", options: { breakLine: true } },
    { text: "\u2022 GP \u5728\u53d8\u6362\u540e\u7a7a\u95f4\u5efa\u6a21\u66f4\u5e73\u6ed1", options: { breakLine: true } },
    { text: "\u2022 \u6807\u51c6 EI \u91c7\u96c6\u51fd\u6570\u5f15\u5bfc\u91c7\u6837", options: { breakLine: true } },
    { text: "\u2022 \u6700\u7ec8\u901a\u8fc7 inverse transform \u8fd4\u56de\u539f\u59cb\u7a7a\u95f4", options: { breakLine: true } },
  ], {
    x: 5.5, y: 2.85, w: 3.8, h: 2.0,
    fontSize: 12, fontFace: "Microsoft YaHei",
    color: C.text, lineSpacingMultiple: 1.8, margin: 0,
  });
}

// ============================================================
// Slide 5 — 变换算子与搜索空间
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("\u53d8\u6362\u7b97\u5b50\u4e0e\u641c\u7d22\u7a7a\u95f4", {
    x: 0.7, y: 0.35, w: 8, h: 0.6,
    fontSize: 30, fontFace: "Microsoft YaHei",
    color: C.dark, bold: true, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 0.35, w: 0.06, h: 0.6,
    fill: { color: C.orange },
  });

  // 左栏：算子说明
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 5.5, h: 3.8,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addText("\u5f53\u524d\u53d8\u6362\u7b97\u5b50\uff083 \u79cd\uff09", {
    x: 0.7, y: 1.4, w: 5.0, h: 0.45,
    fontSize: 16, fontFace: "Microsoft YaHei",
    color: C.orange, bold: true, margin: 0,
  });

  const ops = [
    ["IdentityOperator", "y' = y", "\u4e0d\u505a\u4efb\u4f55\u53d8\u6362\uff0c\u4f5c\u4e3a\u57fa\u7ebf"],
    ["LogWarper", "y' = sign(y)\u00b7log(1+|y|)", "\u538b\u7f29\u5927\u503c\u3001\u653e\u5927\u5c0f\u503c"],
    ["StandardScaler", "y' = (y\u2212\u03bc)/\u03c3", "\u6807\u51c6\u5316\u5230 0 \u5747\u503c 1 \u65b9\u5dee"],
  ];
  ops.forEach(([name, formula, desc], i) => {
    const y = 2.05 + i * 1.0;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.7, y, w: 0.08, h: 0.75,
      fill: { color: C.orange },
    });
    s.addText(name, {
      x: 1.0, y, w: 2.5, h: 0.35,
      fontSize: 13, fontFace: "Consolas",
      color: C.dark, bold: true, margin: 0,
    });
    s.addText(formula, {
      x: 1.0, y: y + 0.3, w: 4.5, h: 0.3,
      fontSize: 12, fontFace: "Consolas",
      color: C.muted, margin: 0,
    });
    s.addText(desc, {
      x: 3.7, y, w: 2.0, h: 0.75,
      fontSize: 11, fontFace: "Microsoft YaHei",
      color: C.text, valign: "middle", margin: 0,
    });
  });

  // 右栏：搜索空间
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.3, y: 1.3, w: 3.2, h: 3.8,
    fill: { color: C.dark }, shadow: makeShadow(),
  });
  s.addText("\u5916\u5c42\u641c\u7d22\u7a7a\u95f4", {
    x: 6.5, y: 1.4, w: 2.8, h: 0.45,
    fontSize: 16, fontFace: "Microsoft YaHei",
    color: C.orange, bold: true, margin: 0,
  });
  s.addText([
    { text: "\u53c2\u6570\u7a7a\u95f4 [0,1]\u00b2", options: { breakLine: true, bold: true } },
    { text: "", options: { breakLine: true, fontSize: 6 } },
    { text: "[0,0] \u2192 Identity", options: { breakLine: true } },
    { text: "[1,0] \u2192 Log only", options: { breakLine: true } },
    { text: "[0,1] \u2192 Scale only", options: { breakLine: true } },
    { text: "[1,1] \u2192 Log+Scale", options: { breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 6 } },
    { text: "\u5f53\u524d\u7b56\u7565\uff1a\u9884\u586b 4 \u4e2a\u89d2\u70b9\u7a77\u4e3e + GP \u5f15\u5bfc\u641c\u7d22", options: { breakLine: true, italic: true } },
  ], {
    x: 6.5, y: 2.0, w: 2.8, h: 2.8,
    fontSize: 11, fontFace: "Microsoft YaHei",
    color: C.white, lineSpacingMultiple: 1.6, margin: 0,
  });
}

// ============================================================
// Slide 6 — 基准测试函数
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("\u57fa\u51c6\u6d4b\u8bd5\u51fd\u6570\uff0812 \u4e2a\uff09", {
    x: 0.7, y: 0.35, w: 8, h: 0.6,
    fontSize: 30, fontFace: "Microsoft YaHei",
    color: C.dark, bold: true, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 0.35, w: 0.06, h: 0.6,
    fill: { color: C.orange },
  });

  const rows = [
    [
      { text: "\u51fd\u6570\u540d", options: { fill: { color: C.dark }, color: C.white, bold: true, fontSize: 10 } },
      { text: "\u6700\u5927\u503c", options: { fill: { color: C.dark }, color: C.white, bold: true, fontSize: 10 } },
      { text: "\u7279\u70b9", options: { fill: { color: C.dark }, color: C.white, bold: true, fontSize: 10 } },
    ],
    ["deceptive_trap", "4.90", "\u6b3a\u9a97\u6027\u9677\u9631"],
    ["multipeak", "5.00", "\u591a\u5cf0"],
    ["flat_region", "3.00", "\u5e73\u5766\u533a + \u5c16\u5cf0"],
    ["asymmetric", "10.00", "\u975e\u5bf9\u79f0"],
    ["noisy", "4.00", "\u9ad8\u566a\u58f0"],
    ["periodic_trap", "7.00", "\u5468\u671f\u80cc\u666f + \u9690\u85cf\u5c16\u5cf0"],
    ["needle_in_haystack", "10.00", "\u6781\u7a84\u5cf0 (\u03c3\u22480.01)"],
    ["cliff", "8.00", "\u68af\u5ea6\u60ac\u5d16"],
    ["double_well", "4.00", "\u53cc\u7b49\u9ad8\u5bf9\u79f0\u5cf0"],
    ["oscillating_decay", "3.50", "\u9ad8\u65af\u5305\u7edc\u00d7\u6b63\u5f26"],
    ["step", "5.00", "\u9636\u68af\u8df3\u53d8"],
    ["valley_ridge", "6.00", "V \u8c37 + \u5c71\u810a"],
  ];

  s.addTable(rows, {
    x: 0.5, y: 1.2, w: 9.0,
    border: { pt: 0.5, color: "DEE2E6" },
    colW: [2.8, 1.2, 5.0],
    fontSize: 11,
    fontFace: "Microsoft YaHei",
    color: C.text,
    rowH: [0.35, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32],
    autoPage: false,
  });

  // 说明
  s.addText("\u8bbe\u8ba1\u539f\u5219\uff1a\u8986\u76d6 GP \u5efa\u6a21\u7684\u5404\u7c7b\u56f0\u96be\u573a\u666f\uff0c\u9a8c\u8bc1\u53d8\u6362\u7b97\u5b50\u7684\u666e\u9002\u6027", {
    x: 0.5, y: 5.2, w: 9, h: 0.35,
    fontSize: 12, fontFace: "Microsoft YaHei",
    color: C.muted, italic: true, margin: 0,
  });
}

// ============================================================
// Slide 7 — 实验设计与评估
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("\u5b9e\u9a8c\u8bbe\u8ba1\u4e0e\u8bc4\u4f30\u6307\u6807", {
    x: 0.7, y: 0.35, w: 8, h: 0.6,
    fontSize: 30, fontFace: "Microsoft YaHei",
    color: C.dark, bold: true, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 0.35, w: 0.06, h: 0.6,
    fill: { color: C.orange },
  });

  // 左栏：实验参数
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 4.2, h: 3.3,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addText("\u5b9e\u9a8c\u53c2\u6570", {
    x: 0.7, y: 1.4, w: 3.8, h: 0.45,
    fontSize: 16, fontFace: "Microsoft YaHei",
    color: C.orange, bold: true, margin: 0,
  });

  const params = [
    ["\u91cd\u590d\u6b21\u6570", "5 \u6b21\uff08seed 42\u201346\uff09"],
    ["\u5916\u5c42\u8fed\u4ee3 M", "5\uff084 \u89d2\u70b9 + 1 \u6b21 GP \u641c\u7d22\uff09"],
    ["\u5185\u5c42\u8fed\u4ee3 N", "15"],
    ["\u63a2\u7d22\u53c2\u6570 xi", "0.05"],
    ["GP \u5185\u6838", "RBF \u00d7 ConstantKernel"],
  ];
  params.forEach(([k, v], i) => {
    const y = 2.05 + i * 0.48;
    s.addText(k, {
      x: 0.7, y, w: 2.0, h: 0.38,
      fontSize: 12, fontFace: "Microsoft YaHei",
      color: C.text, margin: 0,
    });
    s.addText(v, {
      x: 2.8, y, w: 1.8, h: 0.38,
      fontSize: 12, fontFace: "Microsoft YaHei",
      color: C.dark, bold: true, margin: 0,
    });
  });

  // 右栏：评估指标
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.3, y: 1.3, w: 4.2, h: 3.3,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addText("\u8bc4\u4f30\u6307\u6807", {
    x: 5.5, y: 1.4, w: 3.8, h: 0.45,
    fontSize: 16, fontFace: "Microsoft YaHei",
    color: C.orange, bold: true, margin: 0,
  });
  s.addText([
    { text: "Gap = \u7406\u8bba\u6700\u5927\u503c \u2212 \u641c\u7d22\u5230\u7684\u6700\u5927\u503c", options: { breakLine: true, bold: true } },
    { text: "", options: { breakLine: true, fontSize: 6 } },
    { text: "\u57fa\u7ebf Gap\uff1a\u6807\u51c6 BO\uff08\u65e0\u53d8\u6362\uff09\u7684 Gap", options: { breakLine: true } },
    { text: "MN-BO Gap\uff1a\u53cc\u5c42\u65b9\u6cd5\u7684 Gap", options: { breakLine: true } },
    { text: "", options: { breakLine: true, fontSize: 6 } },
    { text: "Gap \u7f29\u51cf\u5dee\u503c = \u57fa\u7ebf Gap \u2212 MN-BO Gap", options: { breakLine: true } },
    { text: "Gap \u7f29\u51cf\u6bd4 = \u7f29\u51cf\u5dee\u503c / \u57fa\u7ebf Gap", options: { breakLine: true } },
  ], {
    x: 5.5, y: 2.0, w: 3.8, h: 2.4,
    fontSize: 12, fontFace: "Microsoft YaHei",
    color: C.text, lineSpacingMultiple: 1.5, margin: 0,
  });
}

// ============================================================
// Slide 8 — 代码架构
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("\u4ee3\u7801\u67b6\u6784", {
    x: 0.7, y: 0.35, w: 8, h: 0.6,
    fontSize: 30, fontFace: "Microsoft YaHei",
    color: C.dark, bold: true, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 0.35, w: 0.06, h: 0.6,
    fill: { color: C.orange },
  });

  // 文件树
  const treeLines = [
    "demo_mn/",
    "\u251c\u2500\u2500 main.py          \u2190 \u5b9e\u9a8c\u5165\u53e3\uff08\u5916\u5c42\u641c\u7d22 + \u5185\u5c42 BO\uff09",
    "\u251c\u2500\u2500 bo_transform.py   \u2190 \u53d8\u6362\u7b97\u5b50\u5b9a\u4e49",
    "\u251c\u2500\u2500 benchmark.py      \u2190 \u91c7\u96c6\u51fd\u6570\u3001\u65e5\u5fd7\u8bb0\u5f55",
    "\u251c\u2500\u2500 functions/        \u2190 12 \u4e2a\u57fa\u51c6\u51fd\u6570\uff08\u72ec\u7acb\u6587\u4ef6\uff09",
    "\u2502   \u251c\u2500\u2500 _base.py       \u2190 BenchmarkFunc \u62bd\u8c61\u57fa\u7c7b",
    "\u2502   \u251c\u2500\u2500 __init__.py    \u2190 REGISTRY \u6ce8\u518c\u8868",
    "\u2502   \u2514\u2500\u2500 *.py           \u2190 \u5404\u51fd\u6570\u5b9e\u73b0",
    "\u2514\u2500\u2500 results/          \u2190 \u5b9e\u9a8c\u8f93\u51fa\uff08md + \u56fe\u7247\uff09",
  ];

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.2, w: 5.5, h: 4.0,
    fill: { color: "1E1E1E" }, shadow: makeShadow(),
  });
  treeLines.forEach((line, i) => {
    s.addText(line, {
      x: 0.8, y: 1.35 + i * 0.42, w: 5.0, h: 0.35,
      fontSize: 11, fontFace: "Consolas",
      color: "D4D4D4", margin: 0,
    });
  });

  // 右侧说明
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.3, y: 1.2, w: 3.2, h: 4.0,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addText("\u5173\u952e\u6a21\u5757\u804c\u8d23", {
    x: 6.5, y: 1.3, w: 2.8, h: 0.45,
    fontSize: 16, fontFace: "Microsoft YaHei",
    color: C.orange, bold: true, margin: 0,
  });
  s.addText([
    { text: "main.py", options: { bold: true, breakLine: true } },
    { text: "\u5916\u5c42 GP \u641c\u7d22\u53d8\u6362 + \u5185\u5c42 BO \u5faa\u73af\uff0c\u7ed3\u679c\u6c47\u603b", options: { breakLine: true, fontSize: 11 } },
    { text: "", options: { breakLine: true, fontSize: 4 } },
    { text: "bo_transform.py", options: { bold: true, breakLine: true } },
    { text: "Log / Scale / Identity \u7b97\u5b50\u53ca Pipeline", options: { breakLine: true, fontSize: 11 } },
    { text: "", options: { breakLine: true, fontSize: 4 } },
    { text: "functions/", options: { bold: true, breakLine: true } },
    { text: "\u6bcf\u4e2a\u51fd\u6570\u72ec\u7acb\u6587\u4ef6\uff0c\u901a\u8fc7 REGISTRY \u6ce8\u518c", options: { breakLine: true, fontSize: 11 } },
    { text: "", options: { breakLine: true, fontSize: 4 } },
    { text: "benchmark.py", options: { bold: true, breakLine: true } },
    { text: "EI \u91c7\u96c6\u51fd\u6570\u3001GP \u91c7\u6837\u3001\u5b9e\u9a8c\u65e5\u5fd7", options: { breakLine: true, fontSize: 11 } },
  ], {
    x: 6.5, y: 1.9, w: 2.8, h: 3.0,
    fontSize: 12, fontFace: "Microsoft YaHei",
    color: C.text, lineSpacingMultiple: 1.1, margin: 0,
  });
}

// ============================================================
// Slide 9 — 当前进展与下一步
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("\u5f53\u524d\u8fdb\u5c55\u4e0e\u4e0b\u4e00\u6b65\u8ba1\u5212", {
    x: 0.7, y: 0.35, w: 8, h: 0.6,
    fontSize: 30, fontFace: "Microsoft YaHei",
    color: C.dark, bold: true, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 0.35, w: 0.06, h: 0.6,
    fill: { color: C.orange },
  });

  // 已完成
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 4.2, h: 3.8,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.3, w: 4.2, h: 0.55,
    fill: { color: C.accent },
  });
  s.addText("\u2705 \u5df2\u5b8c\u6210", {
    x: 0.7, y: 1.3, w: 3.8, h: 0.55,
    fontSize: 16, fontFace: "Microsoft YaHei",
    color: C.white, bold: true, valign: "middle", margin: 0,
  });
  s.addText([
    { text: "\u2022 M\u00d7N \u53cc\u5c42\u67b6\u6784\u5b9e\u73b0\uff08\u5916\u5c42 GP + \u5185\u5c42 BO\uff09", options: { breakLine: true } },
    { text: "\u2022 3 \u79cd\u53d8\u6362\u7b97\u5b50\uff08Identity / Log / Scale\uff09", options: { breakLine: true } },
    { text: "\u2022 12 \u4e2a 1D \u57fa\u51c6\u6d4b\u8bd5\u51fd\u6570", options: { breakLine: true } },
    { text: "\u2022 \u57fa\u7ebf BO vs MN-BO \u5bf9\u6bd4\u5b9e\u9a8c", options: { breakLine: true } },
    { text: "\u2022 5 \u6b21\u91cd\u590d + \u5747\u503c\u00b1\u6807\u51c6\u5dee\u7edf\u8ba1", options: { breakLine: true } },
    { text: "\u2022 \u81ea\u52a8\u751f\u6210\u5b9e\u9a8c\u62a5\u544a\u548c\u6c47\u603b\u8868", options: { breakLine: true } },
  ], {
    x: 0.7, y: 2.05, w: 3.8, h: 2.8,
    fontSize: 12, fontFace: "Microsoft YaHei",
    color: C.text, lineSpacingMultiple: 1.6, margin: 0,
  });

  // 下一步
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.3, y: 1.3, w: 4.2, h: 3.8,
    fill: { color: C.white }, shadow: makeShadow(),
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.3, y: 1.3, w: 4.2, h: 0.55,
    fill: { color: C.orange },
  });
  s.addText("\U0001F680 \u4e0b\u4e00\u6b65\u8ba1\u5212", {
    x: 5.5, y: 1.3, w: 3.8, h: 0.55,
    fontSize: 16, fontFace: "Microsoft YaHei",
    color: C.white, bold: true, valign: "middle", margin: 0,
  });
  s.addText([
    { text: "\u2022 \u53d8\u6362\u7b97\u5b50\u589e\u52a0\u8fde\u7eed\u53c2\u6570", options: { breakLine: true } },
    { text: "  (\u538b\u7f29\u5f3a\u5ea6\u3001\u5e42\u6b21\u7b49\uff0c\u4e0d\u518d\u53ea\u662f\u5f00/\u5173)", options: { breakLine: true, color: C.muted } },
    { text: "\u2022 \u53bb\u6389 round \u79bb\u6563\u5316\uff0c\u8ba9\u5916\u5c42\u771f\u6b63\u505a\u8fde\u7eed\u4f18\u5316", options: { breakLine: true } },
    { text: "\u2022 \u65b0\u589e\u53d8\u6362\u7b97\u5b50\uff08Power\u3001Sigmoid \u7b49\uff09", options: { breakLine: true } },
    { text: "\u2022 \u6269\u5c55\u5230\u591a\u7ef4\u51fd\u6570 (2D/3D)", options: { breakLine: true } },
    { text: "\u2022 \u4e0e\u5176\u4ed6 BO \u65b9\u6cd5\u505a\u5bf9\u6bd4\u57fa\u51c6", options: { breakLine: true } },
  ], {
    x: 5.5, y: 2.05, w: 3.8, h: 2.8,
    fontSize: 12, fontFace: "Microsoft YaHei",
    color: C.text, lineSpacingMultiple: 1.6, margin: 0,
  });
}

// ============================================================
// Slide 10 — 结束页
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.dark };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.12, h: 5.625,
    fill: { color: C.orange },
  });

  s.addText("\u8c22\u8c22", {
    x: 0, y: 1.8, w: 10, h: 1.2,
    fontSize: 48, fontFace: "Microsoft YaHei",
    color: C.white, align: "center", margin: 0,
  });
  s.addShape(pres.shapes.LINE, {
    x: 4.0, y: 3.2, w: 2, h: 0,
    line: { color: C.orange, width: 2 },
  });
  s.addText("Q & A", {
    x: 0, y: 3.5, w: 10, h: 0.6,
    fontSize: 20, fontFace: "Microsoft YaHei",
    color: C.accent, align: "center", margin: 0,
  });
}

// ─── 输出 ───
const outPath = "d:\\2602-stu\\paper\\demo_mn\\MN-BO\u7ec4\u4f1a\u62a5\u544a.pptx";
pres.writeFile({ fileName: outPath }).then(() => {
  console.log("PPT generated: " + outPath);
}).catch(err => {
  console.error("Error:", err);
  process.exit(1);
});
