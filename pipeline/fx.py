"""Drawing blocks for the ResolveAI look: flat-vector illustrated scenes (factory at night, warehouse, school,
hospital, office, shop), simple flat characters, cards, chips, icons and phone/browser frames.

Everything is drawn at 2x and scaled down once (cached by the engine), so edges are smooth.
Do not change the look unless the owner asks.
"""
import math, os, random
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------- brand palette ----------------
PAPER = (247, 246, 242); INK = (10, 10, 10); GOLD = (201, 162, 39); MUTED = (109, 109, 109)
NIGHT = (16, 24, 48); NIGHT2 = (27, 38, 72); NAVY = (36, 50, 92); STEEL = (64, 80, 122)
WINDOW = (255, 200, 87); RED = (228, 87, 46); TEAL = (46, 196, 182); WHITE = (255, 255, 255)
SKIN = [(241, 194, 156), (205, 150, 110), (160, 110, 75), (120, 80, 55)]
SHIRT = {"owner": (201, 162, 39), "worker": (46, 120, 196), "clerk": (180, 90, 140), "doctor": (240, 240, 240),
         "teacher": (90, 150, 90), "staff": (46, 196, 182)}
COLORS = {"ink": INK, "gold": GOLD, "red": RED, "teal": TEAL, "white": WHITE, "paper": PAPER, "muted": MUTED, "night": NIGHT}


def col(c): return COLORS[c] if isinstance(c, str) else tuple(c)


# ---------------- fonts ----------------
FONT_PATH = os.path.join(ROOT, "assets", "fonts", "InterTight.ttf")
WEIGHTS = {"black": 900, "xbold": 800, "bold": 700, "semi": 600, "med": 500, "reg": 400}


@lru_cache(maxsize=256)
def font(weight="bold", size=60):
    f = ImageFont.truetype(FONT_PATH, int(size))
    try: f.set_variation_by_axes([WEIGHTS.get(weight, 700)])
    except Exception: pass
    return f


def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if f.getlength(t) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines


# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, t0, dur): return clamp((t - t0) / dur) if dur > 0 else (1.0 if t >= t0 else 0.0)
def ease_out(p): return 1 - (1 - p) ** 3
def smooth(p): return p * p * (3 - 2 * p)
def ease_back(p, s=1.7):
    p -= 1; return 1 + (s + 1) * p ** 3 + s * p ** 2


# ---------------- pasting ----------------
def paste_c(c, im, x, y, scale=1.0, alpha=1.0):
    """Paste RGBA im centred at (x, y) on c, scaled and faded."""
    if alpha <= 0.003 or scale <= 0.01: return
    if abs(scale - 1) > 0.004:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 0.997:
        im = im.copy(); a = im.getchannel("A").point(lambda v: int(v * alpha)); im.putalpha(a)
    c.alpha_composite(im, (int(round(x - im.width / 2)), int(round(y - im.height / 2)))) if _inside(c, im, x, y) else _paste_clip(c, im, x, y)


def _inside(c, im, x, y):
    x0, y0 = int(round(x - im.width / 2)), int(round(y - im.height / 2))
    return x0 >= 0 and y0 >= 0 and x0 + im.width <= c.width and y0 + im.height <= c.height


def _paste_clip(c, im, x, y):
    x0, y0 = int(round(x - im.width / 2)), int(round(y - im.height / 2))
    sx0, sy0 = max(0, -x0), max(0, -y0); dx0, dy0 = max(0, x0), max(0, y0)
    w = min(im.width - sx0, c.width - dx0); h = min(im.height - sy0, c.height - dy0)
    if w <= 0 or h <= 0: return
    c.alpha_composite(im.crop((sx0, sy0, sx0 + w, sy0 + h)), (dx0, dy0))


