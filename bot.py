"""闪耀吧！噜咪 daily routine on MuMu (720x1280 @240).

  bot.py [step ...]      steps: canteen collect produce guixing explore orders dock battle claim freebies  (default: all; 'spend' only on request)
  options: --orders N (deliveries, default 110: 罐头 for guild war)
           --battles N (<=40: that many ladder matches; >40: play until that many ladder points, default 120)
           --stamina N (budget for the 'spend' step, default 1000)

Never pays real money. Spends stamina only in the 'spend' step, which runs only when named.
Spends coins only in 归星 (cheap purple 噜咪 from its shop).
Exit 0 = done; exit 2 = stuck on an unknown screen (shots/stuck.png saved for Claude).
"""
import os, sys, time, argparse, datetime
# Be polite to a shared PC: lowest CPU priority, OCR on at most 2 threads.
if hasattr(os, "nice"):          # Linux/WSL/macOS; plain Windows has no nice
    os.nice(19 - os.nice(0))
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")
import cv2
import numpy as np
import dev

LOG = dev.ROOT / "bot.log"


def log(msg):
    line = f"{datetime.datetime.now():%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


class Stuck(Exception):
    pass


_tpl_cache = {}


def _variants(name):
    """tpl/<name>.png plus look-alikes tpl/<name>_2.png, _3 ... (day/night etc.)."""
    if name not in _tpl_cache:
        files = [dev.TPL / f"{name}.png"] + sorted(dev.TPL.glob(f"{name}_[0-9].png"))
        _tpl_cache[name] = [cv2.cvtColor(cv2.imread(str(f)), cv2.COLOR_BGR2GRAY) for f in files]
    return _tpl_cache[name]


def find(img, name, thresh=0.85):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    for t in _variants(name):
        _, score, _, loc = cv2.minMaxLoc(cv2.matchTemplate(g, t, cv2.TM_CCOEFF_NORMED))
        if score >= thresh:
            h, w = t.shape
            return loc[0] + w // 2, loc[1] + h // 2
    return None


def shot():
    return dev.screenshot()


def tap(x, y, wait=1.5):
    dev.tap(x, y)
    time.sleep(wait)


def wait_for(name, timeout=8, thresh=0.85):
    end = time.time() + timeout
    while time.time() < end:
        img = shot()
        p = find(img, name, thresh)
        if p:
            return p
        time.sleep(0.7)
    return None


def stuck(why):
    dev.save_shot(shot(), "stuck")
    raise Stuck(why)


CLOSE_X = (360, 1228)


def _bw(g):
    return (g < 110).astype("uint8") * 255


def base_kind(img):
    """'adv' / 'home' from the dark letters of the bottom-right label (map behind it changes
    with day/night and camera, so only the letters are compared). None on other screens."""
    g = _bw(cv2.cvtColor(img[1150:1280, 440:720], cv2.COLOR_BGR2GRAY))
    sc = {}
    for kind, name in (("adv", "scr_adv"), ("home", "scr_home")):
        t = _bw(cv2.imread(str(dev.TPL / f"{name}.png"), 0))
        sc[kind] = cv2.minMaxLoc(cv2.matchTemplate(g, t, cv2.TM_CCOEFF_NORMED))[1]
    best = max(sc, key=sc.get)
    return best if sc[best] >= 0.65 and sc[best] - min(sc.values()) > 0.1 else None


def to_base():
    """Close popups/screens until the adventure or home screen shows. Returns 'adv' or 'home'."""
    for _ in range(10):
        img = shot()
        if find(img, "quit_dialog"):
            tap(274, 684); continue                    # cancel "quit game?"
        if find(img, "banner_reward"):
            tap(360, 1240); continue                   # "tap empty space to close"
        if find(img, "pop_selfsuff"):
            tap(360, 60); continue                     # daily home summary: tap outside
        if find(img, "title_battle", 0.9):
            tap(410, 1200); continue                   # battle tab: its X closes it
        kind = base_kind(img)
        if kind:
            return kind
        n = len(list(dev.SHOTS.glob("unknown_*.png"))) % 20
        dev.save_shot(img, f"unknown_{n:02d}")         # for Claude to teach later
        log(f"to_base: unknown screen saved as unknown_{n:02d}, tapping close")
        tap(*CLOSE_X)
    stuck("cannot get back to the main screens")


