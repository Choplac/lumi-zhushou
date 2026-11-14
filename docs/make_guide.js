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
  new Paragraph({ heading: HeadingLevel.TITLE, children: [r("噜咪助手 · AI 编程助手使用指南")] }),
  P(r("给不会写代码的公会伙伴：怎么装一个 AI 编程助手，让它帮你用、帮你改噜咪助手。", { color: "595959" })),
  P(r("价格和免费额度是 2026 年 11 月整理的，变化很快，购买前请以官网为准。", { color: "C00000", size: 20 })),

  H1("1. 这是什么，为什么要用"),
  P("噜咪助手是一个在电脑上帮你做游戏日常的脚本。脚本会遇到没见过的画面（新活动、新弹窗），这时需要有人看一眼截图，教它认识新画面。"),
  P("“AI 编程助手”就是这个人。它能读写电脑上的文件、运行命令、看截图。你只要用平常的话告诉它要做什么，例如“脚本卡住了，帮我看看”。"),
  BOX("你需要做的只有三件事", [
    "1. 用中文说清楚你想要什么。",
    "2. AI 要运行命令时，看一眼再点“允许”。",
    "3. 在游戏里看结果对不对，告诉它。",
  ]),
  gap(),

  H1("2. 先认识几个词"),
  B(bold("终端（命令行）"), "：一个黑色窗口，用打字代替鼠标点击来运行程序。Windows 里叫 PowerShell。"),
  B(bold("CLI 工具"), "：在终端里运行的 AI 助手，例如 Claude Code、CodeBuddy Code。打字聊天，它直接改文件。"),
  B(bold("IDE 工具"), "：带窗口和按钮的写代码软件，里面也有 AI 聊天框，例如 TRAE。对新手更友好。"),
  B(bold("模型"), "：AI 背后的“大脑”，例如 MiniMax M3、GLM、Kimi、豆包。同一个工具可以换不同的模型。"),
  B(bold("套餐 / Coding Plan"), "：按月付费，换来每 5 小时、每周、每月一定的使用次数。"),
  B(bold("能看图"), "：模型能不能读截图。噜咪助手需要看游戏截图，所以这一点很重要。"),

  H1("3. 选哪个？"),
  TABLE(["工具", "公司", "形式", "登录", "价格（2026-11）", "适合谁"], [
    ["TRAE CN", "字节跳动", "IDE（窗口软件）", "抖音 / 头条", "基础功能免费，有每日/每周次数限制", "完全不想碰命令行的人"],
    ["CodeBuddy Code", "腾讯", "CLI", "微信扫码", "免费每月约 500 积分；付费 99 元/月起", "想免费试试命令行"],
    ["Qoder CLI", "阿里（原通义灵码）", "CLI", "官网注册", "新用户 2 周 Pro 试用 + 300 积分；59 元/月起", "想免费试两周"],
    ["Claude Code + MiniMax", "Anthropic 工具 + MiniMax 模型", "CLI", "手机号注册 MiniMax", "Go 档约 49 元/月", "推荐：长期用，能看截图"],
    ["Claude Code + 火山方舟", "Anthropic 工具 + 豆包模型", "CLI", "火山引擎账号", "Lite 约 40 元/月（常有首月 9.9 元）", "最便宜；看图能力要先测"],
  ], [1500, 1350, 1150, 1150, 2200, 1676]),
  gap(),
  BOX("推荐", [
    [bold("先免费试："), "不会命令行就用 TRAE CN；愿意试命令行就用 CodeBuddy Code（微信扫码就能登录）。"],
    [bold("长期用、便宜、谁都能买："), "Claude Code + MiniMax Go 档（约 49 元/月）。理由："],
    "· Claude Code 会自动读取噜咪助手里的规则文件 CLAUDE.md，不用你每次提醒；",
    "· MiniMax 官方提供看图工具（understand_image），可以读游戏截图；",
    "· 国内手机号注册，人民币付款，不需要境外网络和境外信用卡。",
    [bold("注意："), "Claude 自己的模型和账号在国内用不了，这里只用 Claude Code 这个“壳”，模型换成国产的。"],
  ], "EEF7EA", "548235"),
  gap(),
  P(r("其他也可以：Kimi Code（月之暗面）、小米 MiMo Code（限时免费）、阿里百炼套餐等。iFlow CLI 已在 2026 年 4 月停止服务，不要再装。", { size: 20, color: "595959" })),

  H1("4. 准备工作（Windows，只做一次）"),
  N("s1", bold("装 Python"), "：到 python.org 下载 3.10 以上版本。安装时一定勾选 “Add Python to PATH”。"),
  N("s1", bold("装 Node.js"), "（CLI 工具需要）：到 nodejs.org 或 npmmirror.com 下载 LTS 版，一路“下一步”。"),
  N("s1", bold("装 Git for Windows"), "：到 git-scm.com 或国内镜像下载，一路“下一步”。有些工具（如 Kimi Code、Claude Code）在 Windows 上需要它。"),
  N("s1", bold("解压噜咪助手"), "：把 lumi-zhushou.zip 解压到一个简单的路径，例如 ", code("D:\\lumi-zhushou"), "。"),
  N("s1", bold("在这个文件夹里打开终端"), "：打开文件夹，点地址栏，输入 ", code("powershell"), " 然后按回车。黑色窗口里显示的路径就是这个文件夹。"),
  P("检查是否装好（在终端里逐行输入，每行按回车，能看到版本号就对了）："),
  ...CODE(["python --version", "node --version", "git --version"]),
  P("国内下载 npm 包慢的话，先运行这一行，以后都会走国内镜像："),
  ...CODE(["npm config set registry https://registry.npmmirror.com"]),

  H1("5. 方案 A：TRAE CN（不用命令行）"),
  N("s2", "到 TRAE 中国版官网（trae.cn）下载安装，用抖音或头条账号登录。"),
  N("s2", "菜单里选“打开文件夹”，选噜咪助手的文件夹。"),
  N("s2", "在右边的 AI 对话框里，选能“执行操作/智能体”的模式（不是只聊天的模式）。"),
  N("s2", "第一句话发：", bold("“先读 CLAUDE.md 和 README.zh-CN.md，按里面的规则做。”")),
  N("s2", "之后就可以用第 8 节的话让它干活。它要运行命令时会问你，看一眼再允许。"),

  H1("6. 方案 B：CodeBuddy Code（腾讯，微信登录）"),
  N("s3", "在第 4 步打开的终端里安装："),
  ...CODE(["npm install -g @tencent-ai/codebuddy-code"]),
  N("s3", "在噜咪助手文件夹的终端里输入 ", code("codebuddy"), " 回车启动，按提示用微信扫码登录。"),
  N("s3", "免费额度可能要在官网定价页手动点“免费试用”才生效。"),
  N("s3", "第一句话同样发：", bold("“先读 CLAUDE.md 和 README.zh-CN.md，按里面的规则做。”")),

  H1("7. 方案 C（推荐）：Claude Code + 国产模型"),
  H2("7.1 安装 Claude Code"),
  ...CODE(["npm install -g @anthropic-ai/claude-code"]),
  P("装好后先不要运行，它默认会要求登录 Claude 账号（国内用不了）。先做下面的设置。"),
  H2("7.2 买套餐、拿到 API Key"),
  N("s4", "到 MiniMax 开放平台（国内站 platform.minimaxi.com）用手机号注册。"),
  N("s4", "购买 Coding Plan / Token Plan 的最低档（约 49 元/月）。"),
  N("s4", "在控制台创建一个 API Key，复制下来。", bold("这串字等于你的钱包密码，不要发到群里。")),
  H2("7.3 让 Claude Code 用 MiniMax"),
  P("最简单的办法是装一个图形小工具 ", bold("CC Switch"), "（开源，专门给 Claude Code 切换国产模型），在里面选 MiniMax，粘贴 API Key 就行。"),
  P("也可以手动设置：在 ", code("C:\\Users\\你的用户名\\.claude\\"), " 文件夹里新建 ", code("settings.json"), "，内容照 MiniMax 官方文档“Claude Code 配置”那一页复制，大致是这样："),
  ...CODE([
    "{",
    "  \"env\": {",
    "    \"ANTHROPIC_BASE_URL\": \"（官方文档给的地址，以 /anthropic 结尾）\",",
    "    \"ANTHROPIC_AUTH_TOKEN\": \"（你的 API Key）\",",
    "    \"ANTHROPIC_MODEL\": \"（官方文档给的模型名，例如 MiniMax-M3）\"",
    "  }",
    "}",
  ]),
  P(r("地址末尾不要多加 /v1，否则会报 404 错误。", { color: "C00000" })),
  H2("7.4 打开看图功能"),
  P("MiniMax 的看图工具是一个 MCP 插件。照官方文档“MCP 指南”那一页的 ", code("claude mcp add ..."), " 命令运行一次。然后启动 Claude Code，输入 ", code("/mcp"), "，能看到 ", code("understand_image"), " 就对了。"),
  H2("7.5 启动和测试"),
  N("s5", "在噜咪助手文件夹的终端里输入 ", code("claude"), " 回车。"),
  N("s5", "先测看图：", bold("“运行 python dev.py shot test，然后告诉我 shots/test_small.jpg 里游戏现在在哪个界面。”")),
  N("s5", "它能说对界面，就可以开始用了。"),
  BOX("用火山方舟（豆包）代替 MiniMax", [
    "步骤一样：火山引擎注册 → 购买方舟 Coding Plan Lite → 拿 API Key → 用 CC Switch 或 settings.json 配置（地址和模型名照火山方舟官方文档）。",
    "更便宜，但它的编程模型能不能看图没有确认，一定要先做 7.5 的看图测试。看不了图，脚本卡住时它就帮不上忙。",
  ], "FFF4E5", "C55A11"),
  gap(),

  H1("8. 让 AI 干活：直接复制这些话"),
  P("每次打开 AI 的第一句（Claude Code 可以省略）："),
  ...CODE(["先读 CLAUDE.md 和 README.zh-CN.md，按里面的规则做。"]),
  B(bold("第一次设置"), "：“帮我设置噜咪助手：建 .venv，装 requirements.txt，按 local.env.example 建 local.env，找到我的 MuMu 的 adb 和设备名，然后截一张图测试。”"),
  B(bold("跑日常"), "：“跑一下日常：python bot.py。卡住了就看截图帮我修。”"),
  B(bold("脚本卡住"), "：“脚本卡住了。看 shots/stuck_small.jpg 和 bot.log 最后 20 行，用点击回到主界面（不要按返回键），教脚本认识这个画面。”"),
  B(bold("改成我的阵容"), "：“我的天梯阵容是 ……。长按技能卡读技能，写进 team.md，按我的打法改 fight()。先打 3 场测试。”"),
  B(bold("改成我的生产"), "：“我想生产 ……，不生产 ……。改 PLAN，然后运行 python bot.py produce 测试。”"),
  B(bold("把改好的发回来"), "：“运行 python dev.py share 我的名字”，把生成的 zip 发到公会群，附一句改了什么、怎么测的。"),
  P(r("更多现成的话见噜咪助手里的 CONTRIBUTING.zh-CN.md（用记事本就能打开）。", { color: "595959", size: 20 })),

  H1("9. 规矩和省钱"),
  B(bold("看一眼再允许"), "：AI 要运行命令或改文件时会问你。看不懂就问它“这一步是做什么的？”。"),
  B(bold("绝不让它花钱"), "：不能点任何带 ¥ 的按钮、充值、礼包。花体力只能是你自己说的时候。"),
  B(bold("一件事一个对话"), "：做完一件事就开新对话（Claude Code 输入 ", code("/clear"), "），省额度。"),
  B(bold("让脚本跑，AI 只在卡住时看"), "：AI 一直盯着游戏会很快用完额度。"),
  B(bold("API Key 保密"), "：不要截图、不要发群。泄露了就去官网删掉重新建一个。"),
  B(bold("发截图前看一眼"), "：有名字、UID、聊天内容的地方先遮住。"),

  H1("10. 常见问题"),
  B(bold("输入命令说“不是内部或外部命令”"), "：对应的软件没装好，或者装的时候没勾选 PATH。重装后关掉终端再开一个。"),
  B(bold("npm 安装很慢或失败"), "：先运行第 4 节的 npmmirror 那一行。"),
  B(bold("Claude Code 一启动就要登录 Claude"), "：说明 7.3 的设置没生效。检查 settings.json 的位置和内容，或者用 CC Switch。"),
  B(bold("报 401 / 403"), "：API Key 错了或者套餐没买/过期了。"),
  B(bold("报 404"), "：地址写错了，多半是末尾多了 /v1。"),
  B(bold("额度用完了"), "：套餐一般每 5 小时恢复一部分，等一会儿，或者换用另一个工具的免费额度。"),
  B(bold("截图失败 screencap returned no image"), "：local.env 里的设备名不对。让 AI 帮你运行 adb devices 找正确的名字。"),
  gap(),
  P(r("信息来源：各工具官网与 2026 年 6–8 月的国内对比文章（博客园、CSDN、MiniMax / 火山方舟 / Kimi 官方文档）。价格和免费额度随时会变。", { size: 18, color: "7F7F7F" })),
];

const doc = new Document({
  creator: "lumi-zhushou",
  title: "噜咪助手 AI 编程助手使用指南",
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

Packer.toBuffer(doc).then(b => { fs.writeFileSync("AI编程助手使用指南.docx", b); console.log("written", b.length); });
