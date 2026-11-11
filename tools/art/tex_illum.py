"""Era 2 hero document: an illuminated palace page ("Kurucuların kaydı").

Layout after Ottoman serlevha pages (cf. the Fatiha opening Burak sent): wide
margins; a gilded headpiece (unvan) with a lapis cartouche; the two lines of
text inside gold-outlined clouds (bulut) on a ground of spiral scrolls; side
panels with gold ogee medallions; a footer panel; a running border; blue
finials (tig) on the outside; a palace seal in the margin; centuries of use.
"""
import math

import numpy as np
from scipy import ndimage as ndi

from tex_core import (GOLD, INK, LAPIS, OUT, TURQ, VERMILION, WHITE_LEAD, Canvas, apply_ink, blur, comp,
                      fbm, foxing, gilding, outline, paper, pigment, ridged, rotated_text, save_gray,
                      save_rgb, stains, text_mask, thumb_grime, wormholes, font)

W, H = 1800, 2600
TB = (290, 280, 1510, 2010)          # text block: x0, y0, x1, y1


def rect(w, h, box):
    m = np.zeros((h, w), np.float32)
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    m[y0:y1, x0:x1] = 1
    return m


def floral(w, h, region, seed, density=1.0, palette=None, scale=1.0):
    """Vines, five-petal blossoms, leaves and white dots, each outlined (tahrir)."""
    g = np.random.default_rng(seed)
    palette = palette or [(176, 60, 46), (52, 76, 146), (236, 228, 210), (204, 128, 118), (60, 118, 112)]
    vine, leaf, petals, centres, dots = Canvas(w, h), Canvas(w, h), [Canvas(w, h) for _ in palette], Canvas(w, h), Canvas(w, h)
    ys, xs = np.nonzero(region > 0.5)
    if len(xs) == 0:
        return None
    area = len(xs)
    for _ in range(int(area / 2400 * density)):
        i = g.integers(len(xs))
        x, y = float(xs[i]), float(ys[i])
        a, turn, pts = g.uniform(0, 2 * math.pi), g.choice([-1, 1]), []
        for k in range(34):
            a += turn * (0.06 + 0.014 * k)
            step = max(2.0, 9 - 0.2 * k) * scale
            x, y = x + step * math.cos(a), y + step * math.sin(a)
            pts.append((x, y))
        vine.line(pts, 1.5 * scale)
    for _ in range(int(area / 620 * density)):
        i = g.integers(len(xs))
        x, y = float(xs[i]), float(ys[i])
        a, L, wd = g.uniform(0, 2 * math.pi), g.uniform(7, 12) * scale, g.uniform(2.2, 3.6) * scale
        tip = (x + L * math.cos(a), y + L * math.sin(a))
        side = (math.cos(a + math.pi / 2) * wd, math.sin(a + math.pi / 2) * wd)
        mid = (x + 0.45 * L * math.cos(a), y + 0.45 * L * math.sin(a))
        leaf.poly([(x, y), (mid[0] + side[0], mid[1] + side[1]), tip, (mid[0] - side[0], mid[1] - side[1])])
    for _ in range(int(area / 1050 * density)):
        i = g.integers(len(xs))
        cx, cy = float(xs[i]), float(ys[i])
        r = g.uniform(5, 10) * scale
        c = g.integers(len(palette))
        rot = g.uniform(0, 2 * math.pi)
        n = int(g.choice([5, 5, 6, 8]))
        for k in range(n):
            a = rot + 2 * math.pi * k / n
            petals[c].ellipse(cx + 0.55 * r * math.cos(a), cy + 0.55 * r * math.sin(a), 0.5 * r, 0.5 * r)
        centres.ellipse(cx, cy, 0.28 * r, 0.28 * r)
    for _ in range(int(area / 500 * density)):
        i = g.integers(len(xs))
        dots.ellipse(float(xs[i]), float(ys[i]), 0.9 * scale, 0.9 * scale)
    return dict(vine=vine.mask() * region, leaf=leaf.mask() * region, centres=centres.mask() * region,
                dots=dots.mask() * region, petals=[(p.mask() * region, col) for p, col in zip(petals, palette)])