def to_home():
    """Open home with the camera at its default spot (leaving and re-entering resets it)."""
    if to_base() == "home":
        tap(552, 1238, 3)
        if to_base() != "adv":
            stuck("adventure screen did not open")
    tap(552, 1238, 3)
    if to_base() != "home":
        stuck("home did not open")


# ---------------------------------------------------------------- steps

def collect():
    to_home()
    tap(464, 374, 2)          # any product bubble collects all of them
    to_base()
    log("collect: done")


def explore():
    to_home()
    tap(660, 680, 2.5)
    if not wait_for("title_explore"):
        stuck("exploration screen did not open")
    letters = 0
    for _ in range(30):
        img = shot()
        if find(img, "banner_reward"):
            tap(360, 1200, 1.5)
        elif (p := find(img, "btn_claim_gift")):
            tap(*p, 2); letters += 1
        elif (p := find(img, "btn_view_letter")):
            tap(*p, 2)
        else:
            break
    tap(110, 1146, 2)          # one-tap explore
    img = shot()
    p = find(img, "btn_depart", 0.9) if find(img, "title_oneclick", 0.9) else None
    if p:
        tap(*p, 2.5); sent = True
    else:
        sent = False           # nothing free to send; the plain screen has a look-alike button
    to_base()
    log(f"explore: {letters} letters collected, new trips sent={sent}")


RATE_PER_S = 4.0                # orders per second while 交付 is held (11-14: 8 in 2 s)


def orders(n):
    to_home()
    tap(516, 910, 2.5)
    if not wait_for("title_orderboard"):
        stuck("order board did not open")
    done = 0
    # Holding 交付 delivers continuously: measured 8 in a 2 s hold (~4/s). Hold in short
    # pieces so chest popups can be closed and an unfillable order stops the run.
    held, misses = 0.0, 0
    budget = n / RATE_PER_S
    while held < budget and misses < 3:
        img = shot()
        if find(img, "banner_reward"):            # milestone chest popped up
            tap(360, 1200, 1.5); continue
        p = find(img, "btn_deliver", 0.92)
        if not p:
            misses += 1; time.sleep(1.5); continue
        misses = 0
        piece = min(5.5, budget - held)
        dev.swipe(p[0], p[1], p[0], p[1], int(piece * 1000)); time.sleep(1.5)
        held += piece
    done = round(held * RATE_PER_S)
    for x in (294, 464, 634):  # 10 / 20 / 30 delivery chests
        tap(x, 600, 1.5)
        if find(shot(), "banner_reward"):
            tap(360, 1200, 1.5)
    cv2.imwrite(str(dev.SHOTS / "orders_count.png"), shot()[630:670, 60:140])   # counter, for checking
    to_base()
    log(f"orders: about {done} delivered (held {held:.1f} s)")


def canteen():
    to_home()
    dev.swipe(200, 700, 461, 642, 1500); time.sleep(1.5)   # same drag as the player's: canteen to centre
    tap(372, 640, 2.5)
    if not wait_for("title_canteen"):
        stuck("canteen did not open")
    p = find(shot(), "btn_serve", 0.9)
    if p:
        tap(*p, 2)             # one-tap serve: refill the 8 dish slots
    tap(660, 150, 2)           # dinner bell
    p = find(shot(), "btn_dinner", 0.9)
    if p:
        tap(*p, 3)
    tap(360, 510, 2)           # collect today's canteen coins
    to_base()
    log("canteen: served, bell rung, coins collected")


# ---------------------------------------------------------------- OCR + production

_ocr = None


