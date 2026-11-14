# 噜咪助手 (lumi-zhushou)

English | [简体中文](README.zh-CN.md)

A helper that plays the daily routine of **闪耀吧！噜咪** on the MuMu Android emulator.
It works through adb, finding things on screen by template matching, and it is built to be driven by a Claude Code session.

- **The script does the routine:** canteen, production, orders, fleets, 归星, ladder, task and daily freebie claims.
- **Claude only looks when the script is stuck:** it reads one small screenshot and fixes or teaches the script.

That keeps Claude's usage low.

> **Rules the bot keeps:**
> - It never pays real money.
> - It spends stamina only when you run the `spend` step yourself.
> - The only coins it spends are on the cheap purple 噜咪 for daily 归星.

---

## 1. What you need

| Thing | Setting |
|---|---|
| MuMu Player 12 | Resolution **720 × 1280, portrait, 240 DPI** (Settings → Display). Every tap position assumes this. |
| Game language | Simplified Chinese (templates and OCR read Chinese text) |
| Python | 3.10 or newer (Windows, WSL or Linux) |
| adb | MuMu ships one: `…\Netease\MuMu\nx_main\adb.exe` |
| Claude Code | Optional but recommended: it handles the unknown screens |

## 2. Install

```bash
git clone <this repo> lumi-bot
cd lumi-bot
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux/WSL: source .venv/bin/activate
pip install -r requirements.txt
cp local.env.example local.env       # then edit it
```

Set up `local.env`:

```
LUMI_ADB=C:\Program Files\Netease\MuMu\nx_main\adb.exe      # or /mnt/c/... from WSL
LUMI_SERIAL=127.0.0.1:16384                                   # whatever `adb devices` lists
```

Check that it can see the game:

```bash
python dev.py shot test        # writes shots/test.png and shots/test_small.jpg
```

If you get `screencap returned no image` or a connection error, the serial is wrong.
Run `"<LUMI_ADB>" devices` with MuMu open. Some MuMu installs list `emulator-5554`/`emulator-5558`, others `127.0.0.1:16384`.

## 3. Daily use

Start from the game's main screen (adventure or home) and run:

```bash
python bot.py                       # the whole daily routine
python bot.py orders dock           # only some steps
python bot.py battle --battles 3    # 3 ladder matches
python bot.py battle --battles 120  # play until the ladder shows 120 points
python bot.py spend --stamina 1000  # stamina auto-run (only when YOU decide)
```

Steps, in the default order:

| Step | What it does |
|---|---|
| `canteen` | Serves food in the canteen (餐厅, the octopus building), rings the dinner bell, takes the coin chest |
| `collect` | Collects the product bubbles at home |
| `produce` | Restarts paused production lines from the `PLAN` table (see §5) |
| `guixing` | Does every daily 归星 card: buys 5 cheap purple 噜咪 per card with coins, hands them over |
| `explore` | Reads letters, one-tap explore (only when the 一键探险 page really shows) |
| `orders` | Holds the 交付 button on the order board until about `--orders` deliveries (default 110), then opens the 10/20/30 chests |
| `dock` | Collects returned fleets. For an empty fleet it saves `shots/fleet_N_stock.jpg` so you or Claude can choose the cargo |
| `battle` | Ladder (天梯) with the fight plan in §5 |
| `claim` | Claims daily tasks and the 15–75 point chests |
| `freebies` | Shop 每日赠礼, season pass 旅行目标 tasks and free-track levels, free cells of 特惠礼包 |
| `spend` | **Not in the default run.** Sets the multiplier (×10 default), long-presses the dial to auto-run, taps newly met 噜咪, stops at the stamina budget or when the screen hasn't changed for 90 s |

**What the exit code means:**
- `0`: done.
- `2`: stuck on a screen it doesn't know. It saved `shots/stuck.png` and `shots/stuck_small.jpg`; look at the small one, or let Claude look.

The log goes to `bot.log`.

## 4. Using it with Claude Code