def paint_floral(img, fl, seed):
    h, w = img.shape[:2]
    img = comp(img, (98, 66, 34), fl["vine"] * 0.85)
    img = comp(img, pigment(w, h, (92, 116, 84), seed, 0.25), fl["leaf"])
    img = comp(img, (40, 34, 26), outline(fl["leaf"], 0.8) * 0.6)
    for k, (m, col) in enumerate(fl["petals"]):
        img = comp(img, pigment(w, h, col, seed + k, 0.22), m * 0.96)
        img = comp(img, (36, 28, 22), outline(m, 0.7) * 0.55)
    img = comp(img, (226, 178, 70), fl["centres"])
    img = comp(img, (246, 240, 226), fl["dots"] * 0.9)
    return img


def frame_lines(w, h, box, spec):
    """spec: list of (inset, width, colour) rules drawn as rectangles."""
    out = []
    for inset, width, col in spec:
        c = Canvas(w, h)
        x0, y0, x1, y1 = box[0] - inset, box[1] - inset, box[2] + inset, box[3] + inset
        c.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], width)
        out.append((c.mask(), col))
    return out


def cloud_cartouche(w, h, cx, cy, rw, rh, lobes=3):
    """A lobed cloud collar: a long oval whose ends break into lobes."""
    c = Canvas(w, h)
    c.ellipse(cx, cy, rw * 0.78, rh)
    for side in (-1, 1):
        for k in range(lobes):
            t = (k - (lobes - 1) / 2) / max(1, lobes - 1)
            lx = cx + side * (rw * 0.80 - abs(t) * rw * 0.10)
            ly = cy + t * rh * 1.1
            c.ellipse(lx, ly, rh * 0.42, rh * 0.42)
        c.ellipse(cx + side * rw * 0.93, cy, rh * 0.30, rh * 0.30)
    return ndi.gaussian_filter(c.mask(), 1.0)


def rosette(w, h, cx, cy, r):
    gold_c, petal_c, centre_c = Canvas(w, h), Canvas(w, h), Canvas(w, h)
    gold_c.ellipse(cx, cy, r, r)
    for k in range(8):
        a = 2 * math.pi * k / 8
        petal_c.ellipse(cx + 0.55 * r * math.cos(a), cy + 0.55 * r * math.sin(a), 0.3 * r, 0.3 * r)
    centre_c.ellipse(cx, cy, 0.26 * r, 0.26 * r)
    return gold_c.mask(), petal_c.mask(), centre_c.mask()


def tig(w, h, x0, x1, y, up=True, step=13, seed=4):
    """Blue finials rising from a headpiece border."""
    g = np.random.default_rng(seed)
    c = Canvas(w, h)
    sgn = -1 if up else 1
    n = int((x1 - x0) / step)
    for i in range(n + 1):
        x = x0 + i * step
        k = i % 6
        L = [58, 26, 40, 26, 46, 26][k] * (0.96 + 0.08 * g.random())
        c.line([(x, y), (x, y + sgn * L)], 1.6)
        c.ellipse(x, y + sgn * (L + 3), 2.2, 3.6)
    return c.mask()


def arc_text(w, h, text, cx, cy, r, size, start_deg, seed=0):
    """Text set along a circle, for seal impressions."""
    from PIL import Image, ImageDraw
    f = font(size)
    canvas = Image.new("L", (w, h), 0)
    total = sum(f.getlength(ch) for ch in text)
    ang = math.radians(start_deg) - total / r / 2
    for ch in text:
        cw = f.getlength(ch)
        a = ang + cw / r / 2
        im = Image.new("L", (int(size * 2), int(size * 2)), 0)
        ImageDraw.Draw(im).text((size, size * 1.2), ch, font=f, fill=255, anchor="ms")
        im = im.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        canvas.paste(255, (int(px - size), int(py - size)), im)
        ang += cw / r
    return np.asarray(canvas).astype(np.float32) / 255