def ocr(img, box=None):
    """[(text, cx, cy)] in full-screen coordinates. box = (x1, y1, x2, y2)."""
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)
    x1, y1, x2, y2 = box or (0, 0, img.shape[1], img.shape[0])
    res, _ = _ocr(img[y1:y2, x1:x2])
    out = []
    for pts, text, _score in res or []:
        cx = sum(p[0] for p in pts) / 4 + x1
        cy = sum(p[1] for p in pts) / 4 + y1
        out.append((text.strip(), int(cx), int(cy), int(max(p[0] for p in pts) + x1)))
    return out


def read_num(img, box):
    """One number from a small fixed box (no text detection: ~0.2 s on one core)."""
    ocr(img, (0, 0, 8, 8)) if _ocr is None else None
    x1, y1, x2, y2 = box
    res, _ = _ocr(img[y1:y2, x1:x2], use_det=False, use_cls=False, use_rec=True)
    return _num(res[0][0]) if res else None


def _num(t):
    d = "".join(ch for ch in t if ch.isdigit())
    return int(d) if d else None


# Player 11-14: which processing buildings run and what they make.
#   "max": one fixed recipe;  "low": the recipe with the smallest stock.
PLAN = {
    "木材加工厂": ("max", "木板"),
    "炉灶": ("low", None),
    "石材坊": ("max", "砂石"),
    "建材加工台": ("low", None),
    "饮品摊": ("low", None),
    "水晶坊": ("max", "紫水晶"),
    "精密制卡台": ("max", "传奇噜咪卡"),
}
MANAGE_TABS = {"食物": (180, 1054), "产物": (360, 1054)}
LIST_BOX = (0, 270, 720, 1010)


def _manage_rows(img):
    """Building rows visible in Manage: [(name, paused, x, y)]."""
    items = ocr(img, LIST_BOX)
    rows = []
    for t, x, y, x2 in items:
        name = next((n for n in PLAN if n in t), None)
        if name and x < 400:
            status = [u for u, ux, uy, _ in items if abs(uy - y) < 25 and ux < x and ("暂停" in u or "生产" in u)]
            rows.append((name, bool(status) and "暂停" in status[0], x2 + 18, y))   # the '›' after the name
    return rows


def _start_in_building(name):
    """In a building view: choose the recipe per PLAN, max amount, press 制作."""
    mode, recipe = PLAN[name]
    img = shot()
    items = ocr(img, (0, 640, 720, 900))
    cards = []                                      # (recipe name, x, stock)
    for t, x, y, _ in items:
        if t.startswith("已有"):
            label = min((u for u in items if abs(u[1] - x) < 60 and u[2] < y and not u[0].startswith("已有")),
                        key=lambda u: y - u[2], default=("?", x, y))
            cards.append((label[0], x, _num(t) or 0, label[2]))
    if not cards:
        stuck(f"{name}: no recipes read")
    if mode == "max":
        pick = next((c for c in cards if recipe in c[0]), None)
        if not pick:
            stuck(f"{name}: recipe {recipe} not found in {cards}")
    else:
        pick = min(cards, key=lambda c: c[2])
    tap(pick[1], pick[3] + 40, 1.5)                 # select the recipe card
    k = find(shot(), "slider_knob", 0.75)
    if k:
        dev.swipe(k[0], k[1], 640, k[1], 800); time.sleep(1.2)
    p = find(shot(), "btn_make", 0.85)
    if not p:
        stuck(f"{name}: no 制作 button")
    tap(*p, 2.5)
    return pick[0], pick[2]


