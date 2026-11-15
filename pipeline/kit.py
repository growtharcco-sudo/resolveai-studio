"""Reel kit: brief -> spec, from fixed, tested scene layouts. Never hand-write coordinates or edit specs by hand.

Usage:  python pipeline/kit.py briefs/<id>.json      (writes specs/<id>.json, exits 1 on LAYOUT PROBLEMS)

Brief:
{
  "id": "002_slug", "series": "CASE FILE 002",                 # series = the gold label top right
  "speed": 1.15,                                               # voice is always am_liam (channel rule)
  "beats": [                                                   # one beat = one spoken phrase
    {"say": "...", "cap": "...", "pause": 0.3,                 # cap / pause optional
     "show": {"kind": "hook", ...}},                           # optional: starts a new scene at this beat
    ...],                                                      # beat 0 MUST have a show (the frame-0 hook)
  "cover": {"kicker", "big": [2 short lines], "sub", "place", "person": [role, pose]},
  "sources": [...], "math": [...], "post": {...}               # see ROUTINE.md
}
"@n" = beat n of THIS scene (0 = the beat with the show). Things that appear "in turn" use one beat each.

Places: factory | warehouse | shop | school | hospital | office | city
People: person = [role, pose, skin 0..3]; role owner|worker|clerk|doctor|teacher|staff; pose stand|stress|point|phone|happy
Icons:  box clock rupee phone chart bell check cross paper excel user truck whatsapp
Shots:  shot = "<key>-<page>"  keys/pages: factory-home|inventory|planning|production, trading-home|inventory|reports|sales,
        school-home|attendance|fees|marks, hospital-home|ipd|opd|pharmacy, hub-home|clients|pipeline|projects,
        dashboards-home, flows-home. Phone frames exist only for <key>-home with key factory|trading|school|hospital|hub.

KINDS
  hook     place, kicker (gold chip), lines [1..3] (max ~16 chars a line), hl [gold words], person, badge (red chip @1)
           Everything except the badge is on screen at frame 0.
  story    place, sub (chip), person, bubble [1..3 lines] @0, reply [1..2 lines] @1 (second bubble, right side)
  problem  place, lines [1..2] headline, hl, papers true (paper sheets fall @0), badge (red chip, @badge_at default last)
  number   to, prefix, suffix, dec, indian (true = 1,00,000 style), label (line above), sub (line below, @1), color gold|red|teal
  steps    title, steps [[icon, text], ...] up to 4 (step i appears at @i), hl index (gold edge = "the important one")
  step     n, title (1..2 lines), icon, line (card text, @1), place (optional, dimmed)
  screen   shot, device phone|browser, title [1..2 lines], hl, callout (gold chip @1)
  compare  before {title, lines [1..3]}, after {title, lines [1..3]} (@1, the before card gets struck)
  ending   lines [1..2], hl, cta (default "Try a live demo: resolveai.cc"), follow (default "Follow for more")
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fx
from fx import W, H

CAP_TOP = 1390        # nothing may sit below this (caption zone + Instagram buttons)
GROUND = 1344


def img(fn, x, y, at, anim="pop", args=(), kw=None, delay=0, **extra):
    e = {"type": "img", "make": {"fn": fn, "args": list(args), "kw": kw or {}}, "x": x, "y": y, "at": at, "anim": anim, "delay": delay}
    e.update(extra); return e


def head(lines, y, at, hl=(), size=100, delay=0, color="white"):
    return {"type": "head", "lines": lines, "hl": list(hl), "size": size, "x": W / 2, "y": y, "at": at, "delay": delay, "align": "center", "color": color}


def person_el(p, x, at, scale=1.3, anim="rise", delay=0):
    role, pose = p[0], p[1] if len(p) > 1 else "stand"; skin = p[2] if len(p) > 2 else 1
    h = int(620 * scale)
    return img("person", x, GROUND + 40 - h / 2, at, anim, args=[role, pose, skin], kw={"scale": scale}, delay=delay, float=0)


def block(kind, s, b, nb):
    def at(n=0): return b + min(n, nb - 1)
    first = -1 if b == 0 else at()
    els = []; sc = {"place": s.get("place"), "dim": 0.0}
    if kind == "hook":
        if s.get("kicker"): els.append(img("chip", W / 2, 300, first, "pop", args=[s["kicker"]], kw={"size": 42}))
        els.append(head(s["lines"], 370, first, s.get("hl", []), s.get("size", 104)))
        if s.get("person"): els.append(person_el(s["person"], s.get("person_x", 760), first))
        if s.get("badge"): els.append(img("chip", 330, 1180, at(s.get("badge_at", 1)), "pop", args=[s["badge"]], kw={"size": 50, "bg": fx.RED, "fg": fx.WHITE}, delay=0.3))
        sc["dim"] = 0.15
    elif kind == "story":
        if s.get("sub"): els.append(img("chip", W / 2, 300, first, "pop", args=[s["sub"]], kw={"size": 40}))
        if s.get("person"): els.append(person_el(s["person"], s.get("person_x", 280), first))
        if s.get("bubble"): els.append(img("bubble", 640, 700, at(0), "pop", args=[s["bubble"]], kw={"w": 700, "tail": "left"}, delay=0.35))
        if s.get("reply"):
            els.append(img("bubble", 520, 1020, at(1), "pop", args=[s["reply"]], kw={"w": 640, "tail": "right", "bg": fx.GOLD}, delay=0.2))
    elif kind == "problem":
        els.append(head(s["lines"], 300, first, s.get("hl", []), s.get("size", 96)))
        if s.get("papers", True): els.append({"type": "papers", "n": 14, "at": at(0), "delay": 0.4, "y0": 820, "y1": 1260})
        if s.get("badge"): els.append(img("chip", W / 2, 1150, at(s.get("badge_at", nb - 1)), "pop", args=[s["badge"]], kw={"size": 56, "bg": fx.RED, "fg": fx.WHITE}, delay=0.3))
        sc["dim"] = 0.35
    elif kind == "number":
        if s.get("label"): els.append(head([s["label"]] if isinstance(s["label"], str) else s["label"], 470, first, s.get("hl", []), 76))
        els.append({"type": "count", "to": s["to"], "prefix": s.get("prefix", ""), "suffix": s.get("suffix", ""), "dec": s.get("dec", 0),
                    "indian": s.get("indian", False), "size": s.get("size", 210), "x": W / 2, "y": 700, "color": s.get("color", "gold"),
                    "at": first if b == 0 else at(), "delay": 0.15, "dur": 1.1})
        if s.get("sub"): els.append(head([s["sub"]] if isinstance(s["sub"], str) else s["sub"], 1040, at(1), [], 60, delay=0.1))
        sc["dim"] = 0.62; sc["place"] = s.get("place", "city")
    elif kind == "steps":
        els.append(head([s["title"]] if isinstance(s["title"], str) else s["title"], 290, first, s.get("hl_words", []), 84))
        n = len(s["steps"][:4]); y0 = 600
        for i, (ic, tx) in enumerate(s["steps"][:4]):
            y = y0 + i * 200; a = at(i)
            gold = s.get("hl") == i
            els.append(img("card", W / 2 + 60, y, a, "left", args=[None, [tx]], kw={"w": 800, "size": 52, "accent": fx.GOLD if gold else fx.TEAL, "dark": not gold}, delay=0.15))
            els.append(img("icon", 150, y, a, "pop", args=[ic], kw={"size": 130, "bg": fx.GOLD if gold else fx.TEAL}, delay=0.05))
        sc["dim"] = 0.6; sc["place"] = s.get("place", "office")
    elif kind == "step":
        els.append(img("chip", W / 2, 300, first, "pop", args=[f'STEP {s["n"]}'], kw={"size": 50}))
        els.append(head(s["title"] if isinstance(s["title"], list) else [s["title"]], 380, first, s.get("hl", []), 96))
        els.append(img("icon", W / 2, 830, first, "pop", args=[s.get("icon", "check")], kw={"size": 260}, delay=0.2))
        if s.get("line"): els.append(img("card", W / 2, 1150, at(1), "rise", args=[None, [s["line"]]], kw={"w": 900, "size": 52}, delay=0.1))
        sc["dim"] = 0.55; sc["place"] = s.get("place", "office")
    elif kind == "screen":
        els.append(head(s["title"] if isinstance(s["title"], list) else [s["title"]], 230, first, s.get("hl", []), 80))
        shot = f'assets/shots/{s["shot"]}-{"m" if s.get("device", "phone") == "phone" else "1600"}.webp'
        if s.get("device", "phone") == "phone":
            els.append(img("phone", W / 2, 850, first, "rise", args=[shot], kw={"w": 460}, delay=0.1))
        else:
            els.append(img("browser", W / 2, 860, first, "rise", args=[shot], kw={"w": 960}, delay=0.1))
        if s.get("callout"): els.append(img("chip", W / 2, 1315, at(1), "pop", args=[s["callout"]], kw={"size": 46}, delay=0.2))
        sc["dim"] = 0.7; sc["place"] = s.get("place", "office")
    elif kind == "compare":
        bf, af = s["before"], s["after"]
        els.append(img("card", W / 2, 600, first, "rise", args=[bf.get("title", "BEFORE"), bf["lines"]], kw={"w": 900, "accent": fx.RED, "size": 54}))
        els.append(img("card", W / 2, 1050, at(1), "rise", args=[af.get("title", "AFTER"), af["lines"]], kw={"w": 900, "accent": fx.TEAL, "size": 54}, delay=0.2))
        sc["dim"] = 0.55; sc["place"] = s.get("place", "office")
    elif kind == "ending":
        els.append(img("logo", W / 2, 420, first, "pop", kw={"size": 190}))
        els.append(head(s.get("lines", ["Run your business", "from one screen."]), 600, first, s.get("hl", []), 90, delay=0.2))
        els.append(img("chip", W / 2, 1000, at(0), "pop", args=[s.get("cta", "Try a live demo: resolveai.cc")], kw={"size": 46}, delay=0.6))
        els.append(head([s.get("follow", "Follow for more")], 1120, at(min(1, nb - 1)), [], 56, delay=0.3))
        sc["dim"] = 0.55; sc["place"] = s.get("place", "city"); sc["no_caps"] = True
    else:
        raise ValueError("unknown scene kind: " + kind)
    sc["els"] = els
    return sc


def build_spec(brief):
    beats = brief["beats"]
    starts = [i for i, bt in enumerate(beats) if bt.get("show")]
    if not starts or starts[0] != 0: raise ValueError("beat 0 must have a 'show' (the hook frame)")
    phrases = []
    for i, bt in enumerate(beats):
        ph = {"say": bt["say"], "cap": bt.get("cap", bt["say"])}
        ph["pause"] = bt.get("pause", 0.35 if (i + 1 in starts or i == len(beats) - 1) else 0.18); phrases.append(ph)
    scenes = []
    for k, b in enumerate(starts):
        nxt = starts[k + 1] if k + 1 < len(starts) else len(beats); sh = beats[b]["show"]
        sc = block(sh["kind"], sh, b, nxt - b); sc.update(until=nxt if k + 1 < len(starts) else "end", kind=sh["kind"], seed=3 + k)
        scenes.append(sc)
    spec = {"id": brief["id"], "series": brief.get("series", "RESOLVEAI"), "voice": "am_liam", "speed": brief.get("speed", 1.15),
            "header": brief.get("series", ""), "phrases": phrases, "scenes": scenes}
    for k in ("cover", "sources", "post", "math"): spec[k] = brief.get(k, [] if k in ("sources", "math") else {})
    return spec


def layout_check(spec):
    import engine
    P = []
    for k, sc in enumerate(spec["scenes"]):
        for e in sc["els"]:
            if e["type"] == "head":
                f = fx.font(e.get("weight", "black"), e["size"])
                for ln in e["lines"]:
                    if f.getlength(ln) > 980: P.append(f'scene {k} ({sc["kind"]}): headline line too wide ({int(f.getlength(ln))}px > 980): "{ln}"')
                bottom = e["y"] + len(e["lines"]) * e["size"] * 1.12
                if bottom > CAP_TOP: P.append(f'scene {k} ({sc["kind"]}): headline runs into the captions')
            elif e["type"] == "img":
                im = engine.el_image(e); sw = im.width * e.get("scale", 1)
                if e["make"]["fn"] in ("chip", "card", "bubble", "phone", "browser") and sw - 60 > W:
                    P.append(f'scene {k} ({sc["kind"]}): {e["make"]["fn"]} too wide ({int(sw)}px): {e["make"]["args"][:2]}')
                if e["make"]["fn"] == "chip" and im.width - 60 > 1000: P.append(f'scene {k}: chip text too long: {e["make"]["args"][0]}')
                bot = e["y"] + im.height / 2 - 40
                if e["make"]["fn"] not in ("person",) and bot > CAP_TOP + 20: P.append(f'scene {k} ({sc["kind"]}): {e["make"]["fn"]} runs into the captions (bottom {int(bot)}px)')
                if e["make"]["fn"] == "card" and len(e["make"]["args"][1]) > 4: P.append(f"scene {k}: card has more than 4 lines")
                if e["make"]["fn"] in ("phone", "browser") and not os.path.exists(os.path.join(fx.ROOT, e["make"]["args"][0])):
                    P.append(f'scene {k}: screenshot not found: {e["make"]["args"][0]}')
            elif e["type"] == "count":
                f = fx.font("black", e["size"]); txt = f'{e.get("prefix", "")}{e["to"]:,.{e.get("dec", 0)}f}{e.get("suffix", "")}'
                if f.getlength(txt) > 1000: P.append(f"scene {k}: number too wide: {txt}")
        # stacked items in a scene must not overlap: compare boxes of heads/cards/chips/bubbles
        boxes = []
        for e in sc["els"]:
            if e["type"] == "img" and e["make"]["fn"] in ("card", "chip", "bubble", "phone", "browser", "icon", "logo"):
                im = engine.el_image(e); boxes.append((e["make"]["fn"], e["x"] - im.width / 2 + 40, e["y"] - im.height / 2 + 40, e["x"] + im.width / 2 - 40, e["y"] + im.height / 2 - 50, e))
            elif e["type"] == "head":
                f = fx.font("black", e["size"]); w_ = max(f.getlength(l) for l in e["lines"])
                boxes.append(("headline", W / 2 - w_ / 2, e["y"], W / 2 + w_ / 2, e["y"] + len(e["lines"]) * e["size"] * 1.12 - 10, e))
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b2 = boxes[i], boxes[j]
                if a[0] == "icon" or b2[0] == "icon": continue
                if a[5].get("out_at") is not None or b2[5].get("out_at") is not None: continue
                if a[1] < b2[3] and b2[1] < a[3] and a[2] < b2[4] and b2[2] < a[4]:
                    P.append(f'scene {k} ({sc["kind"]}): {a[0]} overlaps {b2[0]} (shorten the text)')
    n = len(spec["phrases"])
    for k, sc in enumerate(spec["scenes"]):
        for e in sc["els"]:
            if e.get("at", -1) >= n: P.append(f"scene {k}: element timed after the last beat")
    return P


if __name__ == "__main__":
    brief = json.load(open(sys.argv[1])); spec = build_spec(brief)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "specs", f'{spec["id"]}.json'); os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(spec, open(out, "w"), indent=1, ensure_ascii=False)
    print("wrote", os.path.relpath(out, root))
    probs = layout_check(spec)
    if probs: print("LAYOUT PROBLEMS:\n  " + "\n  ".join(probs)); sys.exit(1)
    print("layout ok")