def seal(w, h, cx, cy, r, text, seed):
    c = Canvas(w, h)
    c.ellipse(cx, cy, r, r)
    ring = c.mask()
    c2 = Canvas(w, h)
    c2.ellipse(cx, cy, r - 7, r - 7)
    ring = np.clip(ring - c2.mask(), 0, 1)
    c3 = Canvas(w, h)
    c3.ellipse(cx, cy, r * 0.52, r * 0.52)
    c4 = Canvas(w, h)
    c4.ellipse(cx, cy, r * 0.52 - 4, r * 0.52 - 4)
    ring2 = np.clip(c3.mask() - c4.mask(), 0, 1)
    star = Canvas(w, h)
    pts = []
    for k in range(16):
        a = math.pi * k / 8 - math.pi / 2
        rr = r * (0.36 if k % 2 == 0 else 0.16)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    star.poly(pts)
    txt = arc_text(w, h, text, cx, cy, r * 0.72, int(r * 0.34), -90, seed)
    m = np.clip(ring + ring2 + star.mask() + txt, 0, 1)
    n = fbm(w, h, 4, 60, 0.6, seed)
    return m * np.clip(0.55 + 0.6 * n, 0, 1)        # uneven pressure


def landscape(w, h, box, seed=21):
    """Persian-style landscape for the miniature panel: gold sky, cloud bands,
    spongy pastel rocks, a tarnished silver stream, cypress and blossom tree.
    Returns colour, gold mask and a silver mask (for the material)."""
    g = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    pw, ph = x1 - x0, y1 - y0
    region = np.zeros((h, w), np.float32)
    region[y0:y1, x0:x1] = 1
    img = np.zeros((h, w, 3), np.float32)
    gold_mask = np.zeros((h, w), np.float32)
    silver = np.zeros((h, w), np.float32)
    xs = np.arange(w, dtype=np.float32)

    horizon = y0 + ph * 0.36
    sky = np.zeros((h, w), np.float32)
    sky[y0:int(horizon) + 40, x0:x1] = 1
    gold_mask = np.maximum(gold_mask, sky)

    # cloud bands on the gold sky
    clouds = Canvas(w, h)
    for k in range(2):
        cx = x0 + pw * (0.25 + 0.45 * k)
        cy = y0 + ph * (0.10 + 0.07 * k)
        for t in np.linspace(-1, 1, 15):
            clouds.ellipse(cx + t * pw * 0.13, cy + math.sin(t * 3.0) * ph * 0.025, ph * 0.035, ph * 0.026)
        for side in (-1, 1):
            ex = cx + side * pw * 0.14
            for j in range(6):
                a = j * 0.9
                clouds.ellipse(ex + side * math.cos(a) * ph * 0.02 * (1 + j * 0.15), cy - math.sin(a) * ph * 0.02 * (1 + j * 0.15), ph * 0.012, ph * 0.012)
    cl = clouds.mask() * region
    gold_mask = np.clip(gold_mask - cl, 0, 1)

    layers = [((176, 156, 190), 0.30, 0.10), ((214, 164, 150), 0.42, 0.12), ((206, 176, 120), 0.55, 0.09)]
    rock_masks = []
    for i, (col, base, amp) in enumerate(layers):
        top = y0 + ph * base + ph * amp * np.sin(xs / pw * (5 + 2 * i) + g.uniform(0, 6)) * np.sin(xs / pw * 1.7 + i)
        bumps = (np.abs(np.sin(xs / (pw / (22 + 6 * i)) + i)) ** 0.5) * ph * 0.018
        top = top - bumps
        yy = np.arange(h, dtype=np.float32)[:, None]
        m = (yy > top[None, :]).astype(np.float32) * region
        m = ndi.gaussian_filter(m, 1.0)
        rock_masks.append((m, col))
    ground_top = y0 + ph * 0.66 + ph * 0.02 * np.sin(xs / pw * 3.0)
    ground = ((np.arange(h, dtype=np.float32)[:, None] > ground_top[None, :]).astype(np.float32)) * region

    # colour the sky region gold later (via material); paint a base here
    img = comp(img, GOLD, sky * region)
    img = comp(img, (242, 238, 230), cl)
    img = comp(img, (58, 82, 150), outline(cl, 0.9) * 0.9)
    for k, (m, col) in enumerate(rock_masks):
        sponge = ridged(w, h, 70, seed + k, 0.05) * 0.5 + (fbm(w, h, 4, 50, 0.6, seed + 10 + k) > 0.62) * 0.35
        rock = pigment(w, h, col, seed + 20 + k, 0.22) * (1 - 0.18 * sponge[..., None])
        img = comp(img, rock, m)
        img = comp(img, np.array(col) * 0.5, outline(m, 1.0) * 0.9)
        gold_mask = np.clip(gold_mask - m, 0, 1)
    img = comp(img, pigment(w, h, (112, 138, 84), seed + 30, 0.25), ground)
    gold_mask = np.clip(gold_mask - ground, 0, 1)

    # grass tufts and small flowers on the ground
    tufts, flw = Canvas(w, h), Canvas(w, h)
    gy, gx = np.nonzero(ground > 0.5)
    for _ in range(int(len(gx) / 260)):
        i = g.integers(len(gx))
        x, y = float(gx[i]), float(gy[i])
        for j in range(5):
            a = -math.pi / 2 + (j - 2) * 0.28
            tufts.line([(x, y), (x + 9 * math.cos(a), y + 11 * math.sin(a))], 1.1)
        if g.random() < 0.25:
            flw.ellipse(x + 4, y - 12, 2.6, 2.6)
    img = comp(img, (70, 100, 60), tufts.mask() * 0.8)
    img = comp(img, (240, 226, 220), flw.mask())

    # stream: silver (tarnished) with wave lines
    st = Canvas(w, h)
    pts_l, pts_r = [], []
    for t in np.linspace(0, 1, 40):
        y = y0 + ph * (0.70 + 0.30 * t)
        x = x0 + pw * (0.70 + 0.10 * math.sin(t * 5)) - t * pw * 0.25
        wdt = pw * (0.025 + 0.05 * t)
        pts_l.append((x - wdt, y))
        pts_r.append((x + wdt, y))
    st.poly(pts_l + pts_r[::-1])
    silver = st.mask() * region
    waves = Canvas(w, h)
    for k in range(60):
        y = y0 + ph * (0.70 + 0.3 * k / 60)
        waves.line([(x0, y), (x1, y + 6)], 1.0)
    img = comp(img, (70, 72, 74), silver)
    img = comp(img, (140, 140, 136), waves.mask() * silver * 0.5)
    img = comp(img, (40, 40, 40), outline(silver, 1.0) * 0.8)

    # cypress and blossom tree on the middle rock
    cyp = Canvas(w, h)
    bx, by = x0 + pw * 0.16, y0 + ph * 0.62
    cyp.poly([(bx, by - ph * 0.42), (bx + pw * 0.035, by - ph * 0.15), (bx + pw * 0.03, by), (bx - pw * 0.03, by), (bx - pw * 0.035, by - ph * 0.15)])
    cm = cyp.mask()
    img = comp(img, pigment(w, h, (44, 72, 52), seed + 40, 0.3), cm)
    img = comp(img, (24, 36, 26), outline(cm, 1.0))
    trunk, bl = Canvas(w, h), Canvas(w, h)
    tx, ty = x0 + pw * 0.86, y0 + ph * 0.60
    trunk.line([(tx, ty), (tx - 6, ty - ph * 0.2), (tx + 4, ty - ph * 0.34)], 7)
    for k in range(7):
        a = -math.pi / 2 + (k - 3) * 0.42
        sx, sy = tx - 3, ty - ph * (0.14 + 0.025 * k)
        ex, ey = sx + math.cos(a) * pw * 0.07, sy + math.sin(a) * ph * 0.1
        trunk.line([(sx, sy), (ex, ey)], 2.4)
        for _ in range(16):
            bl.ellipse(ex + g.normal(0, pw * 0.02), ey + g.normal(0, ph * 0.03), 3.4, 3.4)
    img = comp(img, (82, 56, 40), trunk.mask())
    blm = bl.mask()
    img = comp(img, (238, 214, 214), blm)
    img = comp(img, (180, 110, 110), outline(blm, 0.6) * 0.5)
    return img * region[..., None], gold_mask * region, silver