def down(im):  # 2x -> 1x
    return im.resize((im.width // 2, im.height // 2), Image.LANCZOS)


def shadow(im, r=18, off=(0, 14), a=90):
    pad = r * 2 + max(abs(off[0]), abs(off[1]))
    out = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    mask = im.getchannel("A").point(lambda v: int(v * a / 255))
    sh.paste((0, 0, 0, 255), (pad + off[0], pad + off[1]), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(r))
    out.alpha_composite(sh); out.alpha_composite(im, (pad, pad))
    return out


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


# ---------------- sky + ground ----------------
def _sky(w, h, top=NIGHT, bot=NIGHT2, seed=1):
    im = Image.new("RGBA", (w, h)); d = ImageDraw.Draw(im)
    for y in range(h):
        f = y / max(1, h - 1); d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * f) for a, b in zip(top, bot)) + (255,))
    rng = random.Random(seed)
    for _ in range(70):
        x, y, r = rng.randint(0, w), rng.randint(0, int(h * 0.45)), rng.choice([2, 2, 3, 4])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rng.randint(90, 200)))
    mx, my = int(w * 0.8), int(h * 0.12)
    d.ellipse([mx - 70, my - 70, mx + 70, my + 70], fill=(255, 240, 200, 255))
    d.ellipse([mx - 40, my - 85, mx + 100, my + 55], fill=top + (255,))
    return im


def _windows(d, x0, y0, cols, rows, ww, wh, gx, gy, rng, lit=0.75):
    for r in range(rows):
        for c in range(cols):
            on = rng.random() < lit
            x, y = x0 + c * (ww + gx), y0 + r * (wh + gy)
            rrect(d, [x, y, x + ww, y + wh], 6, fill=WINDOW + (255,) if on else (44, 58, 100, 255))


