"""Spec -> video for ResolveAI Reels. Specs are built by kit.py; never hand-write elements.

Scene: {"until": beat|"end", "kind", "place": "factory"|..|None, "bg": "night"|"paper"|"ink", "dim": 0..1, "els": [...]}
Element timing: "at" = beat index (-1 = on screen at frame 0), "delay" = seconds after that beat starts.
Element types:
  img    a pre-drawn block: "make" = {"fn": <fx function>, "args": [...], "kw": {...}}; x, y = centre;
         "anim": pop|rise|fade|drop|left|right|none; "float": px (gentle bob); "scale"
  head   headline lines (list), "hl" words drawn in gold, size, x, y (top of block), align center|left, color
  count  counting number: to, prefix, suffix, dec, size, x, y, color, dur
  papers falling paper sheets (chaos), n
  strike a red line drawn across a box [x0, y0, x1, y1]
"""
import json, math, os, random, subprocess
import numpy as np
from PIL import Image, ImageDraw
import fx
from fx import W, H, FPS

CAP_Y = 1500          # caption block centre
ANIM = {"pop": 0.45, "rise": 0.5, "fade": 0.4, "drop": 0.55, "left": 0.5, "right": 0.5, "none": 0.0}


class Clock:
    def __init__(self, spec, times, total):
        self.times, self.total = times, total
        self.scene_t = []
        for k, sc in enumerate(spec["scenes"]):
            st = 0.0 if k == 0 else times[spec["scenes"][k - 1]["until"]][0]
            en = total if sc["until"] == "end" else times[sc["until"]][0]
            self.scene_t.append((st, en))

    def beat(self, b): return 0.0 if b is None or b < 0 else self.times[min(b, len(self.times) - 1)][0]
    def start(self, e): return 0.0 if e.get("at", -1) < 0 else self.beat(e["at"]) + e.get("delay", 0)
    def scene_at(self, t):
        for k, (a, b) in enumerate(self.scene_t):
            if a <= t < b: return k
        return len(self.scene_t) - 1


_IMG = {}
def el_image(e):
    m = e["make"]; key = json.dumps(m, sort_keys=True)
    if key not in _IMG:
        fn = getattr(fx, m["fn"]); args = list(m.get("args", []))
        if m["fn"] in ("phone", "browser"):
            args[0] = Image.open(os.path.join(fx.ROOT, args[0]))
        im = fn(*args, **m.get("kw", {}))
        if m.get("shadow", True) and m["fn"] not in ("person", "place"): im = fx.shadow(im)
        if m.get("rot"): im = im.rotate(m["rot"], expand=True, resample=Image.BICUBIC)
        _IMG[key] = im
    return _IMG[key]


_PLACE = {}
def place_img(name, seed):
    k = (name, seed)
    if k not in _PLACE: _PLACE[k] = fx.place(name, seed)
    return _PLACE[k]


def head_lines(e):
    f = fx.font(e.get("weight", "black"), e.get("size", 96)); out = []
    for ln in e["lines"]: out.append((ln, f.getlength(ln)))
    return f, out


def draw_head(c, e, t, t0, settled):
    f, lines = head_lines(e); d = ImageDraw.Draw(c); lh = int(e.get("size", 96) * 1.12)
    hl = set(w.lower().strip(".,!?:") for w in e.get("hl", []))
    base = fx.col(e.get("color", "white")); hlc = fx.col(e.get("hl_color", "gold"))
    for i, (ln, lw) in enumerate(lines):
        p = 1.0 if settled else fx.ease_out(fx.prog(t, t0 + 0.12 * i, 0.45))
        if p <= 0: continue
        x = e["x"] - lw / 2 if e.get("align", "center") == "center" else e["x"]
        y = e["y"] + i * lh + 40 * (1 - p); a = int(255 * p)
        for wd in ln.split(" "):
            colr = hlc if wd.lower().strip(".,!?:") in hl else base
            if e.get("shadow", True): d.text((x + 3, y + 5), wd, font=f, fill=(0, 0, 0, int(a * 0.55)))
            d.text((x, y), wd, font=f, fill=colr + (a,)); x += f.getlength(wd + " ")