def spiral_ground(w, h, region, seed, spacing=44, palette=None, line=(84, 54, 30)):
    """Helezon: a jittered grid of small spiral scrolls, each ending in a blossom,
    with leaves on the arc. Regular like a craftsman's work, never like noise."""
    g = np.random.default_rng(seed)
    palette = palette or [(40, 62, 140), (172, 58, 42), (236, 230, 214), (196, 124, 116)]
    vine, leaf, centres, dots = Canvas(w, h), Canvas(w, h), Canvas(w, h), Canvas(w, h)
    petals = [Canvas(w, h) for _ in palette]
    ys, xs = np.nonzero(region > 0.5)
    if len(xs) == 0:
        return None
    bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
    for j, cy in enumerate(np.arange(by0 + spacing / 2, by1, spacing * 0.87)):
        for i, cx in enumerate(np.arange(bx0 + spacing / 2 + (j % 2) * spacing / 2, bx1, spacing)):
            cx2, cy2 = cx + g.normal(0, 2.5), cy + g.normal(0, 2.5)
            if region[int(min(cy2, h - 1)), int(min(cx2, w - 1))] < 0.5:
                continue
            chir = 1 if (i + j) % 2 == 0 else -1
            rot = g.uniform(0, 2 * math.pi)
            turns = g.uniform(1.6, 2.1)
            pts = []
            for t in np.linspace(0.12, 1, 48):
                th = rot + chir * t * turns * 2 * math.pi
                r = spacing * 0.62 * t ** 1.1
                pts.append((cx2 + r * math.cos(th), cy2 + r * math.sin(th)))
            vine.line(pts, 1.5)
            for k in (12, 20, 28, 36, 43):
                (xa, ya), (xb, yb) = pts[k], pts[k + 1]
                a = math.atan2(yb - ya, xb - xa) + chir * 0.9
                L, wd = 6.5, 2.3
                tip = (xa + L * math.cos(a), ya + L * math.sin(a))
                mid = (xa + 0.5 * L * math.cos(a), ya + 0.5 * L * math.sin(a))
                sx, sy = math.cos(a + math.pi / 2) * wd, math.sin(a + math.pi / 2) * wd
                leaf.poly([(xa, ya), (mid[0] + sx, mid[1] + sy), tip, (mid[0] - sx, mid[1] - sy)])
            c = int(g.integers(len(palette)))
            r = g.uniform(3.6, 7.0)
            n = 5 if g.random() < 0.7 else 6
            for k in range(n):
                a = rot + 2 * math.pi * k / n
                petals[c].ellipse(cx2 + 0.58 * r * math.cos(a), cy2 + 0.58 * r * math.sin(a), 0.48 * r, 0.48 * r)
            centres.ellipse(cx2, cy2, 0.3 * r, 0.3 * r)
            ex, ey = pts[-1]
            bc = int(g.integers(len(palette)))
            for k in range(3):
                a = rot + 2 * math.pi * k / 3
                petals[bc].ellipse(ex + 2.0 * math.cos(a), ey + 2.0 * math.sin(a), 1.9, 1.9)
            mx, my = pts[24]
            dots.ellipse(mx, my, 1.1, 1.1)
    return dict(vine=vine.mask() * region, leaf=leaf.mask() * region, centres=centres.mask() * region,
                dots=dots.mask() * region, petals=[(p.mask() * region, col) for p, col in zip(petals, palette)])