# ---------------- places (full 1080x1920 backgrounds, drawn at 2x) ----------------
def place(name, seed=3):
    """Illustrated background. name: factory|warehouse|shop|school|hospital|office|city|desk."""
    S = 2; w, h = W * S, H * S; rng = random.Random(seed)
    im = _sky(w, h, seed=seed); d = ImageDraw.Draw(im)
    gy = int(h * 0.70)                                        # ground line
    # far skyline
    x = 0
    while x < w:
        bw, bh = rng.randint(140, 300), rng.randint(300, 760)
        d.rectangle([x, gy - bh, x + bw, gy], fill=(30, 42, 80, 255)); x += bw + rng.randint(10, 40)
    if name == "factory":
        d.rectangle([160, gy - 900, 1960, gy], fill=NAVY + (255,))
        for i in range(6):                                    # saw-tooth roof
            x0 = 160 + i * 300
            d.polygon([(x0, gy - 900), (x0 + 300, gy - 900), (x0 + 300, gy - 1120)], fill=STEEL + (255,))
            d.polygon([(x0 + 300, gy - 1120), (x0 + 300, gy - 900), (x0 + 280, gy - 900), (x0 + 280, gy - 1090)], fill=(255, 220, 140, 255))
        for cx in (360, 620):                                 # chimneys
            d.rectangle([cx, gy - 1500, cx + 110, gy - 900], fill=(52, 66, 108, 255))
            d.rectangle([cx, gy - 1460, cx + 110, gy - 1420], fill=RED + (255,))
        _windows(d, 260, gy - 760, 8, 3, 150, 110, 64, 70, rng, 0.8)
        rrect(d, [1500, gy - 420, 1860, gy], 12, fill=(24, 32, 60, 255))           # loading door
        for i in range(6): d.line([(1500, gy - 400 + i * 66), (1860, gy - 400 + i * 66)], fill=(60, 76, 120, 255), width=6)
        _sign(d, 760, gy - 860, "FACTORY")
    elif name == "warehouse":
        d.polygon([(120, gy - 820), (1040, gy - 1180), (1960, gy - 820)], fill=STEEL + (255,))
        d.rectangle([120, gy - 820, 1960, gy], fill=NAVY + (255,))
        for sx in (220, 1100):
            for r in range(3):
                yy = gy - 700 + r * 220
                d.rectangle([sx, yy + 170, sx + 760, yy + 186], fill=(110, 125, 165, 255))
                xx = sx + 20
                while xx < sx + 720:
                    bw = rng.randint(90, 150); bh = rng.randint(90, 160)
                    d.rectangle([xx, yy + 170 - bh, xx + bw, yy + 170], fill=(rng.randint(170, 200), rng.randint(125, 145), 80, 255))
                    d.line([(xx, yy + 170 - bh + 20), (xx + bw, yy + 170 - bh + 20)], fill=(140, 100, 60, 255), width=5)
                    xx += bw + rng.randint(10, 30)
        _sign(d, 800, gy - 900, "WAREHOUSE")
    elif name == "shop":
        d.rectangle([240, gy - 900, 1840, gy], fill=NAVY + (255,))
        for i in range(8):                                    # awning
            d.rectangle([240 + i * 200, gy - 900, 440 + i * 200, gy - 760], fill=(RED if i % 2 == 0 else WHITE) + (255,))
        rrect(d, [340, gy - 680, 1200, gy - 120], 16, fill=WINDOW + (255,))
        for i in range(4):
            d.rectangle([380, gy - 640 + i * 130, 1160, gy - 628 + i * 130], fill=(150, 110, 60, 255))
        rrect(d, [1360, gy - 680, 1700, gy], 12, fill=(24, 32, 60, 255))
        _sign(d, 840, gy - 1060, "TRADERS")
    elif name == "school":
        d.rectangle([200, gy - 860, 1880, gy], fill=(150, 70, 60, 255))
        d.polygon([(860, gy - 860), (1040, gy - 1240), (1220, gy - 860)], fill=(120, 55, 48, 255))
        d.ellipse([970, gy - 1130, 1110, gy - 990], fill=WHITE + (255,)); d.line([(1040, gy - 1060), (1040, gy - 1110)], fill=INK + (255,), width=8)
        d.line([(1040, gy - 1060), (1080, gy - 1060)], fill=INK + (255,), width=8)
        _windows(d, 290, gy - 740, 7, 2, 160, 150, 70, 90, rng, 0.85)
        rrect(d, [940, gy - 330, 1140, gy], 10, fill=(60, 30, 26, 255))
        _sign(d, 760, gy - 960, "SCHOOL")
    elif name == "hospital":
        d.rectangle([260, gy - 1100, 1820, gy], fill=(225, 232, 245, 255))
        _windows(d, 340, gy - 1000, 7, 4, 150, 120, 60, 70, rng, 0.7)
        d.rectangle([980, gy - 1300, 1100, gy - 1100], fill=RED + (255,)); d.rectangle([920, gy - 1240, 1160, gy - 1160], fill=RED + (255,))
        rrect(d, [880, gy - 300, 1200, gy], 10, fill=(70, 110, 160, 255))
    elif name in ("office", "desk"):
        im = Image.new("RGBA", (w, h), (34, 44, 78, 255)); d = ImageDraw.Draw(im)
        d.rectangle([0, gy + 120, w, h], fill=(28, 36, 64, 255))
        rrect(d, [180, 260, 1160, 1000], 24, fill=(20, 30, 60, 255))                # window with city
        for i in range(9):
            bh = rng.randint(200, 600); d.rectangle([200 + i * 104, 980 - bh, 280 + i * 104, 980], fill=(44, 58, 100, 255))
            for k in range(0, bh - 60, 70): d.rectangle([220 + i * 104, 1000 - bh + k + 30, 260 + i * 104, 1000 - bh + k + 60], fill=WINDOW + (220,))
        rrect(d, [1360, 360, 1860, 760], 16, fill=(60, 74, 120, 255))                # wall board
        for i in range(4): d.rectangle([1410, 420 + i * 80, 1410 + rng.randint(200, 400), 450 + i * 80], fill=(120, 136, 180, 255))
        d.rectangle([80, gy + 40, w - 80, gy + 120], fill=(120, 86, 56, 255))         # desk top
        d.rectangle([140, gy + 120, 200, h], fill=(90, 64, 42, 255)); d.rectangle([w - 200, gy + 120, w - 140, h], fill=(90, 64, 42, 255))
        return down(im)
    else:  # city
        for i in range(10):
            bw, bh = rng.randint(160, 260), rng.randint(700, 1400); x0 = i * 210 + rng.randint(-20, 20)
            d.rectangle([x0, gy - bh, x0 + bw, gy], fill=NAVY + (255,))
            _windows(d, x0 + 20, gy - bh + 40, max(1, (bw - 40) // 60), bh // 110, 40, 60, 20, 50, rng, 0.6)
    d.rectangle([0, gy, w, h], fill=(22, 30, 56, 255))      # ground
    d.rectangle([0, gy, w, gy + 16], fill=(70, 86, 130, 255))
    return down(im)


def _sign(d, x, y, text):
    f = font("black", 76); tw = f.getlength(text)
    rrect(d, [x - 30, y - 20, x + tw + 30, y + 100], 16, fill=GOLD + (255,))
    d.text((x, y - 6), text, font=f, fill=INK + (255,))


# ---------------- characters ----------------
def person(role="owner", pose="stand", skin=1, scale=1.0, hair=(30, 24, 20)):
    """Flat character, ~520px tall at scale 1. pose: stand|stress|point|phone|happy."""
    S = 2; w, h = 420 * S, 620 * S; im = Image.new("RGBA", (w, h)); d = ImageDraw.Draw(im)
    sk = SKIN[skin % len(SKIN)] + (255,); sh = SHIRT.get(role, GOLD) + (255,)
    cx = w // 2
    d.rounded_rectangle([cx - 70, 900, cx - 18, 1220], 24, fill=(34, 40, 70, 255))      # legs
    d.rounded_rectangle([cx + 18, 900, cx + 70, 1220], 24, fill=(34, 40, 70, 255))
    d.rounded_rectangle([cx - 90, 1200, cx - 10, 1236], 16, fill=(20, 20, 24, 255)); d.rounded_rectangle([cx + 10, 1200, cx + 90, 1236], 16, fill=(20, 20, 24, 255))
    d.rounded_rectangle([cx - 140, 470, cx + 140, 940], 90, fill=sh)                   # torso
    if role == "doctor": d.rectangle([cx - 8, 480, cx + 8, 930], fill=(200, 205, 215, 255))
    if role in ("owner", "clerk"): d.polygon([(cx - 30, 480), (cx + 30, 480), (cx, 600)], fill=WHITE + (255,))
    arm = lambda a, b: d.line([a, b], fill=sh, width=64, joint="curve")
    hand = lambda p: d.ellipse([p[0] - 34, p[1] - 34, p[0] + 34, p[1] + 34], fill=sk)
    L0, R0 = (cx - 120, 540), (cx + 120, 540)
    if pose == "stress":
        for s, p0 in ((-1, L0), (1, R0)):
            e = (cx + s * 210, 420); t = (cx + s * 90, 250); arm(p0, e); arm(e, t); hand(t)
    elif pose == "point":
        arm(L0, (cx - 160, 760)); hand((cx - 160, 790)); e = (cx + 250, 470); arm(R0, e); hand((e[0] + 40, e[1] - 20))
    elif pose == "phone":
        arm(L0, (cx - 160, 760)); hand((cx - 160, 790)); e = (cx + 180, 720); arm(R0, e); t = (cx + 70, 600); arm(e, t)
        d.rounded_rectangle([t[0] - 40, t[1] - 90, t[0] + 40, t[1] + 50], 14, fill=(20, 20, 24, 255))
        d.rounded_rectangle([t[0] - 32, t[1] - 80, t[0] + 32, t[1] + 38], 10, fill=TEAL + (255,)); hand((t[0] + 10, t[1] + 30))
    elif pose == "happy":
        for s, p0 in ((-1, L0), (1, R0)):
            e = (cx + s * 230, 380); t = (cx + s * 200, 200); arm(p0, e); arm(e, t); hand(t)
    else:
        arm(L0, (cx - 170, 780)); hand((cx - 170, 810)); arm(R0, (cx + 170, 780)); hand((cx + 170, 810))
    d.rectangle([cx - 30, 400, cx + 30, 480], fill=sk)                                  # neck
    d.ellipse([cx - 120, 160, cx + 120, 430], fill=sk)                                  # head
    d.chord([cx - 128, 140, cx + 128, 380], 180, 360, fill=hair + (255,))               # hair
    d.ellipse([cx - 60, 280, cx - 36, 306], fill=(20, 20, 24, 255)); d.ellipse([cx + 36, 280, cx + 60, 306], fill=(20, 20, 24, 255))
    if pose == "stress": d.arc([cx - 40, 340, cx + 40, 400], 200, 340, fill=(90, 40, 30, 255), width=8)
    else: d.arc([cx - 40, 320, cx + 40, 380], 20, 160, fill=(90, 40, 30, 255), width=8)
    if role == "doctor":
        d.arc([cx - 70, 470, cx + 70, 640], 0, 180, fill=(60, 60, 70, 255), width=10)
    im = down(im)
    if scale != 1: im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    return im


# ---------------- UI pieces ----------------
def chip(text, bg=GOLD, fg=INK, size=40, pad=(30, 14)):
    f = font("xbold", size); tw = f.getlength(text); bb = f.getbbox(text)
    w_, h_ = int(tw + pad[0] * 2), int(bb[3] + pad[1] * 2)
    im = Image.new("RGBA", (w_ * 2, h_ * 2)); d = ImageDraw.Draw(im)
    rrect(d, [0, 0, w_ * 2 - 1, h_ * 2 - 1], h_, fill=col(bg) + (255,))
    d.text((pad[0] * 2, pad[1] * 2 - 2), text, font=font("xbold", size * 2), fill=col(fg) + (255,))
    return down(im)


def bubble(lines, w=640, tail="left", bg=WHITE, fg=INK, size=48):
    f = font("bold", size); ls = []
    for ln in lines: ls += wrap(ln, f, w - 80)
    lh = int(size * 1.28); h_ = 60 + lh * len(ls) + 40
    S = 2; im = Image.new("RGBA", (w * S, (h_ + 50) * S)); d = ImageDraw.Draw(im)
    rrect(d, [0, 0, w * S - 1, h_ * S], 44 * S, fill=col(bg) + (255,))
    tx = 120 * S if tail == "left" else (w - 120) * S
    d.polygon([(tx - 40 * S, h_ * S - 4), (tx + 40 * S, h_ * S - 4), (tx + (-50 if tail == "left" else 50) * S, (h_ + 48) * S)], fill=col(bg) + (255,))
    f2 = font("bold", size * S)
    for i, ln in enumerate(ls): d.text((40 * S, (40 + i * lh) * S), ln, font=f2, fill=col(fg) + (255,))
    return down(im)


def card(title, lines, w=900, accent=GOLD, size=50, title_size=40, red=(), dark=False):
    """White (or dark) rounded card: small title in accent colour, then lines."""
    f = font("bold", size); ft = font("xbold", title_size); ls = []
    for i, ln in enumerate(lines):
        for x in wrap(ln, f, w - 100): ls.append((x, i in red))
    lh = int(size * 1.3); h_ = 60 + (title_size + 30 if title else 0) + lh * len(ls) + 40
    S = 2; im = Image.new("RGBA", (w * S, h_ * S)); d = ImageDraw.Draw(im)
    bg = (22, 30, 58) if dark else WHITE; fg = WHITE if dark else INK
    rrect(d, [0, 0, w * S - 1, h_ * S - 1], 40 * S, fill=bg + (255,))
    rrect(d, [0, 0, 18 * S, h_ * S - 1], 9 * S, fill=col(accent) + (255,))
    y = 50
    if title:
        d.text((60 * S, y * S), title.upper(), font=font("xbold", title_size * S), fill=col(accent) + (255,)); y += title_size + 30
    for i, (ln, isred) in enumerate(ls):
        d.text((60 * S, (y + i * lh) * S), ln, font=font("bold", size * S), fill=(RED if isred else fg) + (255,))
    return down(im)


def icon(name, size=150, color=INK, bg=GOLD):
    """Round badge with a simple icon. name: box|clock|rupee|phone|chart|bell|check|cross|paper|user|truck|whatsapp|excel"""
    S = 4; s = size * S; im = Image.new("RGBA", (s, s)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], fill=col(bg) + (255,)); c = col(color) + (255,); m = s / 2; u = s / 10; lw = int(u * 0.7)
    if name == "box":
        d.polygon([(m, 2.3 * u), (7.6 * u, 3.6 * u), (m, 5 * u), (2.4 * u, 3.6 * u)], outline=c, width=lw)
        d.line([(2.4 * u, 3.6 * u), (2.4 * u, 6.6 * u), (m, 8 * u), (7.6 * u, 6.6 * u), (7.6 * u, 3.6 * u)], fill=c, width=lw, joint="curve")
        d.line([(m, 5 * u), (m, 8 * u)], fill=c, width=lw)
    elif name == "clock":
        d.ellipse([2.3 * u, 2.3 * u, 7.7 * u, 7.7 * u], outline=c, width=lw); d.line([(m, 3.4 * u), (m, m), (6.4 * u, 6 * u)], fill=c, width=lw, joint="curve")
    elif name == "rupee":
        f = font("black", int(6.4 * u)); d.text((m - f.getlength("₹") / 2, 1.6 * u), "₹", font=f, fill=c)
    elif name in ("phone", "whatsapp"):
        d.rounded_rectangle([3.4 * u, 2 * u, 6.6 * u, 8 * u], u * 0.7, outline=c, width=lw); d.line([(4.6 * u, 7 * u), (5.4 * u, 7 * u)], fill=c, width=lw)
        if name == "whatsapp": d.ellipse([5.6 * u, 1.4 * u, 8.2 * u, 4 * u], fill=(37, 211, 102, 255))
    elif name == "chart":
        for i, hh in enumerate((2.2, 3.6, 5.2)): d.rectangle([(2.6 + i * 1.8) * u, (7.6 - hh) * u, (3.8 + i * 1.8) * u, 7.6 * u], fill=c)
    elif name == "bell":
        d.chord([2.8 * u, 2.4 * u, 7.2 * u, 8.6 * u], 180, 360, fill=c); d.rectangle([2.6 * u, 5.4 * u, 7.4 * u, 6.6 * u], fill=c)
        d.ellipse([4.4 * u, 6.6 * u, 5.6 * u, 7.8 * u], fill=c)
    elif name == "check":
        d.line([(2.8 * u, 5.2 * u), (4.4 * u, 6.8 * u), (7.4 * u, 3.4 * u)], fill=c, width=int(lw * 1.4), joint="curve")
    elif name == "cross":
        d.line([(3 * u, 3 * u), (7 * u, 7 * u)], fill=c, width=int(lw * 1.4)); d.line([(7 * u, 3 * u), (3 * u, 7 * u)], fill=c, width=int(lw * 1.4))
    elif name in ("paper", "excel"):
        d.rounded_rectangle([3 * u, 2.2 * u, 7 * u, 7.8 * u], u * 0.4, outline=c, width=lw)
        for i in range(3): d.line([(3.8 * u, (3.6 + i * 1.2) * u), (6.2 * u, (3.6 + i * 1.2) * u)], fill=c, width=int(lw * 0.7))
        if name == "excel": d.rectangle([2.2 * u, 5.2 * u, 4.6 * u, 7.4 * u], fill=(33, 115, 70, 255))
    elif name == "user":
        d.ellipse([3.8 * u, 2.2 * u, 6.2 * u, 4.6 * u], fill=c); d.chord([2.6 * u, 5 * u, 7.4 * u, 9.6 * u], 180, 360, fill=c)
    elif name == "truck":
        d.rectangle([1.8 * u, 3.4 * u, 5.8 * u, 6.6 * u], fill=c); d.polygon([(5.8 * u, 4.2 * u), (7.4 * u, 4.2 * u), (8.2 * u, 5.4 * u), (8.2 * u, 6.6 * u), (5.8 * u, 6.6 * u)], fill=c)
        for x in (3.2, 6.8): d.ellipse([(x - 0.8) * u, 6 * u, (x + 0.8) * u, 7.6 * u], fill=col(bg) + (255,), outline=c, width=lw)
    return im.resize((size, size), Image.LANCZOS)


def phone(shot, w=560):
    """Phone frame with a real product screenshot (mobile, 390x664 aspect)."""
    S = 2; pw = w * S; ph = int((pw - 44 * S) * shot.height / shot.width) + 44 * S; im = Image.new("RGBA", (pw, ph)); d = ImageDraw.Draw(im)
    rrect(d, [0, 0, pw - 1, ph - 1], 90 * S, fill=(14, 14, 18, 255))
    sx0, sy0, sx1, sy1 = 22 * S, 22 * S, pw - 22 * S, ph - 22 * S
    sc = shot.convert("RGBA"); sw, sh = sx1 - sx0, sy1 - sy0
    sc = sc.resize((sw, int(sc.height * sw / sc.width)), Image.LANCZOS).crop((0, 0, sw, sh))
    mask = Image.new("L", (sw, sh), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw - 1, sh - 1], 70 * S, fill=255)
    im.paste(sc, (sx0, sy0), mask)
    rrect(d, [pw / 2 - 90 * S, 40 * S, pw / 2 + 90 * S, 76 * S], 18 * S, fill=(14, 14, 18, 255))
    return down(im)