def produce():
    to_home()
    tap(660, 940, 2.5)                              # Manage
    started = []
    for tab, xy in MANAGE_TABS.items():
        for _ in range(12):                         # rescan after every start (it returns to Manage)
            tap(*xy, 1.5)
            todo = None
            for scroll in range(6):
                rows = _manage_rows(shot())
                todo = next((r for r in rows if r[1]), None)
                if todo:
                    break
                dev.swipe(360, 900, 360, 450, 1000); time.sleep(1.2)
            if not todo:
                break
            time.sleep(1.5)                         # let the list stop sliding, then re-read
            todo = next((r for r in _manage_rows(shot()) if r[0] == todo[0] and r[1]), todo)
            name, _, x, y = todo
            tap(x, y, 2.5)                          # the '›' after the name opens the building
            if not find(shot(), "bld_arrow_r", 0.85):
                stuck(f"{name}: building view did not open")
            what, stock = _start_in_building(name)
            started.append(f"{name}:{what}(had {stock})")
            if not find(shot(), "btn_apply_manage", 0.85):
                to_home(); tap(660, 940, 2.5)
    to_base()
    log(f"produce: started {started or 'nothing (all running)'}")


def guixing(max_cards=8):
    """Daily 归星 (player 11-14: do all daily cards; buy the cheap purple 噜咪 with coins).

    For each open daily card: open it, buy the cheapest matching purple 噜咪 from the card's own
    shop (5 x ~5,300 coins), hand them over. Only bought 噜咪 are used: the player's own are never
    selected, and anything other than '<type> x5 + 紫色品质 x5' stops for Claude."""
    to_home()
    tap(660, 800, 2.5)                              # 归星 (star tree)
    done = 0
    for _ in range(max_cards):
        if find(shot(), "banner_reward"):
            tap(360, 1240, 1.5)
        top = ocr(shot(), (80, 280, 360, 320))      # first card's '0/1次' counter
        if not any("0/1" in t for t, *_ in top):
            break                                   # first card already done -> all done
        tap(224, 520, 2.5)                          # open the card
        reqs = [t for t, *_ in ocr(shot(), (0, 540, 720, 660)) if "只" in t]
        if len(reqs) != 2 or not any("紫色品质" in t for t in reqs) or any("/5" not in t for t in reqs):
            stuck(f"归星: unexpected requirements {reqs}")
        tap(498, 1138, 2.5)                         # cart: shop filtered to matching purple 噜咪
        tap(152, 560, 2.5)                          # cheapest
        for _ in range(4):
            tap(644, 974, 0.6)                      # quantity 5
        q = [t for t, *_ in ocr(shot(), (0, 800, 720, 1110))]
        if "数量：5" not in q:
            stuck(f"归星: quantity not 5: {q}")
        tap(360, 1130, 3)                           # 购买并放入
        tap(620, 300, 2)                            # close the 'got' popup
        reqs = [t for t, *_ in ocr(shot(), (0, 180, 720, 280))]
        if sum("5/5" in t for t in reqs) != 2:
            stuck(f"归星: requirements not met after buying: {reqs}")
        tap(*CLOSE_X, 2)                            # back to the card with its 5 slots filled
        p = find(shot(), "btn_handover", 0.85)
        if not p:
            stuck("归星: 交付 button not found")
        tap(*p, 2.5)
        p = find(shot(), "btn_confirm_release", 0.85)
        if not p:
            stuck("归星: release confirm not found")
        tap(*p, 3)
        tap(360, 1240, 2)                           # close the reward
        done += 1
    to_base()
    log(f"guixing: {done} daily cards handed in")


DIAL, MULT = (430, 890), (429, 760)
STILL_LIMIT_S = 90                # player: no page change for 1-2 min -> stop for Claude


def stamina():
    t = " ".join(t for t, *_ in ocr(shot(), (400, 10, 560, 60)))
    return _num(t.split("/")[0]) if "/" in t else None