def paint_ground(img, fl, seed):
    h, w = img.shape[:2]
    img = comp(img, (78, 50, 28), fl["vine"] * 0.9)
    img = comp(img, pigment(w, h, (84, 104, 78), seed, 0.25), fl["leaf"] * 0.95)
    img = comp(img, (36, 30, 22), outline(fl["leaf"], 0.6) * 0.5)
    for k, (m, col) in enumerate(fl["petals"]):
        img = comp(img, pigment(w, h, col, seed + k, 0.2), m * 0.95)
        img = comp(img, (32, 26, 20), outline(m, 0.6) * 0.6)
    img = comp(img, (214, 170, 72), fl["centres"])
    img = comp(img, (244, 238, 222), fl["dots"] * 0.9)
    return img


def ogee_panel(w, h, box):
    """Vertical side panel with two gold ogee medallions."""
    x0, y0, x1, y1 = box
    c = Canvas(w, h)
    cx = (x0 + x1) / 2
    for k in range(2):
        cy = y0 + (y1 - y0) * (0.27 + 0.46 * k)
        hh = (y1 - y0) * 0.21
        ww = (x1 - x0) * 0.40
        pts = []
        for t in np.linspace(-1, 1, 80):
            yv = cy + t * hh
            sgn = 1 if t >= 0 else -1
            xv = ww * (1 - abs(t) ** 1.6) ** 0.8 * (1 + 0.18 * math.sin(abs(t) * math.pi))
            pts.append((cx + xv, yv))
        pts += [(2 * cx - x, y) for x, y in pts[::-1]]
        c.poly(pts)
        c.ellipse(cx, cy - hh - 8, 5, 8)
        c.ellipse(cx, cy + hh + 8, 5, 8)
    return c.mask()


