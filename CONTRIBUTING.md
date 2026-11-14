# Contributing (no coding needed)

English | [简体中文](CONTRIBUTING.zh-CN.md)

An AI coding assistant writes the code. Contributors say what they want, check the result in the game, and send the new version back.

## GitHub is optional
GitHub is not blocked in mainland China, but it is often slow or unreliable. So the main route needs no GitHub:

1. Make the change with an AI coding tool opened in this folder.
   - Claude Code reads `CLAUDE.md` by itself.
   - Other tools: tell them to read `CLAUDE.md` first. Many read `AGENTS.md` on their own, and it points to the same rules.
2. Test it in the game by running only the step you changed.
3. Run `python dev.py share <your name>`.
   - It zips the project without screenshots, `local.env` or the log.
4. Send the zip to the guild chat with one or two lines: what changed and how it was tested.
5. The maintainer diffs it against the current version (with an AI), merges what's good, and posts the new zip and pushes to GitHub.

People who can use GitHub may open Issues and Pull Requests instead.

## Rules for changes
- One change at a time, tested in the game.
- Never add anything that pays money. Stamina is spent only in `spend`.
- Templates crop buttons and titles only: no names, UIDs or chat.
- Don't overwrite someone else's team or production plan; keep your own settings in your own copy.

## Reporting a problem without changing code
Send `shots/stuck_small.jpg` (hide any name/UID first), the last 20 lines of `bot.log`, and one line on what you were doing.

Ready-made prompts for common changes (stuck screen, different team, different production plan, new event freebies, night templates) are in the Chinese version, §3.
