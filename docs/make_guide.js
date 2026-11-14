const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, LevelFormat, AlignmentType, Footer, PageNumber,
} = require("docx");

const FONT = "Microsoft YaHei";
const MONO = "Consolas";
const W = 9026; // A4 text width in DXA (1" margins)

const r = (t, o = {}) => new TextRun({ text: t, font: FONT, ...o });
const P = (...runs) => new Paragraph({ children: runs.map(x => typeof x === "string" ? r(x) : x), spacing: { after: 120, line: 320 } });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [r(t)] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [r(t)] });
const B = (...runs) => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: runs.map(x => typeof x === "string" ? r(x) : x), spacing: { after: 80, line: 300 } });
const N = (ref, ...runs) => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs.map(x => typeof x === "string" ? r(x) : x), spacing: { after: 80, line: 300 } });
const bold = t => r(t, { bold: true });
const code = t => new TextRun({ text: t, font: MONO, size: 20, color: "8A1F11" });

// grey code box: one paragraph per line
function CODE(lines) {
  return lines.map((l, i) => new Paragraph({
    children: [new TextRun({ text: l || " ", font: MONO, size: 19 })],
    shading: { type: ShadingType.CLEAR, color: "auto", fill: "F2F2F2" },
    spacing: { before: i === 0 ? 60 : 0, after: i === lines.length - 1 ? 160 : 0 },
    indent: { left: 200, right: 200 },
  }));
}

// coloured callout box
function BOX(title, lines, fill = "EAF3FB", edge = "2E75B6") {
  const border = { style: BorderStyle.SINGLE, size: 12, color: edge };
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: [W],
    rows: [new TableRow({ children: [new TableCell({
      width: { size: W, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: "auto", fill },
      borders: { top: border, bottom: border, left: border, right: border },
      margins: { top: 120, bottom: 120, left: 180, right: 180 },
      children: [new Paragraph({ children: [r(title, { bold: true, color: edge })], spacing: { after: 80 } }),
        ...lines.map(l => new Paragraph({ children: (Array.isArray(l) ? l : [l]).map(x => typeof x === "string" ? r(x) : x), spacing: { after: 60, line: 300 } }))],
    })] })],
  });
}

function TABLE(head, rows, widths) {
  const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const cell = (t, i, isHead) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, borders,
    shading: { type: ShadingType.CLEAR, color: "auto", fill: isHead ? "2E75B6" : "FFFFFF" },
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    children: [new Paragraph({ children: [r(t, { size: 18, bold: isHead, color: isHead ? "FFFFFF" : "000000" })] })],
  });
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: head.map((t, i) => cell(t, i, true)) }),
      ...rows.map(row => new TableRow({ children: row.map((t, i) => cell(t, i, false)) }))],
  });
}
const gap = () => new Paragraph({ children: [], spacing: { after: 120 } });

const steps = ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"];

const body = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [r("噜咪助手 · AI 助手快速上手")] }),
  P(r("装一个 AI 助手，剩下的设置让它自己做。价格是 2026 年 11 月的，买之前看一眼官网。", { color: "595959", size: 20 })),

  H1("1. 选哪个"),
  BOX("推荐：Claude Code + MiniMax（约 49 元/月）", [
    "· 能看游戏截图（脚本卡住时要靠这个）",
    "· 国内手机号注册，人民币付款，不用翻墙",
    "· 自动读取噜咪助手里的规则，不用你提醒",
  ], "EEF7EA", "548235"),
  gap(),
  P(bold("只想先免费试试："), "装 TRAE CN（trae.cn，抖音登录，有按钮的软件，不用敲命令），打开噜咪助手文件夹，第一句话说“先读 CLAUDE.md，按里面的规则做”，然后直接看第 3 步。"),

  H1("2. 安装（只做一次，约 15 分钟）"),
  N("s1", bold("装两个软件"), "，一路点“下一步”：Node.js（nodejs.org，选 LTS）和 Git（git-scm.com）。"),
  N("s1", bold("打开噜咪助手文件夹"), "，点地址栏，输入 ", code("powershell"), " 回车，会出现一个黑色窗口。"),
  N("s1", bold("在黑色窗口里粘贴这两行"), "，每行按回车："),
  ...CODE(["npm config set registry https://registry.npmmirror.com", "npm install -g @anthropic-ai/claude-code"]),
  N("s1", bold("买 MiniMax 套餐"), "：platform.minimaxi.com 手机号注册，买最低档，在控制台创建 API Key 复制下来（", r("这是你的付款密码，别发群里", { color: "C00000" }), "）。"),
  N("s1", bold("装 CC Switch"), "（免费小工具），在里面选 MiniMax，粘贴 API Key，保存。"),
  N("s1", bold("启动"), "：在黑色窗口输入 ", code("claude"), " 回车。"),

  H1("3. 第一句话：让它把剩下的都装好"),
  P("复制这段发给它："),
  ...CODE([
    "帮我把噜咪助手设置好：",
    "1. 照 MiniMax 官方文档装好看图工具（understand_image）；",
    "2. 没有 Python 就装一个，建 .venv，装 requirements.txt；",
    "3. 找到我电脑上 MuMu 的 adb 和设备名，写进 local.env；",
    "4. 截一张图，告诉我游戏现在在哪个界面。",
  ]),
  P("它每一步都会问你“可以运行吗”，点允许就行。最后它能说对游戏界面，就全部好了。"),

  H1("4. 平时就说这些"),
  B(bold("跑日常："), "“跑一下日常，卡住了就看截图帮我修。”"),
  B(bold("我的阵容不一样："), "“我的天梯阵容是 ……，打法是 ……，帮我改好，先打 3 场试试。”"),
  B(bold("我的生产不一样："), "“我想生产 ……，不生产 ……，帮我改好并测试。”"),
  B(bold("发回给大家："), "“打包我的修改。”然后把生成的 zip 发到公会群，说一句改了什么。"),

  H1("5. 三条规矩"),
  B("绝不让它花钱：任何带 ¥ 的按钮都不能点。体力只在你说的时候花。"),
  B("看不懂它要做什么，就问“这一步是做什么的？”再允许。"),
  B("做完一件事输入 ", code("/clear"), " 开新对话，省额度。"),
];
const doc = new Document({
  creator: "lumi-zhushou",
  title: "噜咪助手 AI 助手快速上手",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { font: FONT, size: 40, bold: true, color: "1F3864" }, paragraph: { spacing: { before: 0, after: 160 }, keepNext: true } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: "2E75B6" }, paragraph: { spacing: { before: 320, after: 140 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 25, bold: true, color: "1F3864" }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    ...steps.map(ref => ({ reference: ref, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] })),
  ] },
  sections: [{
    properties: { page: { margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [r("噜咪助手 · 第 ", { size: 18, color: "7F7F7F" }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "7F7F7F", font: FONT }), r(" 页", { size: 18, color: "7F7F7F" })] })] }) },
    children: body,
  }],
});

Packer.toBuffer(doc).then(b => { fs.writeFileSync("AI助手快速上手.docx", b); console.log("written", b.length); });