def running_border(w, h, box, width, seed):
    """Zencerek-like band: lapis ground with gold lozenge-and-dot chain."""
    x0, y0, x1, y1 = box
    outer = rect(w, h, (x0 - width, y0 - width, x1 + width, y1 + width))
    band = np.clip(outer - rect(w, h, box), 0, 1)
    chain = Canvas(w, h)
    step = width * 1.25
    def along(xa, ya, xb, yb):
        L = math.hypot(xb - xa, yb - ya)
        n = int(L / step)
        for k in range(n + 1):
            t = k / max(1, n)
            x, y = xa + (xb - xa) * t, ya + (yb - ya) * t
            r = width * 0.36
            chain.poly([(x, y - r), (x + r, y), (x, y + r), (x - r, y)])
    m = width / 2
    along(x0 - m, y0 - m, x1 + m, y0 - m)
    along(x0 - m, y1 + m, x1 + m, y1 + m)
    along(x0 - m, y0 - m, x0 - m, y1 + m)
    along(x1 + m, y0 - m, x1 + m, y1 + m)
    return band, chain.mask() * band


def finials(w, h, box, gap, step=12, seed=4):
    """Tig: fine lapis strokes radiating from the outer border."""
    g = np.random.default_rng(seed)
    c = Canvas(w, h)
    x0, y0, x1, y1 = box
    pattern = [34, 14, 22, 14, 26, 14]
    def stroke(x, y, dx, dy, k):
        L = pattern[k % 6] * (0.95 + 0.1 * g.random())
        ex, ey = x + dx * L, y + dy * L
        c.line([(x, y), (ex, ey)], 1.15)
        c.ellipse(ex + dx * 2.5, ey + dy * 2.5, 1.7 if dx == 0 else 2.6, 2.6 if dx == 0 else 1.7)
    for k, x in enumerate(np.arange(x0, x1 + 1, step)):
        stroke(x, y0 - gap, 0, -1, k)
        stroke(x, y1 + gap, 0, 1, k)
    for k, y in enumerate(np.arange(y0, y1 + 1, step)):
        stroke(x0 - gap, y, -1, 0, k)
        stroke(x1 + gap, y, 1, 0, k)
    return c.mask()


LAPIS_DEEP = (30, 46, 118)


def lapis(w, h, seed):
    base = pigment(w, h, LAPIS_DEEP, seed, 0.34)
    speck = (np.random.default_rng(seed).random((h, w)) > 0.993).astype(np.float32)
    base = comp(base, (70, 96, 176), ndi.gaussian_filter(speck, 0.6) * 0.8)
    return base