def spend(budget, mult="X10"):
    """Player 11-14: the main loop. Auto-run the adventure dial at `mult` until `budget` stamina is
    spent; tap newly met 噜咪 on the area map (that page stops auto-run) and restart it."""
    if base_kind(shot()) == "home":
        tap(552, 1238, 3)
    start = None
    for _ in range(12):                               # an event may be covering the counter
        start = stamina()
        if start is not None:
            break
        time.sleep(5)
    if start is None:
        stuck("spend: stamina not read")
    stop_at = start - budget
    log(f"spend: stamina {start}, stopping at {stop_at}")
    unknown, last_log = 0, 0
    prev, still_since = None, time.time()
    while True:
        img = shot()
        # Player 11-14: if the page has not changed for ~1.5 min, stop and let Claude look.
        small = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (90, 160)).astype("int16")
        if prev is not None and abs(small - prev).mean() > 2.0:
            still_since = time.time()
        prev = small
        if time.time() - still_since > STILL_LIMIT_S:
            stuck(f"spend: screen unchanged for {STILL_LIMIT_S} s (stamina spent so far: "
                  f"{start - (stamina() or start)})")
        top_right = " ".join(t for t, *_ in ocr(img, (480, 200, 720, 260)))
        if "地图" in top_right:                       # area map after meeting a new 噜咪
            p = find(img, "new_lumi_spark", 0.75)
            if p:
                tap(*p, 2.5); log("spend: new 噜咪 on the map, tapped"); continue
            if any("地图" in t for t, *_ in ocr(img, (0, 1100, 720, 1180))):   # tabs + X visible
                tap(*CLOSE_X, 2.5)
            else:
                tap(360, 1228, 2.5)
            continue
        if base_kind(img) == "adv":
            unknown = 0
            st = stamina()
            label = " ".join(t for t, *_ in ocr(img, (200, 1160, 520, 1230)))
            if st is not None and st <= stop_at:
                if "自动" in label:
                    tap(360, 1196, 2)                  # stop auto-run
                log(f"spend: done, stamina {st} (spent {start - st})"); break
            if "自动" not in label:
                m = " ".join(t for t, *_ in ocr(img, (360, 720, 500, 800))).upper()
                for _ in range(6):
                    if mult in m:
                        break
                    tap(*MULT, 1.2)
                    m = " ".join(t for t, *_ in ocr(shot(), (360, 720, 500, 800))).upper()
                dev.swipe(*DIAL, *DIAL, 2500); time.sleep(3)
                log(f"spend: auto-run (re)started at {m}, stamina {st}")
            elif time.time() - last_log > 120:
                log(f"spend: running, stamina {st}"); last_log = time.time()
            time.sleep(8); continue
        if find(img, "banner_reward"):                # "恭喜获得": tap empty space
            unknown = 0; tap(620, 1000, 2); continue
        bottom = " ".join(t for t, *_ in ocr(img, (0, 1120, 720, 1240)))
        if "技能" in bottom and "档案" in bottom:      # a caught 噜咪's detail page
            unknown = 0; tap(*CLOSE_X, 2); continue
        if "自动" in bottom:                           # auto-run on; events play themselves
            unknown = 0
            st = stamina()
            if st is not None and st <= stop_at:
                tap(360, 1196, 3)                      # tap '自动进行中' to stop auto-run
                log(f"spend: target reached, stamina {st} (spent {start - st}); auto-run stopped")
                break
            if time.time() - last_log > 120:
                log(f"spend: running, stamina {st}"); last_log = time.time()
            time.sleep(5); continue
        unknown += 1
        if unknown >= 4:
            stuck("spend: unknown screen during the stamina run")
        time.sleep(5)


def open_tasks():
    to_base()
    tap(100, 1200, 2)
    if not find(shot(), "menu_header"):
        stuck("menu did not open")
    tap(416, 980, 2)
    tap(356, 1154, 2)


def go_task(label):
    """In the daily task list, tap 'Go' on the row with this label. False if not listed."""
    for attempt in range(2):
        p = find(shot(), label, 0.75)
        if p:
            tap(606, p[1] + 74, 3)
            return True
        dev.swipe(360, 1000, 360, 600, 600); time.sleep(1.5)
    return False


TABS = (150, 290, 430, 570)    # fleet cargo tabs = the 4 whales: produce, dishes, raw, processed


