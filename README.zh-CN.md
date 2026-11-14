# 噜咪助手 (lumi-zhushou)

[English](README.md) | 简体中文

在 MuMu 模拟器上帮你完成 **闪耀吧！噜咪** 日常的小助手。
它通过 adb 截图和点击，用模板匹配识别画面，并且设计成由 Claude Code 来驱动。

- **日常由脚本完成**：餐厅、生产、订单、船队、归星、天梯、任务领取和每日免费福利。
- **脚本卡住时才请 Claude 来看**：Claude 读一张小截图，然后修好脚本或教它认识新画面。

这样 Claude 的用量很少。

> **助手遵守的规则：**
> - 绝不花真钱。
> - 只有你自己运行 `spend` 步骤时才消耗体力。
> - 唯一花金币的地方是每日归星时买便宜的紫色噜咪。

---

## 1. 需要准备

| 项目 | 设置 |
|---|---|
| MuMu 模拟器 12 | 分辨率 **720 × 1280，竖屏，240 DPI**（设置 → 显示）。所有点击位置都按这个分辨率写。 |
| 游戏语言 | 简体中文（模板和 OCR 识别的是中文） |
| Python | 3.10 或更新（Windows、WSL 或 Linux） |
| adb | MuMu 自带：`…\Netease\MuMu\nx_main\adb.exe` |
| Claude Code | 可选，但推荐：遇到没见过的画面由它处理 |

## 2. 安装

```bash
git clone https://github.com/Choplac/lumi-zhushou lumi-bot
cd lumi-bot
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux/WSL: source .venv/bin/activate
pip install -r requirements.txt
cp local.env.example local.env       # 然后编辑它
```

设置 `local.env`：

```
LUMI_ADB=C:\Program Files\Netease\MuMu\nx_main\adb.exe      # WSL 下用 /mnt/c/...
LUMI_SERIAL=127.0.0.1:16384                                   # 填 `adb devices` 列出的名字
```

检查它能不能看到游戏：

```bash
python dev.py shot test        # 生成 shots/test.png 和 shots/test_small.jpg
```

如果出现 `screencap returned no image` 或连接错误，说明设备名不对。
打开 MuMu，运行 `"<LUMI_ADB>" devices` 查看。有的 MuMu 显示 `emulator-5554`/`emulator-5558`，有的显示 `127.0.0.1:16384`。

## 3. 日常使用

先停在游戏主界面（冒险或家园），然后运行：

```bash
python bot.py                       # 完整日常
python bot.py orders dock           # 只跑部分步骤
python bot.py battle --battles 3    # 打 3 场天梯
python bot.py battle --battles 120  # 一直打到天梯显示 120 分
python bot.py spend --stamina 1000  # 体力自动跑图（只在你决定时用）
```

步骤（按默认顺序）：

| 步骤 | 做什么 |
|---|---|
| `canteen` | 在餐厅（章鱼那栋楼）上菜，敲晚餐铃，领金币箱 |
| `collect` | 收家园里的产物气泡 |
| `produce` | 按 `PLAN` 表重新开始暂停的生产线（见第 5 节） |
| `guixing` | 完成所有每日归星卡：每张用金币买 5 只便宜紫色噜咪，然后交接 |
| `explore` | 看信件，一键探险（只在真的出现一键探险页面时） |
| `orders` | 在订单板上按住交付，直到约 `--orders` 次（默认 110），再开 10/20/30 宝箱 |
| `dock` | 领回航船队的奖励。船队空着时保存 `shots/fleet_N_stock.jpg`，由你或 Claude 决定装什么 |
| `battle` | 天梯，按第 5 节的战斗思路打 |
| `claim` | 领每日任务和 15–75 分宝箱 |
| `freebies` | 商城每日赠礼、赛季通行证旅行目标和免费等级奖励、特惠礼包里的免费格子 |
| `spend` | **不在默认流程里。** 设置倍率（默认 ×10），长按表盘自动跑图，点开新遇到的噜咪，到体力预算或画面 90 秒没变时停下 |

**退出码：**
- `0`：完成。
- `2`：卡在不认识的画面。已保存 `shots/stuck.png` 和 `shots/stuck_small.jpg`，看小图，或者让 Claude 看。

