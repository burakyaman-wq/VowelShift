"""Rule tiles, the book-cover menu, bookmark slips and sleeve fabrics.

python3 tools/art/tex_props.py  ->  assets/art/tex/*.png

Rule cards are glazed tiles: the pictogram and name are cobalt under the
glaze (fixed), the proven correspondences are written on top in ink by the
scribe (they appear as the player proves them).
"""
import math

import numpy as np
from scipy import ndimage as ndi

from tex_core import (INK, OUT, Canvas, apply_ink, blur, comp, fbm, gilding, outline, pigment, ridged, save_gray,
                      save_rgb, text_mask)
from tex_docs import save_maps
from tex_illum import cloud_cartouche, spiral_ground, paint_ground

COBALT = (30, 52, 138)
TW, TH = 540, 720

RULES = {
    "R1": ("Sert ünsüzler", ["bh → ph", "dh → th", "gh → kh"]),
    "R2": ("Çift ünlüler tekleşir", ["ei → ī", "eu → ū"]),
    "R3": ("ē yükselir", ["ē → ī"]),
    "R4": ("ā kayar", ["ā → ē"]),
    "R5": ("Son ünsüz düşer", ["-s → ∅", "-m → ∅"]),
    "R6": ("Damaklaşma", ["kh → ş", "k → ç", "g → c"]),
}


def brush(c, pts, width):
    """A brush stroke: a line plus rounded ends."""
    c.line(pts, width)
    for x, y in (pts[0], pts[-1]):
        c.ellipse(x, y, width / 2, width / 2)


def pictogram(rule, w=TW, h=TH, cx=TW / 2, cy=265, s=1.0):
    c = Canvas(w, h)
    if rule == "R1":      # a soft wave turns into a hard zigzag
        wave = [(cx - 150 + t * 120, cy + 26 * math.sin(t * 2 * math.pi)) for t in np.linspace(0, 1, 30)]
        zig = [(cx - 20, cy), (cx + 20, cy - 40), (cx + 60, cy + 40), (cx + 100, cy - 40), (cx + 145, cy + 30)]
        brush(c, wave, 13 * s)
        brush(c, zig, 13 * s)
    elif rule == "R2":    # two become one long vowel
        c.ellipse(cx - 120, cy - 20, 24, 24)
        c.ellipse(cx - 60, cy + 20, 24, 24)
        brush(c, [(cx - 10, cy), (cx + 30, cy)], 8)
        brush(c, [(cx + 18, cy - 14), (cx + 34, cy), (cx + 18, cy + 14)], 8)
        brush(c, [(cx + 60, cy), (cx + 150, cy)], 22)
    elif rule == "R3":    # the vowel climbs
        brush(c, [(cx - 120, cy + 60), (cx - 20, cy + 60)], 18)
        brush(c, [(cx + 20, cy - 50), (cx + 120, cy - 50)], 18)
        arc = [(cx - 70 + 140 * t, cy + 30 - 90 * math.sin(t * math.pi / 2)) for t in np.linspace(0, 1, 20)]
        brush(c, arc, 8)
        brush(c, [(cx + 52, cy - 70), (cx + 72, cy - 60), (cx + 58, cy - 38)], 8)
    elif rule == "R4":    # the vowel slides forward
        brush(c, [(cx - 140, cy + 30), (cx - 40, cy + 30)], 18)
        brush(c, [(cx + 40, cy - 20), (cx + 140, cy - 20)], 18)
        brush(c, [(cx - 30, cy + 10), (cx + 30, cy - 4)], 8)
        brush(c, [(cx + 14, cy - 20), (cx + 32, cy - 5), (cx + 12, cy + 10)], 8)
    elif rule == "R5":    # the last sound falls off the edge
        brush(c, [(cx - 150, cy - 30), (cx + 60, cy - 30)], 14)
        brush(c, [(cx + 60, cy - 30), (cx + 60, cy + 90)], 6)
        c.ellipse(cx + 110, cy + 40, 16, 16)
        brush(c, [(cx + 92, cy - 4), (cx + 104, cy + 14)], 5)
    elif rule == "R6":    # a hard corner softens into a curl
        brush(c, [(cx - 140, cy - 40), (cx - 80, cy + 50), (cx - 30, cy - 40)], 13)
        curl = [(cx + 70 + 50 * math.cos(a) * (1 - a / 9), cy + 50 * math.sin(a) * (1 - a / 9)) for a in np.linspace(0, 7.5, 50)]
        brush(c, curl, 12)
    return c.mask()