def dock():
    """Collect returned fleets' rewards; report fleets 1-2 that still need cargo.

    Cargo is chosen by Claude from shots/fleet_<n>_stock.jpg (one item per tab, from real
    surplus; see production.md), because the right amounts depend on the day's stock."""
    to_home()
    tap(660, 868, 2.5)         # whale icon in the right column
    if not wait_for("title_dock"):
        stuck("dock did not open")
    tap(300, 690, 2.5)         # reward bubbles over a returned fleet: one tap collects all
    if find(shot(), "banner_reward"):
        tap(360, 1240, 1.5)
    if not find(shot(), "title_dock"):
        tap(*CLOSE_X, 2)       # the tap opened a fleet instead: back to the dock
    tap(462, 476, 2.5)         # fleet 1
    empty = []
    for n in (1, 2):           # the player fills the 3rd only from real excess
        rows, loaded = [], 0
        for x in TABS:
            tap(x, 610, 1.2)
            img = shot()
            loaded += bool(find(img, "btn_unload", 0.9))
            rows.append(img[580:900])
        if loaded == 0:
            empty.append(n)
            cv2.imwrite(str(dev.SHOTS / f"fleet_{n}_stock.jpg"),
                        cv2.resize(np.vstack(rows), (480, 853)), [cv2.IMWRITE_JPEG_QUALITY, 80])
        tap(680, 350, 2)       # next fleet
    to_base()
    log(f"dock: rewards collected; fleets needing cargo: {empty or 'none'}")


TOP_CARD, BOTTOM_CARD = (640, 870), (640, 1030)
SHIELD = (644, 1196)              # yellow 光灵 shield (blocks enemy skills), bottom right


STRIKES_BEFORE_HANDOFF = 1      # rabbits: strikes before 交接棒 (tuned from match results)
TEAM = ("light", "shadow", "shark")                 # ladder team order = portrait order (player 11-14 10:15)
PORTRAITS = ((96, 1070), (236, 1070), (356, 1070))  # bottom-left; tap = free manual swap (has a CD)


def active_slot(img):
    """Index of the 噜咪 on the field: its portrait sits on a bright yellow base."""
    hsv = cv2.cvtColor(img[1100:1112], cv2.COLOR_BGR2HSV)
    v = [hsv[:, x - 45:x - 25, 2].mean() for x, _ in PORTRAITS]
    best = max(range(3), key=lambda i: v[i])
    return best if v[best] > 200 else None