def draw_el(c, e, t, t0, clock, settled=False):
    k = e["type"]
    if k == "img":
        im = el_image(e); an = e.get("anim", "pop"); p = 1.0 if settled else fx.prog(t, t0, ANIM.get(an, 0.45))
        x, y, s, a = e["x"], e["y"], e.get("scale", 1.0), 1.0
        if an == "pop": s *= 0.55 + 0.45 * fx.ease_back(p); a = min(1, p * 2.5)
        elif an == "rise": y += 90 * (1 - fx.ease_out(p)); a = fx.ease_out(p)
        elif an == "fade": a = fx.ease_out(p)
        elif an == "drop": y -= 260 * (1 - fx.ease_back(p, 1.2)); a = min(1, p * 3)
        elif an == "left": x -= 700 * (1 - fx.ease_out(p))
        elif an == "right": x += 700 * (1 - fx.ease_out(p))
        if e.get("float"): y += e["float"] * math.sin(t * 1.6 + e["x"] * 0.01)
        if e.get("out_at") is not None:
            to = clock.beat(e["out_at"]) + e.get("out_delay", 0)
            if t >= to: a *= 1 - fx.ease_out(fx.prog(t, to, 0.3))
        fx.paste_c(c, im, x, y, s, a)
    elif k == "head":
        draw_head(c, e, t, t0, settled)
    elif k == "count":
        p = 1.0 if settled else fx.ease_out(fx.prog(t, t0, e.get("dur", 1.1)))
        v = e["to"] * p; dec = e.get("dec", 0)
        txt = f'{e.get("prefix", "")}{v:,.{dec}f}{e.get("suffix", "")}'
        if e.get("indian"): txt = e.get("prefix", "") + indian(v, dec) + e.get("suffix", "")
        f = fx.font("black", e.get("size", 230)); d = ImageDraw.Draw(c); tw = f.getlength(txt)
        d.text((e["x"] - tw / 2 + 4, e["y"] + 8), txt, font=f, fill=(0, 0, 0, 120))
        d.text((e["x"] - tw / 2, e["y"]), txt, font=f, fill=fx.col(e.get("color", "gold")))
    elif k == "papers":
        rng = random.Random(7)
        for i in range(e.get("n", 14)):
            ti = t0 + i * 0.12; p = 1.0 if settled else fx.prog(t, ti, 0.9)
            if p <= 0: continue
            sx, ex = rng.uniform(80, W - 80), rng.uniform(140, W - 140); ey = rng.uniform(e.get("y0", 900), e.get("y1", 1260))
            im = el_image({"make": {"fn": "paper_sheet", "args": [i % 5], "kw": {"w": 200}, "rot": rng.uniform(-35, 35)}})
            fx.paste_c(c, im, sx + (ex - sx) * fx.ease_out(p), -200 + (ey + 200) * fx.ease_out(p), 1.0, 1.0)
    elif k == "strike":
        p = 1.0 if settled else fx.ease_out(fx.prog(t, t0, 0.35)); b = e["box"]; d = ImageDraw.Draw(c)
        d.line([(b[0], b[3]), (b[0] + (b[2] - b[0]) * p, b[3] - (b[3] - b[1]) * p)], fill=fx.RED, width=e.get("width", 16))


def indian(v, dec=0):
    s = f"{v:.{dec}f}"; i, _, f = s.partition(".")
    neg = i.startswith("-"); i = i.lstrip("-")
    if len(i) > 3:
        head, tail = i[:-3], i[-3:]; parts = []
        while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
        if head: parts.insert(0, head)
        i = ",".join(parts) + "," + tail
    return ("-" if neg else "") + i + ("." + f if f else "")


def anim_end(e, clock):
    if e.get("at", -1) < 0: return 0.0
    t0 = clock.start(e); k = e["type"]
    if k == "img": return t0 + ANIM.get(e.get("anim", "pop"), 0.45)
    if k == "head": return t0 + 0.45 + 0.12 * len(e["lines"])
    if k == "count": return t0 + e.get("dur", 1.1)
    if k == "papers": return t0 + 0.12 * e.get("n", 14) + 0.9
    return t0 + 0.4