def rule_line_mask(text, size, origin, seed):
    return text_mask(TW, TH, [text], size, origin, 0, align="left", seed=seed, wobble=0.6)


def tile(rule, lines_shown, state="fresh", seed=0):
    """state: fresh | worn (inherited) | scorched (survived the fire)."""
    w, h = TW, TH
    g = np.random.default_rng(seed)
    body = pigment(w, h, (186, 118, 86), seed, 0.25)
    glaze = pigment(w, h, (238, 239, 230), seed + 1, 0.05)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    thin = np.clip(1 - (edge + (fbm(w, h, 4, 8, 0.6, seed + 2) - 0.5) * 16) / 16, 0, 1)
    img = comp(glaze, body * 0.8 + 40, thin * 0.7)
    border = Canvas(w, h)
    for inset, wd in ((34, 7), (48, 2.5)):
        border.line([(inset, inset), (w - inset, inset), (w - inset, h - inset), (inset, h - inset), (inset, inset)], wd)
    cob = np.clip(blur(border.mask(), 1.4) * 1.2 + blur(pictogram(rule), 1.6) * 1.15, 0, 1)
    name, rule_lines = RULES[rule]
    nm = text_mask(w, h, [name], 40 if len(name) < 16 else 32, (w / 2, 120), 0, seed=seed + 3, wobble=0.3)
    cob = np.clip(cob + blur(nm, 1.0), 0, 1)
    pool = np.clip(cob - blur(cob, 2.5), 0, 1)
    img = comp(img, pigment(w, h, COBALT, seed + 4, 0.3), cob * 0.92)
    img = comp(img, (14, 24, 80), pool * 0.6)
    guide = Canvas(w, h)
    for i in range(3):
        y = 440 + 78 * i
        for x in np.arange(90, w - 90, 16):
            guide.ellipse(x, y + 14, 1.2, 1.2)
    img = comp(img, (150, 150, 150), guide.mask() * 0.5)
    ink = np.zeros((h, w), np.float32)
    for i, ln in enumerate(rule_lines):
        if i in lines_shown:
            ink = np.maximum(ink, rule_line_mask(ln, 52, (96, 440 + 78 * i), seed + 10 + i))
    crackle = ridged(w, h, 34, seed + 5, 0.015) * 0.5 + ridged(w, h, 70, seed + 6, 0.012) * 0.35
    img = comp(img, (150, 146, 130), crackle * 0.35)
    pin = (g.random((h, w)) > 0.9993).astype(np.float32)
    img = comp(img, (60, 56, 50), ndi.gaussian_filter(pin, 0.7) * 0.9)
    height = 0.6 + 0.04 * (fbm(w, h, 3, 3, 0.5, seed + 7) - 0.5) - 0.25 * thin - 0.02 * crackle
    rough = np.clip(0.16 + 0.1 * crackle + 0.5 * thin, 0, 1)
    fade = 1.0
    if state in ("worn", "scorched"):
        wear = np.clip((fbm(w, h, 5, 6, 0.6, seed + 8) - 0.55) / 0.3, 0, 1)
        img = comp(img, (196, 180, 150), wear * 0.25)
        chip = Canvas(w, h)
        chip.poly([(w - 1, 0), (w - 70, 0), (w - 1, 60)])
        cm = ndi.gaussian_filter(chip.mask(), 2) * (fbm(w, h, 4, 10, 0.6, seed + 9) > 0.3)
        img = comp(img, (176, 106, 76), cm)
        height -= 0.3 * cm
        rough = np.clip(rough + 0.25 * wear + 0.6 * cm, 0, 1)
        fade = 0.7
    img, ink_a = apply_ink(img, ink, INK, seed + 11, density=0.95 * fade)
    rough = rough * (1 - ink_a) + 0.3 * ink_a
    if state == "scorched":
        d = np.hypot(xx - w * 0.05, yy - h * 0.95) / (w * 0.9)
        soot = np.clip(1 - d, 0, 1) ** 1.4 * (0.6 + 0.6 * fbm(w, h, 5, 6, 0.6, seed + 12))
        img = comp(img, (34, 28, 24), np.clip(soot, 0, 0.92))
        rough = np.clip(rough + 0.5 * soot, 0, 1)
    return img, rough, np.clip(height, 0, 1)