def fight(limit=420):
    """Play one ladder fight with the team plan in team.md; returns "WIN"/"LOSS"/"?" or None.

    Boost levels only survive a swap through 交接棒; a manual swap (portrait tap) is free but drops
    them, so it is used only by a 噜咪 with nothing to lose (the shark when it did not receive a
    hand-off). Rabbits: strike (mark + boost) then 交接棒. Shark: if it carries handed-on boosts,
    spend them on 元气共鸣 and leave by 燕返; if not, swap manually to the rabbit whose entry bonus
    fires (the opposite of the last mark), falling back to 燕返 when the swap is on cooldown."""
    end = time.time() + limit
    strikes, slot, actions, result = 0, None, [], "?"
    handoff_pending, carries, last_mark, swap_tried, opened = False, False, None, 0.0, False
    shield_used = False
    while time.time() < end:
        img = shot()
        if find(img, "btn_match"):
            log(f"fight: {result}; actions {' '.join(actions)}")
            return result
        power = read_num(img, (600, 885, 720, 930))
        power = power % 100 if power else None     # the card edge sometimes reads as a leading '1'
        energy = read_num(img, (30, 1205, 90, 1250))
        now = active_slot(img)
        if power not in (75, 80) and not find(img, "battle_flag", 0.8):   # intro / result screens
            top = " ".join(t for t, *_ in ocr(img, (0, 80, 720, 320)))
            if "胜利" in top: result = "WIN"
            elif "失败" in top: result = "LOSS"
            tap(620, 640, 1.2); continue           # empty sand: closes "点击空白处关闭" screens
        if energy is None or now is None or power not in (75, 80):
            time.sleep(0.4); continue              # an OCR miss is not a new 噜咪
        if now != slot:                            # someone new on the field
            if slot is not None:
                opened = True                       # the opener is over once anyone has swapped
            swap_tried = 0.0 if not opened else swap_tried
            carries = handoff_pending
            handoff_pending, strikes, slot = False, 0, now
            actions.append(f"[{TEAM[now]}{'+' if carries else ''}]")
        who = TEAM[slot]
        if who == "shadow" and not shield_used:
            dev.tap(*SHIELD); shield_used = True; actions.append("D")   # player: shield with the dark rabbit
            time.sleep(0.6)
        if who != "shark" and not opened and strikes >= 1:
            # player's opener: first rabbit strikes once (marks), then a FREE manual swap to the
            # other rabbit, which enters on the opposite mark (+1/+1, swap cooldown reset)
            other = TEAM.index("shadow" if who == "light" else "light")
            if swap_tried == 0.0:
                dev.tap(*PORTRAITS[other]); swap_tried = time.time(); actions.append("m")
            elif time.time() - swap_tried < 4:
                dev.tap(*PORTRAITS[other])          # retry: a tap during an animation is swallowed
            else:
                opened = True                       # swap was on cooldown: carry on with 交接棒
            time.sleep(0.8); continue
        if who != "shark":
            if strikes < STRIKES_BEFORE_HANDOFF and energy >= 5:
                dev.tap(*TOP_CARD); strikes += 1; last_mark = who; actions.append("S")
            elif strikes >= STRIKES_BEFORE_HANDOFF and energy >= 4:
                dev.tap(*BOTTOM_CARD); handoff_pending = True; actions.append("H")
        else:
            if carries:
                if energy >= 5:
                    dev.tap(*TOP_CARD); carries = False; actions.append("R")
            elif time.time() - swap_tried > 4:
                target = 1 if last_mark == "shadow" else 0          # the opposite rabbit
                dev.tap(*PORTRAITS[target]); swap_tried = time.time(); actions.append("m")
            elif energy >= 8:
                dev.tap(*TOP_CARD); actions.append("R")
            elif energy >= 3:
                dev.tap(*BOTTOM_CARD); actions.append("Y")
        time.sleep(0.8)
    return None


def ladder_points():
    """Today's ladder points: the number at the left end of the reward bar."""
    return next((_num(t) for t, x, y, _ in ocr(shot(), (0, 60, 720, 300))
                 if x < 170 and 150 < y < 178 and _num(t) is not None), None)


def ladder_status():
    """Text of the ladder header (rank + points), to compare before/after."""
    return " ".join(t for t, *_ in ocr(shot(), (0, 60, 720, 300)))


def battle(n):
    to_base()
    tap(410, 1200, 2.5)
    tap(606, 500, 3)           # ladder (天梯) 出发
    if not wait_for("btn_match", 10):
        stuck("ladder screen did not open")
    target = n if n > 40 else None                 # n > 40 means "play until this many points"
    rounds = 40 if target else n
    for i in range(rounds):
        pts = ladder_points()
        if target and pts is not None and pts >= target:
            log(f"battle: ladder points {pts} >= {target}, done"); break
        p = find(shot(), "btn_match")
        tap(*p, 15)            # matchmaking + "prepare" countdown
        res = fight()
        if not res:
            stuck("ladder match did not finish in 7 minutes")
        log(f"battle: ladder match {i + 1}/{n}: {res}; ladder now: {ladder_status()}")
    to_base()


def _red_dots(img, x1, y1, x2, y2):
    """Centres of red notification dots inside a box (full-res coordinates)."""
    hsv = cv2.cvtColor(img[y1:y2, x1:x2], cv2.COLOR_BGR2HSV)
    m = (((hsv[..., 0] < 8) | (hsv[..., 0] > 172)) & (hsv[..., 1] > 150) & (hsv[..., 2] > 170)).astype("uint8")
    n, _, st, cen = cv2.connectedComponentsWithStats(m)
    return [(int(cen[i][0]) + x1, int(cen[i][1]) + y1) for i in range(1, n) if st[i][4] >= 40]