class Renderer:
    def __init__(self, spec, times, total):
        self.spec, self.clock = spec, Clock(spec, times, total)
        self.words = []                                       # (start, end, word, phrase index)
        for i, ph in enumerate(spec["phrases"]):
            a, b = times[i]; ws = ph.get("cap", ph["say"]).split(); L = sum(len(w) + 1 for w in ws) or 1; acc = 0
            for w_ in ws:
                ws0 = a + (b - a) * acc / L; acc += len(w_) + 1; self.words.append((ws0, a + (b - a) * acc / L, w_, i))
        self.phr = [(times[i][0], times[i][1] + 0.25) for i in range(len(spec["phrases"]))]
        self.cache = {}

    def background(self, sc, t, k):
        st, en = self.clock.scene_t[k]
        if sc.get("place"):
            bg = place_img(sc["place"], sc.get("seed", 3)).copy()
            z = 1.0 + 0.05 * fx.smooth(fx.clamp((t - st) / max(1, en - st)))
            if z > 1.001:
                bw, bh = int(W * z), int(H * z); bg = bg.resize((bw, bh), Image.BILINEAR).crop(((bw - W) // 2, int((bh - H) * 0.6), (bw - W) // 2 + W, int((bh - H) * 0.6) + H))
        else:
            c = {"paper": fx.PAPER, "ink": (14, 14, 16), "night": fx.NIGHT}[sc.get("bg", "night")]
            bg = Image.new("RGBA", (W, H), c + (255,))
        if sc.get("dim"): bg.alpha_composite(Image.new("RGBA", (W, H), (8, 10, 22, int(255 * sc["dim"]))))
        return bg

    def frame(self, t):
        cl = self.clock; k = cl.scene_at(t); sc = self.spec["scenes"][k]; st, en = cl.scene_t[k]
        out = self.background(sc, t, k)
        for e in sc["els"]:
            if e.get("at", -1) >= 0 and t < cl.start(e): continue
            draw_el(out, e, t, cl.start(e), cl, settled=e.get("at", -1) < 0 or (t >= anim_end(e, cl) and e["type"] != "img"))
        # scene transition: quick white flash-wipe
        if k > 0 and t - st < 0.18:
            a = 1 - (t - st) / 0.18; out.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(110 * a))))
        if not sc.get("no_caps"): self.caption(out, t)
        self.header(out)
        return out.convert("RGB")

    def header(self, c):
        d = ImageDraw.Draw(c); f = fx.font("xbold", 34)
        lg = fx.logo(64); c.alpha_composite(lg, (64, 92))
        d.text((146, 106), "RESOLVEAI", font=f, fill=fx.WHITE)
        s = self.spec.get("header", ""); sw = f.getlength(s)
        if s:
            fx.rrect(d, [W - 64 - sw - 40, 96, W - 64, 152], 28, fill=fx.GOLD + (255,))
            d.text((W - 64 - sw - 20, 104), s, font=f, fill=fx.INK)

    def caption(self, c, t):
        cur = next((i for i, (a, b) in enumerate(self.phr) if a <= t < b), None)
        if cur is None: return
        ws = [w for w in self.words if w[3] == cur]
        f = fx.font("xbold", 58); d = ImageDraw.Draw(c)
        lines, line, wid = [], [], 0
        for w_ in ws:
            lw = f.getlength(w_[2] + " ")
            if wid + lw > 900 and line: lines.append(line); line, wid = [], 0
            line.append(w_); wid += lw
        if line: lines.append(line)
        lh = 76; y0 = CAP_Y - lh * len(lines) / 2
        for li, ln in enumerate(lines):
            txt = " ".join(w[2] for w in ln); tw = f.getlength(txt); x = (W - tw) / 2; y = y0 + li * lh
            fx.rrect(d, [x - 22, y - 8, x + tw + 22, y + lh - 6], 18, fill=(8, 10, 22, 215))
            for w_ in ln:
                on = w_[0] <= t < w_[1] + 0.05
                d.text((x, y), w_[2], font=f, fill=fx.GOLD if on else fx.WHITE); x += f.getlength(w_[2] + " ")


# ---------------- sound ----------------
def sfx(spec, clock, total, path):
    import soundfile as sf
    from scipy.signal import lfilter
    SR = 48000; N = int((total + 0.5) * SR); t = np.arange(N) / SR
    rng = np.random.default_rng(2); lp = lambda x, a: lfilter([1 - a], [1, -a], x)
    out = np.zeros(N)
    # warm pad: A minor-ish chord, slow swell
    pad = sum(np.sin(2 * np.pi * f * t + i) * g for i, (f, g) in enumerate(((110, .5), (164.8, .35), (220, .3), (261.6, .2))))
    out += pad * 0.035 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t)) * np.minimum(1, t / 1.5) * np.minimum(1, (total + 0.5 - t) / 1.2)
    beat = 60 / 96                                      # soft pulse
    for bt in np.arange(0.5, total, beat):
        n = int(0.18 * SR); tt = np.arange(n) / SR; i = int(bt * SR); e = min(N, i + n)
        out[i:e] += (np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 22) * 0.18)[:e - i]
    def put(at, s):
        i = int(max(0, at) * SR); e = min(N, i + len(s)); out[i:e] += s[:e - i]
    def pop(at):
        n = int(0.09 * SR); tt = np.arange(n) / SR
        put(at, np.sin(2 * np.pi * (900 - 4000 * tt) * tt) * np.exp(-tt * 45) * 0.22)
    def whoosh(at):
        n = int(0.45 * SR); tt = np.arange(n) / SR; nz = rng.normal(0, 1, n)
        put(at - 0.12, (lp(nz, 0.9) - lp(nz, 0.995)) * np.sin(np.pi * tt / 0.45) ** 2 * 0.3)
    def ding(at):
        n = int(0.8 * SR); tt = np.arange(n) / SR
        put(at, (np.sin(2 * np.pi * 1318 * tt) + 0.5 * np.sin(2 * np.pi * 1975 * tt)) * np.exp(-tt * 6) * 0.12)
    for sc in spec["scenes"]:
        for e in sc["els"]:
            if e.get("at", -1) < 0: continue
            if e["type"] == "img" and e.get("anim", "pop") in ("pop", "drop"): pop(clock.start(e))
            elif e["type"] == "count": ding(clock.start(e) + e.get("dur", 1.1))
            elif e["type"] == "img": whoosh(clock.start(e) + 0.1)
    for st, _ in clock.scene_t[1:]: whoosh(st)
    sf.write(path, (out / max(1, np.abs(out).max() / 0.9)).astype(np.float32), SR)