def build_tiles():
    for rule, (_, lines) in RULES.items():
        img, rough, height = tile(rule, list(range(len(lines))), "fresh", seed=hash(rule) % 1000)
        save_maps(f"tile_{rule}", albedo=img, rough=rough, height=height)
    img, rough, height = tile("R1", [0], "fresh", seed=301)
    save_maps("tile_R1_partial", albedo=img, rough=rough, height=height)
    img, rough, height = tile("R3", [], "fresh", seed=302)
    save_maps("tile_R3_blank", albedo=img, rough=rough, height=height)
    img, rough, height = tile("R2", [0, 1], "worn", seed=303)
    save_maps("tile_R2_worn", albedo=img, rough=rough, height=height)
    img, rough, height = tile("R6", [0, 1, 2], "scorched", seed=304)
    save_maps("tile_R6_scorched", albedo=img, rough=rough, height=height)


# ---------------------------------------------------------------- book cover (menu)
def semse(w, h, cx, cy, rx, ry, lobes=22, pend=True):
    c = Canvas(w, h)
    pts = []
    for k in range(240):
        a = 2 * math.pi * k / 240
        r = 1 + 0.035 * abs(math.sin(lobes * a / 2))
        pts.append((cx + rx * r * math.sin(a) * abs(math.sin(a)) ** 0.15, cy - ry * r * math.cos(a)))
    c.poly(pts)
    if pend:
        for sgn in (-1, 1):
            c.ellipse(cx, cy + sgn * (ry + 40), 34, 30)
            c.poly([(cx - 10, cy + sgn * ry), (cx + 10, cy + sgn * ry), (cx, cy + sgn * (ry + 90))])
            c.ellipse(cx, cy + sgn * (ry + 96), 9, 9)
    return ndi.gaussian_filter(c.mask(), 1.0)