def freebies():
    """Free daily things outside the task list (menu tour 11-14):
    shop 每日赠礼 (20 stamina), season pass 旅行目标 tasks + free-track levels, 特惠礼包 free items.
    Never taps anything with a price."""
    to_base()
    # 1. shop daily gift: shop icon is top-left on both main screens
    tap(44, 184, 4)
    if find(shot(), "title_shop_gift", 0.8):
        tap(84, 206, 3)
        tap(360, 1140, 2)                  # close the reward (tap empty space)
        tap(*CLOSE_X, 3)
        log("freebies: shop daily gift tapped")
    to_base()
    # 2. season pass: season icon -> 通行证; an intro carousel may show first (its X opens the pass)
    tap(48, 290, 5)
    tap(150, 920, 5)
    if not find(shot(), "title_pass", 0.8):
        tap(*CLOSE_X, 4)
    if find(shot(), "title_pass", 0.8):
        tap(530, 1150, 3)                  # 旅行目标 tab
        got = 0
        for _ in range(8):
            p = find(shot(), "btn_pass_claim", 0.85)
            if not p:
                break
            tap(*p, 2.5); tap(360, 1140, 1.5); got += 1
        tap(180, 1150, 3)                  # rewards tab: free track = left column
        lv = 0
        for _ in range(6):
            dots = _red_dots(shot(), 130, 360, 250, 1000)
            if not dots:
                break
            tap(dots[0][0] - 24, dots[0][1] + 32, 2.5); tap(360, 1140, 1.5); lv += 1
        log(f"freebies: pass tasks {got}, free levels {lv}")
        tap(*CLOSE_X, 4)                   # pass -> season page
        tap(*CLOSE_X, 4)                   # season page -> main
    else:
        log("freebies: season pass did not open (shots/freebies_pass saved)")
        dev.save_shot(shot(), "freebies_pass")
    # 3. 特惠礼包 (adventure screen, 3rd left icon): claim unlocked 免费 cells, stop at the paid one
    if to_base() != "adv":
        tap(552, 1238, 4)
    if to_base() == "adv":
        tap(44, 370, 4)
        if find(shot(), "title_deal", 0.8):
            n = 0
            for _ in range(6):
                p = find(shot(), "tag_free", 0.85)
                if not p:
                    break
                tap(p[0] - 76, p[1] + 96, 2.5); tap(360, 1140, 1.5); n += 1
            log(f"freebies: deal pack free items {n}")
            tap(360, 1210, 3)
    to_base()


def claim():
    open_tasks()
    got = 0
    for _ in range(10):
        img = shot()
        if find(img, "banner_reward"):
            tap(360, 1240, 1.5); continue
        p = find(img, "btn_claim", 0.9)
        if not p:
            break
        tap(*p, 2); got += 1
    for x in (188, 304, 424, 540, 660):   # 15..75 point chests
        tap(x, 472, 1.5)
        if find(shot(), "banner_reward"):
            tap(360, 1240, 1.5)
    to_base()
    log(f"claim: {got} tasks claimed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("steps", nargs="*")
    ap.add_argument("--stamina", type=int, default=1000)   # 'spend' step budget
    ap.add_argument("--orders", type=int, default=110)   # player: 100-120 a day, they give 罐头 for guild war
    ap.add_argument("--battles", type=int, default=120)   # >40 = play until that many ladder points (player: ~120)
    a = ap.parse_args()
    steps = a.steps or ["canteen", "collect", "produce", "guixing", "explore", "orders", "dock", "battle", "claim", "freebies"]
    run = {"spend": lambda: spend(a.stamina), "canteen": canteen, "collect": collect, "produce": produce, "guixing": guixing, "explore": explore, "orders": lambda: orders(a.orders),
           "dock": dock, "battle": lambda: battle(a.battles), "claim": claim, "freebies": freebies}
    log(f"start {steps}")
    try:
        for s in steps:
            run[s]()
    except Stuck as e:
        log(f"STUCK: {e} -> shots/stuck_small.jpg")
        sys.exit(2)
    log("finished")


if __name__ == "__main__":
    main()