Open Claude Code in this folder. `CLAUDE.md` gives Claude the rules (never press Android back, read the small screenshots, double the coordinates, and so on).
You can then ask in plain words:

- "run the daily routine"
- "spend 2000 stamina at x10"
- "the bot is stuck, have a look"

How to keep Claude's usage low:
- Let the script run and call Claude only on exit code 2.
- Claude should read `*_small.jpg` (360 px wide), not the full PNG.

## 5. Making it fit **your** account

These parts are tuned to the first player's account. Change them before running `produce` or `battle`.

**Production plan** (`PLAN` in `bot.py`). Building name → what to make:
- `("max", "<item>")` makes that item at full slider.
- `("low", None)` makes whichever recipe has the smallest stock (已有).

```python
PLAN = {"木材加工厂": ("max","木板"), "炉灶": ("low",None), "石材坊": ("max","砂石"),
        "建材加工台": ("low",None), "饮品摊": ("low",None), "水晶坊": ("max","紫水晶"),
        "精密制卡台": ("max","传奇噜咪卡")}
```

Buildings that are not listed are never touched.

**Ladder fight** (`TEAM`, `fight()` in `bot.py`).
- It was written for this lineup, in portrait order: 光 knight rabbit, 暗影兔 (shadow rabbit), 飞行猫鲨.
- `team.md` explains the plan:
  1. The light rabbit strikes.
  2. A free manual swap to the shadow rabbit.
  3. The shadow rabbit strikes, with the yellow shield used while it is on the field.
  4. Then the 4-cost 交接棒 (hand-off) rotation.
  5. The shark finishes.
- If your team is different, the fight logic needs rewriting. That is a good job for Claude: hold a card to read its skills, then describe your plan to Claude.

**Orders speed.** `RATE_PER_S` is how many deliveries the game makes per second while 交付 is held (4.0 here). Check `shots/orders_count.png` after a run and adjust it.

**Night/day and new events.** Templates live in `tpl/`.
- If a button stops matching (night lighting, a new season skin), add a variant `tpl/<name>_2.png` next to the old one.
- To cut one: `python dev.py shot x` → `python dev.py crop <name> X1 Y1 X2 Y2 x`.

## 6. Tools for fixing it

```bash
python dev.py shot NAME            # screenshot → shots/NAME.png + NAME_small.jpg
python dev.py tap X Y              # full-resolution coordinates (small-image x2)
python dev.py swipe X1 Y1 X2 Y2 MS # same point + long MS = long-press
python dev.py crop NAME X1 Y1 X2 Y2 SRC   # cut tpl/NAME.png from shots/SRC.png
python dev.py share NAME           # zip your version to send back (no screenshots/local.env)
```

## 7. Things learned the hard way

- **Never send the Android back key.** The game opens "quit game?". `to_base()` cancels that box if it shows.
- **The home camera drifts.** Leaving home and entering again resets it, and `to_home()` always does that before fixed-position taps.
- **The screen lags after a tap**, sometimes several seconds on menus that load. If a screenshot looks one step behind, wait and take another.
- **Rewards are closed by tapping empty space**, not the X. The X on many pages closes the whole page.
- **On the guild page, the "…" button only offers 退出公会 (leave guild).** Never tap it.
- **CPU:** the bot runs at lowest priority with OCR on 2 threads, so it doesn't slow down other things on the PC.

## 8. Notes in this repo

- `menus.md`: every menu, what's free, what costs money, what is the player's choice.
- `production.md`: buildings, recipes, times, and what fleets pay per item.
- `team.md`: the ladder team's skills and the fight plan.

Each has a Chinese version (`*.zh-CN.md`).

## 9. Contributing

No coding needed: an AI assistant makes the change, and the zip goes back through the guild chat. GitHub is optional. See [CONTRIBUTING.md](CONTRIBUTING.md).

## 10. Fair use

This plays your own account the way you would, at human speed, through the emulator's screen. Use it at your own risk: the game's terms may not allow automation.