def book_cover(seed=61):
    w, h = 1400, 2000
    n1, n2 = fbm(w, h, 6, 4, 0.6, seed), fbm(w, h, 4, 2, 0.5, seed + 1)
    grain = ridged(w, h, 140, seed + 2, 0.08) * 0.6 + fbm(w, h, 3, 220, 0.6, seed + 3) * 0.4
    img = np.array((96, 40, 28), np.float32) * (0.8 + 0.25 * n1[..., None] + 0.06 * grain[..., None])
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    wear = np.clip(1 - (edge + (n2 - 0.5) * 60) / 70, 0, 1) ** 1.2
    img = comp(img, (150, 96, 64), wear * 0.55)
    hand = np.exp(-(((xx - w * 0.82) / (w * 0.2)) ** 2 + ((yy - h * 0.5) / (h * 0.25)) ** 2))
    img = comp(img, (60, 26, 20), hand * 0.35)                       # darkened where it is held
    scuff = Canvas(w, h, 1)
    g = np.random.default_rng(seed)
    for _ in range(160):
        x, y = g.uniform(0, w), g.uniform(0, h)
        a, L = g.uniform(0, math.pi), g.uniform(10, 70)
        scuff.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], 1, fill=int(g.uniform(60, 180)))
    img = comp(img, (160, 110, 80), scuff.mask() * 0.5)
    height = 0.55 + 0.04 * grain + 0.02 * n1
    rough = np.clip(0.5 + 0.2 * grain - 0.2 * hand, 0, 1)
    metal = np.zeros((h, w), np.float32)
    gold, grough, gmetal = gilding(w, h, seed + 4, burnish=0.4)
    gold = comp(gold, (196, 156, 76), (gold[..., 0] < 170).astype(np.float32) * 0.85)   # no red bole on a binding

    def gild(m, relief=-0.08):
        nonlocal img, rough, metal, height
        img = comp(img, gold, m)
        rough = rough * (1 - m) + grough * m
        metal = np.maximum(metal, gmetal * m)
        height = height + relief * m

    tool = Canvas(w, h)
    for inset in (70, 84, 160):
        tool.line([(inset, inset), (w - inset, inset), (w - inset, h - inset), (inset, h - inset), (inset, inset)], 3)
    tm = tool.mask()
    height -= 0.12 * blur(tm, 1.2)
    img = comp(img, (54, 22, 16), tm * 0.6)
    chain = Canvas(w, h)
    for t in np.arange(0, 1, 0.012):
        for (xa, ya, xb, yb) in ((120, 120, w - 120, 120), (120, h - 120, w - 120, h - 120), (120, 120, 120, h - 120), (w - 120, 120, w - 120, h - 120)):
            x, y = xa + (xb - xa) * t, ya + (yb - ya) * t
            chain.poly([(x, y - 9), (x + 9, y), (x, y + 9), (x - 9, y)])
    gild(chain.mask())
    sm = semse(w, h, w / 2, h / 2, 330, 520)
    gild(sm)
    fl = spiral_ground(w, h, sm, seed + 5, 34, [(120, 80, 30), (150, 100, 40)], line=(80, 50, 20))
    relief = np.clip(fl["vine"] + fl["leaf"] + sum(m for m, _ in fl["petals"]), 0, 1)
    img = comp(img, (128, 88, 40), relief * 0.55)
    height += 0.05 * relief
    for cx, cy, sx, sy in ((0, 0, 1, 1), (w, 0, -1, 1), (0, h, 1, -1), (w, h, -1, -1)):
        corner = semse(w, h, cx + sx * 160, cy + sy * 160, 260, 260, 18, pend=False)
        quad = ((xx - cx) * sx > 160) & ((yy - cy) * sy > 160)
        gild(corner * quad)
    car = cloud_cartouche(w, h, w / 2, h / 2, 360, 84, lobes=3)
    img = comp(img, np.array((88, 34, 24), np.float32) * (0.9 + 0.2 * n1[..., None]), car)
    rough = rough * (1 - car) + 0.45 * car
    metal = metal * (1 - car)
    title = text_mask(w, h, ["Ses Kayması"], 84, (w / 2, h / 2 + 28), 0, seed=seed + 6, wobble=0.3)
    gild(title, -0.05)
    img = comp(img, (40, 20, 12), outline((car > 0.5).astype(np.float32), 1.2) * 0.6)
    gild(np.clip(ndi.gaussian_filter((car > 0.5).astype(np.float32), 3) * 3, 0, 1) * (1 - (car > 0.5)))
    save_maps("menu_cover", albedo=img, rough=rough, metal=metal, height=np.clip(height, 0, 1))


def slips():
    """Paper bookmark slips sticking out of the book: the menu entries."""
    from tex_core import paper
    for i, word in enumerate(["Başla", "Devam", "Ayarlar", "Çık"]):
        w, h = 420, 150
        img, _ = paper(w, h, 70 + i, tone=(236, 226, 200), age=0.6, laid=False)
        tm = text_mask(w, h, [word], 70, (w / 2, 100), 0, seed=80 + i, wobble=0.4)
        img, _ = apply_ink(img, tm, INK, 90 + i)
        save_rgb(img, OUT / f"menu_slip_{i + 1}_albedo.png")