日志写在 `bot.log`。

## 4. 配合 Claude Code 使用

在这个文件夹里打开 Claude Code。`CLAUDE.md` 告诉 Claude 规则（绝不按安卓返回键、看小截图、坐标乘 2 等）。
然后直接用平常的话说：

- “跑一下日常”
- “用 x10 花 2000 体力”
- “脚本卡住了，帮我看看”

省用量的办法：
- 让脚本自己跑，只有退出码是 2 时才叫 Claude。
- Claude 应该看 `*_small.jpg`（360 像素宽），不看原图。

## 5. 改成适合**你自己**的账号

下面这些是按第一个玩家的账号调好的。运行 `produce` 或 `battle` 之前先改。

**生产计划**（`bot.py` 里的 `PLAN`）。建筑名 → 生产什么：
- `("max", "<物品>")`：滑条拉满生产这个物品。
- `("low", None)`：生产已有数量最少的那个配方。

```python
PLAN = {"木材加工厂": ("max","木板"), "炉灶": ("low",None), "石材坊": ("max","砂石"),
        "建材加工台": ("low",None), "饮品摊": ("low",None), "水晶坊": ("max","紫水晶"),
        "精密制卡台": ("max","传奇噜咪卡")}
```

没列出的建筑不会被动。

**天梯战斗**（`bot.py` 里的 `TEAM` 和 `fight()`）。
- 它是按这个阵容写的（头像顺序）：光骑士兔、暗影兔、飞行猫鲨。
- `team.md` 写了打法：
  1. 光兔先出手。
  2. 免费手动换成暗影兔。
  3. 暗影兔出手，它在场时用黄色护盾。
  4. 然后是 4 费交接棒轮转。
  5. 猫鲨收尾。
- 如果你的阵容不同，战斗逻辑需要重写。这很适合交给 Claude：长按卡片看技能，再把你的打法告诉 Claude。

**交付速度。** `RATE_PER_S` 是按住交付时每秒交付的次数（这里是 4.0）。跑完后看 `shots/orders_count.png`，再调整。

**昼夜和新活动。** 模板在 `tpl/` 里。
- 如果某个按钮认不出了（夜晚光线、新赛季皮肤），在旧模板旁边加一个变体 `tpl/<名字>_2.png`。
- 截取方法：`python dev.py shot x` → `python dev.py crop <名字> X1 Y1 X2 Y2 x`。

## 6. 修脚本用的工具

```bash
python dev.py shot 名字            # 截图 → shots/名字.png + 名字_small.jpg
python dev.py tap X Y              # 原图坐标（小图坐标 x2）
python dev.py swipe X1 Y1 X2 Y2 毫秒 # 起点终点相同 + 时间长 = 长按
python dev.py crop 名字 X1 Y1 X2 Y2 来源   # 从 shots/来源.png 截出 tpl/名字.png
```

## 7. 踩过的坑

- **绝不要发送安卓返回键。** 游戏会弹出“退出游戏？”。`to_base()` 看到这个框会点取消。
- **家园镜头会漂移。** 离开家园再进去会重置镜头，`to_home()` 在点固定位置之前总会这样做。
- **点击后画面会延迟**，加载慢的菜单有时要好几秒。如果截图看起来慢了一步，等一下再截一次。
- **奖励弹窗点空白处关闭**，不要点 X。很多页面的 X 会把整个页面关掉。
- **公会页面的“…”按钮只有退出公会。** 绝对不要点。
- **CPU：** 助手以最低优先级运行，OCR 只用 2 个线程，不会拖慢电脑上的其他东西。

## 8. 仓库里的笔记

- `menus.md`：每个菜单里有什么、什么免费、什么要花钱、什么需要玩家自己决定。
- `production.md`：建筑、配方、时间，以及船队每种物品给多少。
- `team.md`：天梯阵容的技能和打法。

（这三份笔记目前是英文的。）

## 9. 使用须知

助手以人的速度、通过模拟器画面操作你自己的账号，和你亲手玩一样。风险自负：游戏条款可能不允许自动化。