# ---------------- entry points ----------------
def _encode_range(args):
    spec, times, total, a, b, path = args
    r = Renderer(spec, times, total); tmp = path[:-4] + ".tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-profile:v", "high", tmp], stdin=subprocess.PIPE)
    for fi in range(a, b): p.stdin.write(r.frame(fi / FPS).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode != 0: raise SystemExit("ffmpeg failed on part " + path)
    os.replace(tmp, path)


def render(spec, times, total, wav, out, stills=None, workers=None):
    if stills is not None:
        r = Renderer(spec, times, total)
        for t in stills: r.frame(min(max(0, t), total - 0.05)).save(f"{out}.still_{t:05.1f}.png")
        return
    workers = workers or max(2, min(4, (os.cpu_count() or 2)))
    N = int(round(total * FPS)); parts = workers * 2
    work = os.path.dirname(out); bounds = [(N * i // parts, N * (i + 1) // parts) for i in range(parts)]
    jobs = [(spec, times, total, a, b, os.path.join(work, f"part{i}.mp4")) for i, (a, b) in enumerate(bounds)]
    from multiprocessing import Pool
    with Pool(workers) as pool: pool.map(_encode_range, jobs)
    lst = os.path.join(work, "parts.txt"); open(lst, "w").write("".join(f"file '{os.path.basename(j[5])}'\n" for j in jobs))
    vid = os.path.join(work, "video_only.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    sfxp = os.path.join(work, "sfx.wav"); sfx(spec, Clock(spec, times, total), total, sfxp)
    mix = os.path.join(work, "mix.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-i", sfxp, "-filter_complex",
                    "[1:a]volume=0.5[s];[s][0:a]sidechaincompress=threshold=0.05:ratio=5:attack=20:release=300[sd];"
                    "[0:a][sd]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]",
                    "-map", "[a]", "-t", f"{N / FPS:.3f}", mix], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", out], check=True)
    for j in jobs: os.remove(j[5])
    for f in (lst, vid, sfxp, mix): os.remove(f)


def cover(spec, path):
    """Thumbnail 1080x1920: the hook place, kicker chip, two big lines (last in gold), logo."""
    cv = spec["cover"]; c = place_img(cv.get("place", spec["scenes"][0].get("place") or "factory"), 5).copy()
    c.alpha_composite(Image.new("RGBA", (W, H), (8, 10, 22, 110)))
    if cv.get("person"):
        p = fx.person(*cv["person"], scale=1.0); c.alpha_composite(p, (W // 2 - p.width // 2, 1344 - p.height + 40))
    d = ImageDraw.Draw(c)
    ch = fx.shadow(fx.chip(cv.get("kicker", "RESOLVEAI"), size=46)); fx.paste_c(c, ch, W / 2, 300)
    lines = cv["big"] if isinstance(cv["big"], list) else [cv["big"]]
    y = 380
    for i, ln in enumerate(lines):
        f = fx.font("black", 150)
        while f.getlength(ln) > 960: f = fx.font("black", f.size - 6)
        tw = f.getlength(ln); colr = fx.GOLD if i == len(lines) - 1 else fx.WHITE
        d.text(((W - tw) / 2 + 4, y + 8), ln, font=f, fill=(0, 0, 0, 160)); d.text(((W - tw) / 2, y), ln, font=f, fill=colr)
        y += int(f.size * 1.1)
    if cv.get("sub"):
        f = fx.font("bold", 52); tw = f.getlength(cv["sub"]); d.text(((W - tw) / 2, y + 10), cv["sub"], font=f, fill=fx.WHITE)
    lg = fx.logo(110); c.alpha_composite(lg, (W // 2 - 55, 1620))
    c.convert("RGB").save(path)