def build(out_dir=OUT, seed=7):
    out_dir.mkdir(parents=True, exist_ok=True)
    img, height = paper(W, H, seed, tone=(236, 224, 194), age=0.6)
    rough = np.full((H, W), 0.62, np.float32)
    metal = np.zeros((H, W), np.float32)
    gold_layer, gold_rough, gold_metal = gilding(W, H, seed + 1, burnish=0.7)
    hatch = np.sin((np.arange(W)[None, :] + np.arange(H)[:, None]) * (2 * math.pi / 4.0)) * 0.5 + 0.5
    gold_layer = gold_layer * (1 - 0.06 * hatch[..., None])

    def lay_gold(mask, relief=0.02):
        nonlocal img, rough, metal, height
        mask = np.clip(mask, 0, 1)
        img = comp(img, gold_layer, mask)
        rough = rough * (1 - mask) + gold_rough * mask
        metal = np.maximum(metal, gold_metal * mask)
        height = height + relief * mask

    def ring_outside(m, r=4):
        b = (m > 0.5).astype(np.float32)
        return np.clip(ndi.gaussian_filter(b, r) * 3, 0, 1) * (1 - b)

    X0, X1 = 270, 1530
    head = (X0, 560, X1, 880)
    body = (X0, 880, X1, 1620)
    foot = (X0, 1620, X1, 1820)
    side_w = 128
    text_box = (X0 + side_w, body[1], X1 - side_w, body[3])

    # ---- headpiece
    hp = rect(W, H, head)
    hcx, hcy = (X0 + X1) / 2, (head[1] + head[3]) / 2
    car = cloud_cartouche(W, H, hcx, hcy, 300, 78)
    meds = np.zeros((H, W), np.float32)
    for sx in (X0 + 95, X1 - 95):
        c = Canvas(W, H)
        c.ellipse(sx, hcy, 58, 92)
        meds = np.maximum(meds, c.mask())
    ground = np.clip(hp - ring_outside(car, 3) - (car > 0.5) - ring_outside(meds, 3) - (meds > 0.5), 0, 1)
    lay_gold(ground)
    img = paint_ground(img, spiral_ground(W, H, ground, seed + 2, 31), seed + 3)
    img = comp(img, lapis(W, H, seed + 4), car)
    img = comp(img, pigment(W, H, TURQ, seed + 5, 0.26), meds)
    img = paint_ground(img, spiral_ground(W, H, meds * 0.99, seed + 6, 34, [(236, 230, 214), (172, 58, 42), (226, 186, 80)]), seed + 7)
    for m in (car, meds):
        lay_gold(ring_outside(m, 3))
        img = comp(img, (20, 18, 16), outline((m > 0.5).astype(np.float32), 1.0) * 0.9)
    title = text_mask(W, H, ["Kerdāgros"], 112, (hcx, hcy + 38), 0, seed=seed + 8, wobble=0.4)
    lay_gold(title, 0.03)
    img = comp(img, (26, 20, 14), outline(title, 0.8) * 0.9)

    # ---- body: side panels with ogees, text in clouds on spiral ground
    for sx0 in (X0, X1 - side_w):
        box = (sx0, body[1], sx0 + side_w, body[3])
        panel = rect(W, H, box)
        img = comp(img, pigment(W, H, TURQ, seed + 9, 0.26), panel)
        og = ogee_panel(W, H, (box[0] + 14, box[1] + 10, box[2] - 14, box[3] - 10))
        lay_gold(og)
        img = paint_ground(img, spiral_ground(W, H, og * 0.99, seed + 10 + sx0, 26), seed + 11)
        img = comp(img, (20, 18, 16), outline(og, 0.9) * 0.9)
        for m, col in frame_lines(W, H, box, [(0, 2.2, (20, 18, 16))]):
            img = comp(img, np.array(col, np.float32), m)
    tb = rect(W, H, text_box)
    lines = ["Mīros Mērom ageti.", "Mēros nākos."]
    size, lead = 100, 290
    tcx = (text_box[0] + text_box[2]) / 2 - 26
    cy0 = body[1] + 275
    tm = text_mask(W, H, lines, size, (tcx, cy0), lead, seed=seed + 12, wobble=0.6)
    env = ndi.binary_dilation(tm > 0.2, iterations=24)
    env = ndi.gaussian_filter(env.astype(np.float32), 16) > 0.3
    env = ndi.gaussian_filter(env.astype(np.float32), 1.2) * tb
    tground = np.clip(tb - ring_outside(env, 4) - (env > 0.5), 0, 1)
    lay_gold(tground)
    img = paint_ground(img, spiral_ground(W, H, tground, seed + 13, 31), seed + 14)
    lay_gold(ring_outside(env, 4) * tb)
    img = comp(img, (22, 18, 14), outline((env > 0.5).astype(np.float32), 1.0) * tb * 0.9)
    img, ink_a = apply_ink(img, tm, INK, seed + 15)
    rough = rough * (1 - ink_a) + 0.34 * ink_a
    height = height + 0.012 * ink_a
    f = font(size)
    for i, line in enumerate(lines):
        rx = tcx + f.getlength(line) / 2 + 56
        ry = cy0 + i * lead - size * 0.3
        gm, pm, cm = rosette(W, H, rx, ry, 26)
        lay_gold(gm)
        img = comp(img, lapis(W, H, seed + 16), pm)
        img = comp(img, (176, 52, 40), cm)
        img = comp(img, (22, 18, 14), outline(gm, 0.8))

    # ---- footer
    fp = rect(W, H, foot)
    fcx, fcy = (X0 + X1) / 2, (foot[1] + foot[3]) / 2
    fcar = cloud_cartouche(W, H, fcx, fcy, 170, 46, lobes=2)
    fground = np.clip(fp - ring_outside(fcar, 3) - (fcar > 0.5), 0, 1)
    lay_gold(fground)
    img = paint_ground(img, spiral_ground(W, H, fground, seed + 17, 31), seed + 18)
    img = comp(img, lapis(W, H, seed + 19), fcar)
    img = paint_ground(img, spiral_ground(W, H, fcar * 0.99, seed + 20, 30, [(236, 230, 214), (226, 186, 80)]), seed + 21)
    lay_gold(ring_outside(fcar, 3))
    img = comp(img, (20, 18, 16), outline((fcar > 0.5).astype(np.float32), 1.0) * 0.9)

    # ---- rules, running border, finials
    block = (X0, head[1], X1, foot[3])
    for yy in (head[3], body[3]):
        c = Canvas(W, H)
        c.line([(X0, yy), (X1, yy)], 6)
        lay_gold(c.mask())
        c2 = Canvas(W, H)
        c2.line([(X0, yy - 3.5), (X1, yy - 3.5)], 1.2)
        c2.line([(X0, yy + 3.5), (X1, yy + 3.5)], 1.2)
        img = comp(img, (20, 18, 16), c2.mask())
    for m, col in frame_lines(W, H, block, [(0, 2.4, (20, 18, 16)), (6, 7, None), (10, 2.0, (20, 18, 16))]):
        if col is None:
            lay_gold(m)
        else:
            img = comp(img, np.array(col, np.float32), m)
    bbox = (block[0] - 12, block[1] - 12, block[2] + 12, block[3] + 12)
    band, chain = running_border(W, H, bbox, 34, seed + 22)
    img = comp(img, lapis(W, H, seed + 23), band)
    lay_gold(chain)
    img = comp(img, (20, 18, 16), outline(chain, 0.7) * 0.8)
    outer = (bbox[0] - 34, bbox[1] - 34, bbox[2] + 34, bbox[3] + 34)
    for m, col in frame_lines(W, H, outer, [(0, 2.2, (20, 18, 16)), (5, 4, None), (14, 1.6, LAPIS)]):
        if col is None:
            lay_gold(m)
        else:
            img = comp(img, np.array(col, np.float32), m)
    img = comp(img, np.array(LAPIS_DEEP, np.float32) * 1.3, finials(W, H, outer, 22, 12, seed + 24) * 0.95)

    # ---- the palace seal, the reader's thumb, worms and water
    sm = seal(W, H, 1380, 2250, 84, "Kerdēgros", seed + 25)
    sm *= np.clip(0.4 + 1.2 * fbm(W, H, 3, 3, 0.5, seed + 26), 0, 1)
    img = comp(img, (78, 36, 30), sm * 0.85)
    img = comp(img, (176, 132, 84), stains(W, H, seed + 27, 1, (0.06, 0.12)) * 0.22)
    img = comp(img, (150, 100, 56), foxing(W, H, seed + 28, 90) * 0.45)
    img = comp(img, (108, 84, 60), thumb_grime(W, H, seed + 29, (1, 1), 0.3) * 0.4)
    hole, halo = wormholes(W, H, seed + 30, tunnels=2, holes=7, scale=1.2)
    lower = np.zeros((H, W), np.float32)
    lower[2080:, :] = 1
    hole, halo = hole * lower, halo * lower
    img = comp(img, (118, 82, 48), halo * 0.6)
    alpha = np.clip(1 - hole * 1.2, 0, 1)
    green = np.clip(ndi.gaussian_filter((meds > 0.5).astype(np.float32), 8) - (meds > 0.5) * 0.6, 0, 1)
    img = comp(img, (120, 104, 60), green * 0.35)      # verdigris eating into the paper

    save_rgb(img, out_dir / "era2_illum_albedo.png")
    save_gray(np.clip(rough, 0, 1), out_dir / "era2_illum_rough.png")
    save_gray(np.clip(metal, 0, 1), out_dir / "era2_illum_metal.png")
    save_gray(np.clip(height, 0, 1), out_dir / "era2_illum_height.png")
    save_gray(alpha, out_dir / "era2_illum_alpha.png")
    return img


if __name__ == "__main__":
    import time
    t = time.time()
    build()
    print("illuminated page", round(time.time() - t, 1), "s")
