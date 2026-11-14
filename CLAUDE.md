# Rules for Claude sessions driving lumi-bot

Read `README.md` first. It covers setup, steps, and what to customise.

## Hard rules
- **Never pay real money.** Never tap a price in ¥ or a 充值/礼包 purchase button.
- **Stamina is spent only when the player asks**, through `python bot.py spend --stamina N`.
- **Coins:**
  - The `guixing` step may spend coins only on the cheap purple 噜咪.
  - Ask before any other coin spending (特训, shop items, market bids).
- **Never use the Android back key** (`dev.py back`). It opens "quit game?".
- **Never tap the guild page's "…" button.** It only offers 退出公会.
- **Ask the player** about anything that gives away their 噜咪, answers surveys, or posts in world chat.

## Keeping usage low
- Run the script and look only when it exits 2 or the player asks.
- Read `shots/<name>_small.jpg` (360 px wide). Tap coordinates are **small × 2**.
- Batch taps with `sleep` in one shell call, then take one screenshot. Menus can lag 3–5 s, so wait before judging a screen.
- Prefer teaching the script a new template (`dev.py crop`) over solving the same screen by hand twice.

## Being polite to the PC
- The bot lowers its own priority and limits OCR threads.
- Don't start several bot runs at once. They share one emulator screen.

## When the bot is stuck
1. Look at `shots/stuck_small.jpg` and the end of `bot.log`.
2. Get the game back to the adventure or home screen using taps, never back.
3. If it is a new popup, add its template, and a branch in `to_base()` or the step.
4. Re-run only the failed step: `python bot.py <step>`.
