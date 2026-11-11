"""Procedural illuminated-manuscript page (look-dev for the hero asset).

python3 assets/art/concept/render_page.py  ->  sayfa_v2.png
Everything is drawn in code (no generated imagery): paper, gilding with
red bole showing through, lapis/turquoise rulings, floral ground,
cartouches, ink and ageing.
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = Path("/tmp/ttf")
rng = np.random.default_rng(11)

PW, PH = 1240, 1960          # page
CW, CH = 1460, 2180          # canvas (page on dark backdrop)
S = 2                        # supersampling for line work


# ---------------------------------------------------------------- noise
def fbm(w, h, octaves=6, base=3, persist=0.55, seed=None):
    g = np.random.default_rng(seed) if seed is not None else rng
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * 2 ** o
        small = g.random((max(2, int(n * h / w)), n)).astype(np.float32)
        layer = np.asarray(Image.fromarray(small, "F").resize((w, h), Image.BICUBIC))
        out += amp * layer
        tot += amp
        amp *= persist
    out /= tot
    return (out - out.min()) / (out.max() - out.min() + 1e-6)


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def mask_from(draw_fn, w, h, blur=0.0):
    m = Image.new("L", (w * S, h * S), 0)
    draw_fn(ImageDraw.Draw(m))
    m = m.resize((w, h), Image.LANCZOS)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(m).astype(np.float32) / 255.0


def comp(base, color, alpha):
    """Alpha-composite a flat colour (or colour image) onto base with a 0..1 mask."""
    a = alpha[..., None]
    col = np.array(color, np.float32) if not isinstance(color, np.ndarray) else color
    return base * (1 - a) + col * a


# ---------------------------------------------------------------- materials
def paper(w, h):
    n1, n2, n3 = fbm(w, h, 7, 3, 0.55), fbm(w, h, 5, 18, 0.6), fbm(w, h, 3, 2, 0.5)
    base = np.array([232, 218, 186], np.float32)
    img = base * (0.88 + 0.10 * n1[..., None] + 0.04 * n2[..., None])
    img[..., 2] -= 14 * n3                       # uneven yellowing
    # fibres
    fib = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(fib)
    for _ in range(9000):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a, l = rng.uniform(0, math.pi), rng.uniform(6, 26)
        d.line([(x, y), (x + l * math.cos(a), y + l * math.sin(a))], fill=int(rng.uniform(10, 40)), width=1)
    fib = np.asarray(fib.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255
    img = comp(img, (180, 150, 105), fib * 0.35)
    # foxing
    fox = np.zeros((h, w), np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(70):
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(2, 11)
        x0, x1, y0, y1 = int(max(cx - 3 * r, 0)), int(min(cx + 3 * r, w)), int(max(cy - 3 * r, 0)), int(min(cy + 3 * r, h))
        sub = np.exp(-(((xx[y0:y1, x0:x1] - cx) ** 2 + (yy[y0:y1, x0:x1] - cy) ** 2) / (2 * r * r)))
        fox[y0:y1, x0:x1] = np.maximum(fox[y0:y1, x0:x1], sub * rng.uniform(.25, .7))
    img = comp(img, (150, 100, 55), fox * 0.55)
    return img


def water_stain(w, h, cx, cy, r, strength=0.45):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    warp = (fbm(w, h, 5, 4, 0.6) - .5) * r * 0.5
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) + warp
    ring = np.exp(-((d - r) ** 2) / (2 * (r * 0.025) ** 2))
    inner = np.clip(1 - d / r, 0, 1) ** 0.5 * 0.25
    return np.clip(ring + inner, 0, 1) * strength


def gold(w, h):
    n = fbm(w, h, 6, 6, 0.55)
    streak = fbm(w, h, 3, 2, 0.5)
    base = np.array([206, 168, 84], np.float32)
    img = base * (0.82 + 0.30 * n[..., None]) + 55 * (streak[..., None] ** 4)
    # crackle: thin network from a ridged noise
    c = np.abs(fbm(w, h, 4, 22, 0.5, seed=5) - 0.5)
    crack = np.clip(1 - c / 0.025, 0, 1)
    img = comp(img, (120, 80, 35), crack * 0.28)
    # flaking: red bole shows through where gold leaf is lost
    flake = fbm(w, h, 5, 10, 0.55, seed=9)
    bole = np.clip((flake - 0.86) / 0.04, 0, 1) * np.clip((fbm(w, h, 3, 40, .6, seed=12) - .45) / .1, 0, 1)
    img = comp(img, (150, 72, 46), bole * 0.85)
    return img


def pigment(w, h, color, grain=0.18):
    n = fbm(w, h, 6, 12, 0.6)
    return np.array(color, np.float32) * (1 - grain / 2 + grain * n[..., None])


# ---------------------------------------------------------------- ornament
FLOWER_COLS = [(190, 58, 42), (196, 70, 52), (74, 104, 168), (232, 222, 200), (212, 118, 112), (58, 132, 128)]


def floral_layer(w, h, density=1.0, seed=3):
    """Vine scrolls with five-petal flowers and leaves, drawn at S× and reduced."""
    g = np.random.default_rng(seed)
    big = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    # vines
    for _ in range(int(w * h / 2600 * density)):
        x, y = g.uniform(0, w * S), g.uniform(0, h * S)
        a = g.uniform(0, 2 * math.pi)
        turn = g.choice([-1, 1])
        pts = []
        for k in range(40):
            a += turn * (0.05 + 0.012 * k)
            step = max(3.0, 12 - 0.22 * k)
            x += step * math.cos(a)
            y += step * math.sin(a)
            pts.append((x, y))
        d.line(pts, fill=(92, 58, 28, 230), width=3)
    # leaves
    for _ in range(int(w * h / 700 * density)):
        x, y = g.uniform(0, w * S), g.uniform(0, h * S)
        a = g.uniform(0, math.pi)
        l = g.uniform(12, 20)
        poly = [(x + l * math.cos(a + t) * (1 if i % 2 == 0 else .35), y + l * math.sin(a + t) * (1 if i % 2 == 0 else .35))
                for i, t in enumerate(np.linspace(0, 2 * math.pi, 9))]
        d.polygon(poly, fill=(108, 128, 92, 230), outline=(70, 60, 35, 230))
    # flowers
    for _ in range(int(w * h / 1100 * density)):
        x, y = g.uniform(0, w * S), g.uniform(0, h * S)
        r = g.uniform(14, 26)
        col = FLOWER_COLS[g.integers(len(FLOWER_COLS))]
        rot = g.uniform(0, 2 * math.pi)
        npet = g.choice([5, 5, 6, 8])
        for k in range(npet):
            a = rot + 2 * math.pi * k / npet
            px, py = x + r * 0.62 * math.cos(a), y + r * 0.62 * math.sin(a)
            pr = r * 0.48
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=col + (255,), outline=(70, 40, 25, 255), width=2)
        d.ellipse([x - r * .28, y - r * .28, x + r * .28, y + r * .28], fill=(226, 186, 92, 255), outline=(90, 55, 25, 255), width=2)
        # highlight dot
        d.ellipse([x - r * .1 - 3, y - r * .1 - 3, x - r * .1 + 3, y - r * .1 + 3], fill=(250, 240, 220, 160))
    small = big.resize((w, h), Image.LANCZOS)
    arr = np.asarray(small).astype(np.float32)
    rgb, a = arr[..., :3], arr[..., 3] / 255
    rgb *= (0.86 + 0.24 * fbm(w, h, 5, 14, 0.6))[..., None]       # uneven paint
    a *= np.clip(0.75 + 0.5 * fbm(w, h, 4, 8, 0.6, seed=seed + 1), 0, 1)  # worn paint
    return rgb, a


def cloud_cartouche(w, h, lobes=12, amp=0.05):
    def fn(d):
        pts = []
        for t in np.linspace(0, 2 * math.pi, 720):
            ex = 0.5 * w * S * (abs(math.cos(t)) ** 0.55) * np.sign(math.cos(t))
            ey = 0.5 * h * S * (abs(math.sin(t)) ** 0.9) * np.sign(math.sin(t))
            k = 1 + amp * math.cos(lobes * t)
            pts.append((w * S / 2 + ex * k * 0.97, h * S / 2 + ey * k * 0.94))
        d.polygon(pts, fill=255)
    return fn


def ogee(w, h):
    def fn(d):
        pts = []
        for t in np.linspace(0, 2 * math.pi, 720):
            x = math.sin(t)
            y = math.cos(t)
            x = np.sign(x) * abs(x) ** 0.55 * (1 - 0.55 * abs(y) ** 3)
            k = 1 + 0.035 * math.cos(14 * t)
            pts.append((w * S / 2 + 0.5 * w * S * x * k * 0.96, h * S / 2 + 0.5 * h * S * y * 0.98))
        d.polygon(pts, fill=255)
    return fn


def font(name, size):
    return ImageFont.truetype(str(FONTS / f"{name}.ttf"), size)


def text_mask(w, h, lines, fnt, leading, top):
    def fn(d):
        f = font(fnt[0], fnt[1] * S)
        y = top * S
        for line in lines:
            tw = d.textlength(line, font=f)
            d.text(((w * S - tw) / 2 + rng.normal(0, 3), y + rng.normal(0, 2)), line, font=f, fill=255)
            y += leading * S
    return fn


def ink(base, m, color=(34, 24, 20)):
    n = fbm(base.shape[1], base.shape[0], 5, 40, 0.6)
    bleed = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    out = comp(base, (90, 70, 50), bleed * 0.18)
    return comp(out, color, np.clip(m * (0.72 + 0.4 * n), 0, 1))


def rosette(img, cx, cy, r):
    h, w = img.shape[:2]
    def fn(d):
        x, y, R = cx * S, cy * S, r * S
        d.ellipse([x - R, y - R, x + R, y + R], fill=255)
    gm = mask_from(fn, w, h)
    img = comp(img, gold(w, h), gm)
    def petals(d):
        x, y, R = cx * S, cy * S, r * S
        for k in range(8):
            a = 2 * math.pi * k / 8
            px, py = x + R * .58 * math.cos(a), y + R * .58 * math.sin(a)
            pr = R * .2
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=255)
    pm = mask_from(petals, w, h)
    img = comp(img, (178, 54, 40), pm * .9)
    ring = mask_from(lambda d: d.ellipse([cx * S - r * S, cy * S - r * S, cx * S + r * S, cy * S + r * S], outline=255, width=3), w, h)
    img = comp(img, (80, 50, 25), ring)
    dot = mask_from(lambda d: d.ellipse([cx * S - r * S * .22, cy * S - r * S * .22, cx * S + r * S * .22, cy * S + r * S * .22], fill=255), w, h)
    return comp(img, (40, 70, 130), dot)


def rule_line(w, h, x0, y0, x1, y1, width):
    def fn(d):
        n = 40
        pts = [(x0 * S + (x1 - x0) * S * i / n + rng.normal(0, .5), y0 * S + (y1 - y0) * S * i / n + rng.normal(0, .5)) for i in range(n + 1)]
        d.line(pts, fill=255, width=int(width * S))
    return mask_from(fn, w, h)


def rect_mask(w, h, box, inset=0):
    x0, y0, x1, y1 = box
    return mask_from(lambda d: d.rectangle([(x0 + inset) * S, (y0 + inset) * S, (x1 - inset) * S, (y1 - inset) * S], fill=255), w, h)


def frame_rules(img, box, spec):
    """spec: list of (inset_px, width_px, colour) rulings around a box."""
    h, w = img.shape[:2]
    x0, y0, x1, y1 = box
    for inset, wd, col in spec:
        for seg in [(x0 + inset, y0 + inset, x1 - inset, y0 + inset), (x0 + inset, y1 - inset, x1 - inset, y1 - inset),
                    (x0 + inset, y0 + inset, x0 + inset, y1 - inset), (x1 - inset, y0 + inset, x1 - inset, y1 - inset)]:
            img = comp(img, col, rule_line(w, h, *seg, wd) * .92)
    return img


# ---------------------------------------------------------------- page
def build():
    w, h = PW, PH
    img = paper(w, h)

    OUT = (95, 105, w - 95, h - 115)          # outer gold frame box
    GOLDBAND = 26
    INNER = (OUT[0] + GOLDBAND + 12, OUT[1] + GOLDBAND + 12, OUT[2] - GOLDBAND - 12, OUT[3] - GOLDBAND - 12)
    x0, y0, x1, y1 = INNER
    TOPH, BOTH, SIDEW = 300, 270, 150
    top = (x0, y0, x1, y0 + TOPH)
    bot = (x0, y1 - BOTH, x1, y1)
    left = (x0, y0 + TOPH + 14, x0 + SIDEW, y1 - BOTH - 14)
    right = (x1 - SIDEW, y0 + TOPH + 14, x1, y1 - BOTH - 14)
    text = (x0 + SIDEW + 14, y0 + TOPH + 14, x1 - SIDEW - 14, y1 - BOTH - 14)

    # outer gold band
    band = rect_mask(w, h, OUT) - rect_mask(w, h, OUT, GOLDBAND)
    img = comp(img, gold(w, h), np.clip(band, 0, 1))
    img = frame_rules(img, OUT, [(0, 1.6, (40, 28, 20)), (GOLDBAND, 1.4, (40, 28, 20)), (GOLDBAND + 5, 2.0, (40, 70, 140)), (-14, 1.2, (190, 150, 70)), (-20, 1.0, (40, 70, 140))])

    # panels: gold floral ground with cartouche (top/bottom), turquoise with ogees (sides)
    gld = gold(w, h)
    for box in (top, bot):
        m = rect_mask(w, h, box)
        img = comp(img, gld, m)
        rgb, a = floral_layer(box[2] - box[0], box[3] - box[1], 1.0, seed=int(box[1]))
        full_rgb = np.zeros((h, w, 3), np.float32)
        full_a = np.zeros((h, w), np.float32)
        full_rgb[box[1]:box[3], box[0]:box[2]] = rgb
        full_a[box[1]:box[3], box[0]:box[2]] = a
        img = comp(img, full_rgb, full_a * m)
        cw, chh = int((box[2] - box[0]) * 0.62), int((box[3] - box[1]) * 0.66)
        cm_local = mask_from(cloud_cartouche(cw, chh), cw, chh)
        cm = np.zeros((h, w), np.float32)
        cx0 = (box[0] + box[2]) // 2 - cw // 2
        cy0 = (box[1] + box[3]) // 2 - chh // 2
        cm[cy0:cy0 + chh, cx0:cx0 + cw] = cm_local
        edge = np.clip(np.asarray(Image.fromarray((cm * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))).astype(np.float32) / 255 - cm, 0, 1)
        img = comp(img, (60, 40, 22), edge * .85)
        img = comp(img, paper(w, h) * 1.03, cm)
        img = frame_rules(img, box, [(0, 1.4, (40, 28, 20))])
    for box in (left, right):
        m = rect_mask(w, h, box)
        img = comp(img, pigment(w, h, (52, 128, 132)), m)
        bw, bh = box[2] - box[0], box[3] - box[1]
        for k in range(2):
            ow, oh = int(bw * .9), int(bh * .46)
            om_local = mask_from(ogee(ow, oh), ow, oh)
            om = np.zeros((h, w), np.float32)
            ox0 = box[0] + (bw - ow) // 2
            oy0 = box[1] + int(bh * (0.04 + 0.5 * k))
            om[oy0:oy0 + oh, ox0:ox0 + ow] = om_local
            img = comp(img, gld, om)
            rgb, a = floral_layer(ow, oh, 1.1, seed=oy0 + k)
            fr = np.zeros((h, w, 3), np.float32)
            fa = np.zeros((h, w), np.float32)
            fr[oy0:oy0 + oh, ox0:ox0 + ow] = rgb
            fa[oy0:oy0 + oh, ox0:ox0 + ow] = a
            img = comp(img, fr, fa * om)
            edge = np.clip(np.asarray(Image.fromarray((om * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))).astype(np.float32) / 255 - om, 0, 1)
            img = comp(img, (60, 40, 22), edge * .8)
        img = frame_rules(img, box, [(0, 1.4, (40, 28, 20)), (5, 2.2, (176, 54, 44))])

    # cetvel between panels and text: red, dotted turquoise, gold
    img = frame_rules(img, INNER, [(-6, 2.0, (176, 54, 44)), (-10, 1.2, (40, 28, 20))])
    img = frame_rules(img, text, [(-4, 1.6, (40, 28, 20)), (-8, 2.4, (190, 150, 70)), (0, 1.0, (176, 54, 44))])

    # titles in cartouches
    tm = mask_from(text_mask(w, h, ["PHĀGOS RĒGOSYO"], ("cor_bold", 64), 0, (top[1] + top[3]) // 2 - 44), w, h)
    img = comp(img, (150, 112, 48), tm)
    img = ink(img, mask_from(text_mask(w, h, ["PHĀGOS RĒGOSYO"], ("cor_bold", 64), 0, (top[1] + top[3]) // 2 - 44), w, h) * 0, (0, 0, 0))
    edge_t = np.clip(np.asarray(Image.fromarray((tm * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))).astype(np.float32) / 255 - tm, 0, 1)
    img = comp(img, (70, 45, 20), edge_t * .7)
    bm = mask_from(text_mask(w, h, ["Kerdāgros"], ("ebg_it", 76), 0, (bot[1] + bot[3]) // 2 - 50), w, h)
    img = comp(img, (150, 112, 48), bm)
    edge_b = np.clip(np.asarray(Image.fromarray((bm * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))).astype(np.float32) / 255 - bm, 0, 1)
    img = comp(img, (70, 45, 20), edge_b * .7)

    # body text with verse rosettes
    lines = ["Mīros Mērom ageti", "Mēros nākos Mīros", "āgrom emeti Mīros", "dīwosyo khewom", "dōneti Mīros rēgos", "Mērosyo āgros nākos", "phāgom khrepheti"]
    lead = (text[3] - text[1] - 60) / len(lines)
    tmask = mask_from(text_mask(w, h, lines, ("ebg_reg", 70), lead, text[1] + 26), w, h)
    img = ink(img, tmask)
    f = font("ebg_reg", 70)
    dd = ImageDraw.Draw(Image.new("L", (10, 10)))
    for i, line in enumerate(lines):
        tw = dd.textlength(line, font=f)
        cy = text[1] + 26 + i * lead + 50
        if i in (0, 3, 5):
            img = rosette(img, (w + tw) / 2 + 30, cy, 15)
    # ruling guide marks (mistar) faintly pressed into the paper
    for i in range(len(lines)):
        yb = text[1] + 26 + i * lead + 82
        img = comp(img, (150, 120, 85), rule_line(w, h, text[0] + 30, yb, text[2] - 30, yb, 0.8) * .18)

    # ageing: water stain, edge browning, rubbing on gold, global grain
    img = comp(img, (140, 100, 55), water_stain(w, h, w * .78, h * .30, 260, .35))
    img = comp(img, (150, 110, 60), water_stain(w, h, w * .18, h * .86, 190, .28))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edged = np.minimum(np.minimum(xx, w - xx), np.minimum(yy, h - yy))
    brown = np.clip(1 - edged / 55 + (fbm(w, h, 5, 6, .6) - .5) * .6, 0, 1)
    img = comp(img, (128, 90, 50), brown * .45)
    rub = np.clip((fbm(w, h, 4, 5, .6, seed=21) - .62) / .2, 0, 1)
    img = img * (1 - 0.10 * rub[..., None])
    img = img * (0.95 + 0.08 * fbm(w, h, 3, 90, .7, seed=33)[..., None])

    # page alpha with a worn, irregular edge
    em = np.clip(edged / 2.5 + (fbm(w, h, 5, 30, .6, seed=44) - .5) * 1.2, 0, 1)
    page = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
    page.putalpha(Image.fromarray((em * 255).astype(np.uint8)))

    # backdrop: dark walnut desk under lamp light
    bw_, bh_ = CW, CH
    desk = np.array([46, 31, 21], np.float32) * (0.75 + 0.5 * fbm(bw_, bh_, 6, 3, .6, seed=50)[..., None])
    gy, gx = np.mgrid[0:bh_, 0:bw_].astype(np.float32)
    grain = np.sin(gx * 0.035 + fbm(bw_, bh_, 4, 4, .6, seed=51) * 18) * .5 + .5
    desk *= (0.85 + 0.18 * grain[..., None])
    light = np.exp(-(((gx - bw_ * .5) / (bw_ * .55)) ** 2 + ((gy - bh_ * .35) / (bh_ * .55)) ** 2))
    desk = desk * (0.35 + 0.95 * light[..., None]) + np.array([40, 22, 0], np.float32) * light[..., None]
    canvas = Image.fromarray(np.clip(desk, 0, 255).astype(np.uint8)).convert("RGBA")
    shadow = Image.new("L", (bw_, bh_), 0)
    ox, oy = (bw_ - w) // 2, (bh_ - h) // 2
    shadow.paste(page.getchannel("A"), (ox + 18, oy + 26))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas = Image.composite(Image.new("RGBA", (bw_, bh_), (8, 4, 2, 255)), canvas, shadow.point(lambda v: int(v * .75)))
    # lamp light also falls on the page
    pl = np.asarray(page).astype(np.float32)
    lit = light[oy:oy + h, ox:ox + w]
    pl[..., :3] *= (0.62 + 0.48 * lit[..., None])
    pl[..., :3] += np.array([18, 8, 0], np.float32) * lit[..., None]
    page = Image.fromarray(np.clip(pl, 0, 255).astype(np.uint8), "RGBA")
    canvas.alpha_composite(page, (ox, oy))
    out = HERE / "sayfa_v2.png"
    canvas.convert("RGB").save(out)
    return out


if __name__ == "__main__":
    print(build())
