"""Small adb helpers for MuMu (720x1280 @240 DPI, portrait). NEVER use `back`: in this game it opens "quit game?".

Usage:
  dev.py shot [name]        save full PNG to shots/<name>.png and a small JPEG for Claude
  dev.py tap X Y            tap at full-resolution coordinates
  dev.py swipe X1 Y1 X2 Y2 [ms]
  dev.py back
  dev.py crop name X1 Y1 X2 Y2 [src]   cut a button template from a shot into tpl/<name>.png
"""
import os, subprocess, sys, pathlib
import numpy as np
import cv2

ROOT = pathlib.Path(__file__).resolve().parent
# Per-PC settings: environment variables, or KEY=VALUE lines in local.env (not committed).
_LOCAL = ROOT / "local.env"
if _LOCAL.exists():
    for _line in _LOCAL.read_text(encoding="utf-8").splitlines():
        if "=" in _line and not _line.lstrip().startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())
ADB = os.environ.get("LUMI_ADB", "adb")                  # path to adb (MuMu ships its own adb.exe)
SERIAL = os.environ.get("LUMI_SERIAL", "127.0.0.1:16384")  # see `adb devices`
SHOTS = ROOT / "shots"
TPL = ROOT / "tpl"
SMALL_W = 360  # what Claude looks at: half size, JPEG


def adb(*args, out=False):
    cmd = [ADB, "-s", SERIAL, *args]
    if out:
        return subprocess.run(cmd, capture_output=True, timeout=30, check=True).stdout
    subprocess.run(cmd, timeout=30, check=True, capture_output=True)


def screenshot():
    raw = adb("exec-out", "screencap", "-p", out=True)
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError("screencap returned no image")
    return img


def save_shot(img, name="last"):
    SHOTS.mkdir(exist_ok=True)
    cv2.imwrite(str(SHOTS / f"{name}.png"), img)
    h, w = img.shape[:2]
    small = cv2.resize(img, (SMALL_W, int(h * SMALL_W / w)), interpolation=cv2.INTER_AREA)
    p = SHOTS / f"{name}_small.jpg"
    cv2.imwrite(str(p), small, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return p


def tap(x, y):
    adb("shell", "input", "tap", str(int(x)), str(int(y)))


def swipe(x1, y1, x2, y2, ms=300):
    adb("shell", "input", "swipe", *map(str, map(int, (x1, y1, x2, y2, ms))))


def back():
    adb("shell", "input", "keyevent", "4")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    if a[0] == "shot":
        print(save_shot(screenshot(), a[1] if len(a) > 1 else "last"))
    elif a[0] == "tap":
        tap(a[1], a[2])
    elif a[0] == "swipe":
        swipe(*a[1:6]) if len(a) > 5 else swipe(*a[1:5])
    elif a[0] == "back":
        back()
    elif a[0] == "crop":
        name, x1, y1, x2, y2 = a[1], *map(int, a[2:6])
        src = SHOTS / f"{a[6] if len(a) > 6 else 'last'}.png"
        TPL.mkdir(exist_ok=True)
        img = cv2.imread(str(src))
        cv2.imwrite(str(TPL / f"{name}.png"), img[y1:y2, x1:x2])
        print(TPL / f"{name}.png")
    else:
        print(__doc__); sys.exit(1)


def find(img, name, thresh=0.85):
    """Return (x, y) centre of template tpl/<name>.png in img, or None."""
    t = cv2.imread(str(TPL / f"{name}.png"))
    r = cv2.matchTemplate(img, t, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(r)
    if score < thresh:
        return None
    h, w = t.shape[:2]
    return loc[0] + w // 2, loc[1] + h // 2
