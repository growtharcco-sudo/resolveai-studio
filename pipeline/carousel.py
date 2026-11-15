"""Instagram carousel maker (1080x1350 JPEG slides, the ResolveAI night look).

Usage:  python pipeline/carousel.py carousels/<id>.json          -> queue/<id>/slide1.jpg.. + post.json + sheet.png
Brief:
{
 "id": "C001_slug", "series": "5 SIGNS",
 "slides": [
   {"kind": "cover", "kicker": "SAVE THIS", "lines": ["Your stock", "records lie?"], "hl": ["lie?"], "place": "warehouse", "sub": "5 signs. Swipe."},
   {"kind": "point", "n": 1, "title": "Short headline", "body": "One or two plain sentences.", "icon": "box"},   # or "shot": "factory-home"
   ...,
   {"kind": "cta", "lines": ["See it on", "one screen."], "hl": ["one", "screen."]}
 ],
 "sources": [...], "math": [...],
 "post": {"post_at": "2026-11-21T11:00:00+05:30", "instagram_caption": "... question?\n\n#resolveai #a #b #c #d"}
}
3 to 10 slides. Same caption rules as Reels (ROUTINE.md), facts sourced the same day. No YouTube for carousels.
"""
import json, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fx

W, H = 1080, 1350
ROOT = fx.ROOT


def _bg(place, dim):
    full = fx.place(place or "office", 4)                       # 1080x1920; keep the band with the building
    bg = full.crop((0, 1920 - H - 380, W, 1920 - 380)).copy()
    bg.alpha_composite(Image.new("RGBA", (W, H), (8, 10, 22, int(255 * dim))))
    return bg


def _head(d, lines, y, hl=(), size=110, color=fx.WHITE):
    hl = {w.lower().strip(".,!?:") for w in hl}
    for ln in lines:
        f = fx.font("black", size)
        while f.getlength(ln) > W - 120: f = fx.font("black", f.size - 4)
        x = (W - f.getlength(ln)) / 2
        for wd in ln.split(" "):
            c = fx.GOLD if wd.lower().strip(".,!?:") in hl else color
            d.text((x + 3, y + 5), wd, font=f, fill=(0, 0, 0, 140)); d.text((x, y), wd, font=f, fill=c); x += f.getlength(wd + " ")
        y += int(f.size * 1.1)
    return y


def _frame(c, series, i, n):
    d = ImageDraw.Draw(c); f = fx.font("xbold", 32)
    c.alpha_composite(fx.logo(56), (60, 56)); d.text((132, 66), "RESOLVEAI", font=f, fill=fx.WHITE)
    if series:
        sw = f.getlength(series); fx.rrect(d, [W - 60 - sw - 40, 58, W - 60, 110], 26, fill=fx.GOLD + (255,)); d.text((W - 60 - sw - 20, 64), series, font=f, fill=fx.INK)
    pf = fx.font("bold", 30); t = f"{i} / {n}"; d.text((W - 60 - pf.getlength(t), H - 80), t, font=pf, fill=(200, 205, 220))
    if i < n: d.text((60, H - 80), "Swipe →", font=pf, fill=(200, 205, 220))
    else: d.text((60, H - 80), "resolveai.cc", font=pf, fill=fx.GOLD)