# ---------------------------------------------------------------- sleeves
def weave(w, h, seed, period=6.0, slub=0.3):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    warp = 0.5 + 0.5 * np.sin(xx * 2 * math.pi / period)
    weft = 0.5 + 0.5 * np.sin(yy * 2 * math.pi / period)
    check = ((xx // (period / 2) + yy // (period / 2)) % 2)
    tex = 0.5 * (warp * check + weft * (1 - check))
    slubs = np.clip((fbm(w, h, 4, 60, 0.6, seed) - 0.6) / 0.3, 0, 1) * slub
    return tex, slubs


def fabric_linen(seed=71):
    w = h = 1024
    tex, slubs = weave(w, h, seed, 5.0, 0.5)
    img = np.array((210, 196, 166), np.float32) * (0.86 + 0.14 * tex[..., None] + 0.08 * slubs[..., None])
    band = (np.arange(h)[:, None] < 230) * np.ones((1, w))
    stripes = Canvas(w, h)
    for y0, y1 in ((40, 70), (190, 215)):
        stripes.poly([(0, y0), (w, y0), (w, y1), (0, y1)])
    loz = Canvas(w, h)
    for x in np.arange(0, w + 40, 64):
        loz.poly([(x, 130), (x + 26, 100), (x + 52, 130), (x + 26, 160)])
    img = comp(img, np.array((38, 52, 96), np.float32) * (0.8 + 0.3 * tex[..., None]), stripes.mask() * band)
    img = comp(img, np.array((150, 54, 40), np.float32) * (0.8 + 0.3 * tex[..., None]), loz.mask())
    dirt = np.clip(1 - np.arange(h)[:, None] / 300.0, 0, 1) * fbm(w, h, 4, 6, 0.6, seed + 1)
    img = comp(img, (110, 92, 70), dirt * 0.35)
    save_maps("sleeve_linen", albedo=img, rough=np.full((h, w), 0.85, np.float32), height=0.5 + 0.2 * tex)


def fabric_kemha(seed=72):
    """Crimson silk brocade with gold-thread cintamani (three pearls, two waves)."""
    w = h = 1024
    tex, _ = weave(w, h, seed, 3.0, 0.1)
    img = np.array((128, 22, 28), np.float32) * (0.85 + 0.2 * tex[..., None])
    sheen = fbm(w, h, 3, 3, 0.5, seed + 1)
    img = img * (0.85 + 0.3 * sheen[..., None])
    c = Canvas(w, h)
    for j, y in enumerate(np.arange(60, h, 170)):
        for x in np.arange(60 + (j % 2) * 128, w + 128, 256):
            for dx, dy in ((-22, 0), (22, 0), (0, -36)):
                c.ellipse(x + dx, y + dy, 17, 17)
            for k in (0, 1):
                wave = [(x - 60 + t * 120, y + 46 + 22 * k + 9 * math.sin(t * 4 * math.pi)) for t in np.linspace(0, 1, 30)]
                c.line(wave, 7)
    m = c.mask()
    gold, grough, gmetal = gilding(w, h, seed + 2, burnish=0.2)
    img = comp(img, gold * (0.85 + 0.25 * tex[..., None]), m)
    rough = np.clip(0.38 + 0.1 * tex, 0, 1) * (1 - m) + 0.5 * m
    save_maps("sleeve_kemha", albedo=img, rough=rough, metal=m * 0.8, height=0.5 + 0.15 * tex + 0.15 * m)


def fabric_felt(seed=73):
    w = h = 1024
    n = fbm(w, h, 6, 60, 0.65, seed)
    fib = ridged(w, h, 120, seed + 1, 0.06)
    img = np.array((86, 72, 58), np.float32) * (0.75 + 0.35 * n[..., None] + 0.1 * fib[..., None])
    band = Canvas(w, h)
    for x in np.arange(0, w + 60, 60):
        band.line([(x, 60), (x + 30, 120), (x + 60, 60)], 9)
    bm = band.mask()
    img = comp(img, (150, 60, 36), bm * 0.9)
    img = comp(img, (186, 140, 70), (np.arange(h)[:, None] < 30) * np.ones((1, w)) * 0.8)
    soot = np.clip((fbm(w, h, 5, 5, 0.6, seed + 2) - 0.55) / 0.3, 0, 1)
    img = comp(img, (36, 30, 26), soot * 0.5)
    save_maps("sleeve_felt", albedo=img, rough=np.full((h, w), 0.95, np.float32), height=0.5 + 0.2 * n + 0.1 * bm)


def build_all():
    OUT.mkdir(parents=True, exist_ok=True)
    build_tiles()
    book_cover()
    slips()
    fabric_linen()
    fabric_kemha()
    fabric_felt()


if __name__ == "__main__":
    import time
    t = time.time()
    build_all()
    print("props", round(time.time() - t, 1), "s")