def browser(shot, w=960):
    """Browser frame with a desktop screenshot."""
    S = 2; bw = w * S; sc = shot.convert("RGBA"); sc = sc.resize((bw, int(sc.height * bw / sc.width)), Image.LANCZOS)
    bar = 56 * S; im = Image.new("RGBA", (bw, sc.height + bar)); d = ImageDraw.Draw(im)
    rrect(d, [0, 0, bw - 1, sc.height + bar - 1], 26 * S, fill=(236, 236, 234, 255))
    for i, cc in enumerate(((237, 106, 94), (245, 191, 79), (98, 197, 84))):
        d.ellipse([(24 + i * 34) * S, 18 * S, (44 + i * 34) * S, 38 * S], fill=cc + (255,))
    mask = Image.new("L", sc.size, 255); ImageDraw.Draw(mask).rectangle([0, sc.height - 26 * S, bw, sc.height], fill=255)
    im.paste(sc, (0, bar))
    m2 = Image.new("L", im.size, 0); ImageDraw.Draw(m2).rounded_rectangle([0, 0, im.width - 1, im.height - 1], 26 * S, fill=255)
    out = Image.new("RGBA", im.size); out.paste(im, (0, 0), m2)
    return down(out)


def paper_sheet(seed=0, w=260):
    rng = random.Random(seed); S = 2; h = int(w * 1.3)
    im = Image.new("RGBA", (w * S, h * S)); d = ImageDraw.Draw(im)
    rrect(d, [0, 0, w * S - 1, h * S - 1], 10 * S, fill=(250, 248, 240, 255))
    for i in range(7):
        y = (40 + i * 34) * S; d.line([(30 * S, y), ((30 + rng.randint(120, w - 60)) * S, y)], fill=(160, 160, 170, 255), width=6 * S // 2)
    if rng.random() < 0.5: d.ellipse([(w - 80) * S, (h - 80) * S, (w - 30) * S, (h - 30) * S], outline=RED + (255,), width=5 * S)
    return down(im)


def logo(size=200):
    p = os.path.join(ROOT, "assets", "logo.png")
    if os.path.exists(p): return Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
    im = Image.new("RGBA", (size * 2, size * 2)); d = ImageDraw.Draw(im)
    rrect(d, [0, 0, size * 2 - 1, size * 2 - 1], size // 2, fill=INK + (255,))
    f = font("black", int(size * 1.2)); d.text((size - f.getlength("R") / 2, size * 0.2), "R", font=f, fill=WHITE + (255,))
    return down(im)