def slide(s, series, i, n):
    k = s["kind"]
    if k == "cover":
        c = _bg(s.get("place", "factory"), 0.35); d = ImageDraw.Draw(c)
        if s.get("kicker"): fx.paste_c(c, fx.shadow(fx.chip(s["kicker"], size=44)), W / 2, 300)
        y = _head(d, s["lines"], 380, s.get("hl", []), 130)
        if s.get("sub"):
            f = fx.font("bold", 54); tw = f.getlength(s["sub"]); x = (W - tw) / 2
            fx.rrect(d, [x - 30, y + 18, x + tw + 30, y + 98], 22, fill=(8, 10, 22, 220)); d.text((x, y + 26), s["sub"], font=f, fill=fx.WHITE)
    elif k == "point":
        c = _bg(s.get("place", "office"), 0.72); d = ImageDraw.Draw(c)
        fx.paste_c(c, fx.chip(f'{s["n"]:02d}', size=60), W / 2, 260)
        y = _head(d, wrap_lines(s["title"], 92), 350, s.get("hl", []), 92)
        if s.get("shot"):
            m = os.path.join(ROOT, f'assets/shots/{s["shot"]}-m.webp')
            if os.path.exists(m): sh = fx.shadow(fx.phone(Image.open(m), w=330))
            else: sh = fx.shadow(fx.browser(Image.open(os.path.join(ROOT, f'assets/shots/{s["shot"]}-1600.webp')), w=940))
            fx.paste_c(c, sh, W / 2, y + 40 + sh.height / 2 - 30)
        else:
            fx.paste_c(c, fx.icon(s.get("icon", "check"), 200), W / 2, y + 150)
            card = fx.shadow(fx.card(None, [s["body"]], w=920, size=48)); fx.paste_c(c, card, W / 2, y + 300 + card.height / 2 - 30)
        if s.get("shot") and s.get("body"):
            pass
    elif k == "cta":
        c = _bg(s.get("place", "city"), 0.5); d = ImageDraw.Draw(c)
        fx.paste_c(c, fx.shadow(fx.logo(180)), W / 2, 330)
        y = _head(d, s.get("lines", ["Run your business", "from one screen."]), 480, s.get("hl", []), 100)
        fx.paste_c(c, fx.shadow(fx.chip(s.get("cta", "Try a live demo: resolveai.cc"), size=46)), W / 2, y + 90)
        f = fx.font("bold", 46); t = s.get("follow", "Save this. Follow for more.")
        d.text(((W - f.getlength(t)) / 2, y + 190), t, font=f, fill=fx.WHITE)
    else:
        raise ValueError("unknown slide kind " + k)
    _frame(c, series, i, n)
    return c.convert("RGB")


def wrap_lines(text, size):
    return fx.wrap(text, fx.font("black", size), W - 140)


def check(b):
    P = []; n = len(b["slides"]); cap = b["post"]["instagram_caption"]
    if not 3 <= n <= 10: P.append("3 to 10 slides")
    if b["slides"][0]["kind"] != "cover" or b["slides"][-1]["kind"] != "cta": P.append("first slide cover, last slide cta")
    every = json.dumps(b, ensure_ascii=False)
    if "—" in every or "–" in every: P.append("no em or en dashes")
    if "small team" in every.lower(): P.append('banned phrase "small team"')
    tags = [w for w in cap.split() if w.startswith("#") and len(w) > 2 and not w[1:].isdigit()]
    if len(tags) != 5 or "#resolveai" not in [t.lower() for t in tags]: P.append("caption: exactly 5 hashtags including #resolveai")
    body = cap.rsplit("\n\n", 1)[0].strip()
    if not body.endswith("?"): P.append("caption: the line before the hashtags must be a question")
    for s in b["slides"]:
        if s["kind"] == "point":
            if len(wrap_lines(s["title"], 92)) > 3: P.append(f'slide {s["n"]}: title too long')
            if len(s.get("body", "")) > 160: P.append(f'slide {s["n"]}: body over 160 characters')
            if s.get("shot") and not any(os.path.exists(os.path.join(ROOT, f'assets/shots/{s["shot"]}-{v}.webp')) for v in ("m", "1600")): P.append(f'slide {s["n"]}: shot not found')
    for m in b.get("math", []):
        if str(eval(m["expr"], {"__builtins__": {}}, {"round": round})) != str(m["expect"]): P.append(f'math wrong: {m["expr"]} != {m["expect"]}')
    if not b.get("sources"): P.append("sources missing")
    return P


if __name__ == "__main__":
    b = json.load(open(sys.argv[1])); probs = check(b)
    if probs: print("PROBLEMS:\n  " + "\n  ".join(probs)); sys.exit(1)
    out = os.path.join(ROOT, "queue", b["id"]); os.makedirs(out, exist_ok=True)
    n = len(b["slides"]); names = []
    for i, s in enumerate(b["slides"], 1):
        im = slide(s, b.get("series", ""), i, n); nm = f"slide{i}.jpg"; im.save(os.path.join(out, nm), quality=92); names.append(nm)
    th = [Image.open(os.path.join(out, x)).resize((270, 338)) for x in names]
    sheet = Image.new("RGB", (270 * min(5, n), 338 * ((n + 4) // 5)), (0, 0, 0))
    for i, t in enumerate(th): sheet.paste(t, ((i % 5) * 270, (i // 5) * 338))
    sheet.save(os.path.join(out, "sheet.png"))
    post = {"type": "carousel", "slot": "carousel", "post_at": b["post"]["post_at"], "images": names,
            "instagram_caption": b["post"]["instagram_caption"]}
    json.dump(post, open(os.path.join(out, "post.json"), "w"), indent=1, ensure_ascii=False)
    print("ready:", os.path.relpath(out, ROOT), f"({n} slides)")
