"""The game's look: a classical Ottoman miniature (after Nakkaş Osman) of the
scribe's desk, seen straight from above. Rules: assets/art/STYLE.md.

    python3 tools/art/minyatur.py            every sprite of the second era
    python3 tools/art/minyatur.py masa tepsi only the named ones
    python3 tools/art/minyatur.py --sheet    a contact sheet for looking at

Everything is drawn here as a display list (nakkas.py) and painted by the same
pigment pass, so every object comes from one hand. Each sprite also leaves a
layered SVG in assets/art/style/sprites_src for touching up in Illustrator.
"""
import math
import sys
from pathlib import Path

import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image
from scipy import ndimage as ndi

import nakkas as nk
from nakkas import (G, LINE, almond, arc, bez, brush, d_of, disc, el, fill, holed, lobed, oval, place, ribbon,
                    ring, rrect, spline, stroke, xf)

ROOT = Path(__file__).resolve().parents[2]
SPR = ROOT / "assets/art/sprites"
SRC = ROOT / "assets/art/style/sprites_src"
KATIP = ROOT / "assets/fonts/Katip-Regular.ttf"
W, H = 1920, 1080
PI = math.pi

C = {
    "paper": "#ecdcb9", "paper2": "#dcc69c", "paper3": "#c7ab7e", "fresh": "#f2e7cd", "glaze": "#f4ecdb",
    "ink": "#2a1b14",
    "lapis": "#2f4d9e", "lapis_dk": "#1e3171", "lapis_lt": "#8ca4d6", "lapis_pale": "#cdd8ef",
    "red": "#b33a29", "red_dk": "#6c2a1d", "red_deep": "#4c1c13", "red_lt": "#dc8a76", "red_pale": "#f1cbbb",
    "wood": "#5a2519", "wood_dk": "#47190f", "wood_lt": "#6b2f20", "light": "#f8e2d6", "light2": "#fcefe5",
}

_font = TTFont(KATIP)
_gs = _font.getGlyphSet()
_cmap = _font.getBestCmap()


def text_path(s, x, y, size, anchor="start"):
    sc = size / 1000.0
    names = [_cmap.get(ord(c)) for c in s]
    width = sum(_gs[n].width for n in names if n) * sc
    x0 = x - width / 2 if anchor == "middle" else (x - width if anchor == "end" else x)
    pen = SVGPathPen(_gs)
    cx = x0
    for n in names:
        if n:
            _gs[n].draw(TransformPen(pen, (sc, 0, 0, -sc, cx, y)))
            cx += _gs[n].width * sc
    return pen.getCommands(), width


def text(s, x, y, size, color=None, anchor="start", rot=0.0):
    d, _ = text_path(s, x, y, size, anchor)
    att = {"d": d}
    if rot:
        att["transform"] = f"rotate({rot:.2f} {x:.1f} {y:.1f})"
    return [el("path", "ink", fill=color or C["ink"], **att)]


# ================================================================ motifs
def penc(x, y, r, n=5, color=None, eye=None, line=0.8, a0=-PI / 2):
    """A rosette seen from above (penç)."""
    out = []
    for k in range(n):
        out += fill(xf(almond(r, r * 0.8, k=0.62, base=0.4, n=9), x, y, a0 + 2 * PI * k / n), color or C["red"], line)
    out += disc(x, y, r * 0.3, eye or C["paper"], line)
    return out


def gul(x, y, r, n=6, color=None, eye=None, line=0.8):
    """A small rosette of round petals; the durak, the sentence stop."""
    out = []
    for k in range(n):
        a = 2 * PI * k / n - PI / 2
        out += disc(x + 0.56 * r * math.cos(a), y + 0.56 * r * math.sin(a), 0.4 * r, color or C["red"], line)
    out += disc(x, y, 0.34 * r, eye or C["paper"], line)
    return out


def lale(x, y, a, s=1.0, color=None, line=0.9, leaves=True):
    """The tulip of the tile painters: three pointed petals on two leaves."""
    out = []
    if leaves:
        for da in (-1.0, 1.0):
            out += fill(xf(almond(11, 4.4, k=0.5), x, y, a + da, s), C["lapis"], line * 0.8)
    for da in (-0.44, 0.44):
        out += fill(xf(almond(19, 7.5, k=0.36, sharp=1.5), x, y, a + da, s), color or C["red"], line)
    out += fill(xf(almond(22, 8, k=0.4, sharp=1.3), x, y, a, s), color or C["red"], line)
    return out


def karanfil(x, y, a, s=1.0, color=None, line=0.9):
    """The carnation: a fan of toothed petals over a calyx."""
    out = []
    for k in (-2, 2, -1, 1, 0):
        th = k * 0.36
        pts = [(4, 0)]
        for j, t in enumerate(np.linspace(th - 0.2, th + 0.2, 7)):
            rr = 21 * (1.0 if j % 2 == 0 else 0.82)
            pts.append((rr * math.cos(t), rr * math.sin(t)))
        out += fill(xf(pts, x, y, a, s), color or C["red"], line)
    out += fill(xf(almond(10, 6.5, k=0.55, base=0.5), x - 4 * s * math.cos(a), y - 4 * s * math.sin(a), a, s), C["lapis"], line)
    return out


_RUMI = spline([(0, 0), (0.3, -0.13), (0.62, -0.15), (0.88, -0.02), (0.98, 0.2), (0.86, 0.36), (0.72, 0.31)], 6)


def rumi(x, y, a, s, mirror=False, color=None, line=0.7, vein=None):
    """The split leaf: swells from the stem and curls back at its tip."""
    t = np.linspace(0, 1, len(_RUMI))
    wd = 0.92 * t ** 0.55 * (1 - t) ** 0.8
    out = fill(xf(ribbon(_RUMI, wd, (0, 0), 1.0), x, y, a, s, mirror), color or C["paper"], line)
    if vein:
        out += brush(xf(_RUMI[2:len(_RUMI) * 3 // 5], x, y, a, s, mirror), 0.9, vein, (0.3, 0.6))
    return out


def cintemani(x, y, s, ball, wave, ground):
    """Three moons and two tiger stripes."""
    out = []
    for dx, dy in ((-9, 2), (9, 2), (0, -13)):
        out += disc(x + dx * s, y + dy * s, 7 * s, ball, 0.9)
        out += disc(x + (dx + 1.9) * s, y + (dy - 1.7) * s, 3.7 * s, ground, 0)
    for k in (0, 1):
        pts = [(x + (-24 + 48 * t) * s, y + (17 + 9 * k) * s + 3.2 * s * math.sin(t * 2 * PI)) for t in np.linspace(0, 1, 20)]
        out += brush(pts, 5.4 * s, wave, (0.5, 0.5), "paint")
    return out


def zencerek(length, period=24.0, amp=5.0, w=3.0, col_a=None, col_b=None):
    """A chain of two strands, one over the other in turn, along +x."""
    n = max(2, round(length / period))
    p = length / n
    u = np.linspace(0, length, n * 16 + 1)
    a = np.stack([u, amp * np.sin(2 * PI * u / p)], 1)
    b = np.stack([u, -amp * np.sin(2 * PI * u / p)], 1)
    ca, cb = col_a or C["paper"], col_b or C["red_lt"]
    out = stroke(a, w + 1.5, cap="butt") + stroke(a, w, ca, "paint", cap="butt")
    out += stroke(b, w + 1.5, cap="butt") + stroke(b, w, cb, "paint", cap="butt")
    for k in range(0, 2 * n + 1, 2):
        uu = np.clip(np.linspace(k * p / 2 - p * 0.13, k * p / 2 + p * 0.13, 7), 0, length)
        seg = np.stack([uu, amp * np.sin(2 * PI * uu / p)], 1)
        out += stroke(seg, w + 1.5, cap="butt") + stroke(seg, w, ca, "paint", cap="butt")
    return out


def kivrik_dal(length, hb=11.0, period=92.0, amp=6.2):
    """The running vine of a carpet border, along +x and centred on y=0: a
    white stem in waves, a blossom in every bay, two split leaves beside it."""
    n = max(1, round(length / period))
    p = length / n
    u = np.linspace(0, length, n * 28 + 1)
    out = stroke(np.stack([u, amp * np.sin(2 * PI * u / p)], 1), 2.0, C["paper"], "paint")
    for k in range(2 * n):
        uc = (k + 0.5) * p / 2
        sg = 1.0 if k % 2 == 0 else -1.0
        vb = -sg * 3.4
        out += stroke([(uc, sg * amp), (uc, vb + sg * 4)], 1.5, C["paper"], "paint")
        for side in (-1.0, 1.0):
            ang = math.atan2(-sg * 4.5, side * 13.0)
            out += rumi(uc + side * 2.0, sg * (amp - 1.6), ang, 15.5, mirror=(side * sg > 0), color=C["paper"], line=0)
        if k % 2 == 0:
            out += penc(uc, vb, 5.6, 5, C["red"], C["paper"], 0.7, a0=-sg * PI / 2)
        else:
            out += penc(uc, vb, 5.2, 6, C["lapis_pale"], C["red"], 0.7, a0=-sg * PI / 2)
        out += disc(uc + p / 4, -sg * (hb - 3.2), 1.5, C["red_lt"], 0)
    return out


def kartus(cx, cy, w, h):
    """The outline of a title cartouche: a band whose ends come to an ogee point."""
    xe = w / 2 - 0.85 * h
    rho = 0.25 * h
    right = np.vstack([arc(xe, -h / 2 + rho, rho, -PI / 2, 0, 6),
                       bez((xe + rho, -h / 2 + rho), (xe + 0.42 * h, -0.25 * h), (xe + 0.55 * h, -0.04 * h), (xe + 0.85 * h, 0), 9)[1:]])
    full = np.vstack([right, (right * [1, -1])[::-1][1:]])
    return np.vstack([full, full * [-1, -1]]) + [cx, cy]


def kosebent(x, y, sx, sy, s=26.0):
    """A corner piece: a quarter medallion of three lobes."""
    th = np.linspace(0, PI / 2, 37)
    rr = s * (0.72 + 0.28 * np.abs(np.sin(6 * th)) ** 0.55)
    pts = np.vstack([[0, 0], np.stack([rr * np.cos(th), rr * np.sin(th)], 1)]) * [sx, sy] + [x, y]
    out = fill(pts, C["lapis"], 1.0)
    out += disc(x + sx * s * 0.3, y + sy * s * 0.3, s * 0.13, C["red"], 0.8)
    for a in (PI / 12, PI / 4, 5 * PI / 12):
        out += disc(x + sx * s * 0.66 * math.cos(a), y + sy * s * 0.66 * math.sin(a), s * 0.055, C["paper"], 0)
    return out


def tig(x, y, a, length, color=None, dot=True):
    """A needle of the illuminator: a hair line running out from an edge."""
    ux, uy = math.cos(a), math.sin(a)
    out = brush([(x, y), (x + ux * length * 0.5, y + uy * length * 0.5), (x + ux * length, y + uy * length)], 1.3,
                color or C["lapis"], (0.0, 0.8), wmin=0.25)
    if dot:
        out += [el("circle", "ink", fill=color or C["lapis"], cx=f"{x + ux * (length + 2.4):.1f}", cy=f"{y + uy * (length + 2.4):.1f}", r="1.0")]
    return out


def sheet(w, h, seed=0, rough=1.0):
    """A sheet of paper trimmed by hand: straight, but not ruled."""
    g = np.random.default_rng(seed)
    c, pts = 2.2, []
    for ax, ay, bx, by, nx, ny in ((c, 0, w - c, 0, 0, 1), (w, c, w, h - c, -1, 0), (w - c, h, c, h, 0, -1), (0, h - c, 0, c, 1, 0)):
        n = max(3, int(math.hypot(bx - ax, by - ay) / 46))
        off = np.abs(ndi.gaussian_filter1d(g.standard_normal(n + 1), 1.2)) * 1.7 * rough
        off[0] = off[-1] = 0
        for i in range(n + 1):
            t = i / n
            pts.append((ax + (bx - ax) * t + nx * off[i], ay + (by - ay) * t + ny * off[i]))
    return np.array(pts)


# ================================================================ the carpet and the desk
def carpet():
    """What shows of the floor carpet round the desk: guard stripes and a
    lapis border with a running vine, a rosette in each corner."""
    out = rrect(0, 0, W, H, C["red_dk"], 0)
    out += rrect(4, 4, W - 8, H - 8, C["paper"], 1.2)
    for x in np.arange(13.0, W - 8, 9.0):
        out += disc(x, 7.5, 1.5, C["red"], 0) + disc(x, H - 7.5, 1.5, C["red"], 0)
    for y in np.arange(13.0, H - 8, 9.0):
        out += disc(7.5, y, 1.5, C["red"], 0) + disc(W - 7.5, y, 1.5, C["red"], 0)
    out += rrect(11, 11, W - 22, H - 22, C["lapis"], 1.2)
    out.append(G("bordur_ust", kivrik_dal(W - 78), place(39, 25)))
    out.append(G("bordur_alt", kivrik_dal(W - 78), place(W - 39, H - 25, 180)))
    out.append(G("bordur_sol", kivrik_dal(H - 78), place(25, H - 39, -90)))
    out.append(G("bordur_sag", kivrik_dal(H - 78), place(W - 25, 39, 90)))
    for cx, cy in ((25, 25), (W - 25, 25), (25, H - 25), (W - 25, H - 25)):
        out += rrect(cx - 14, cy - 14, 28, 28, C["lapis_dk"], 1.0)
        out += rrect(cx - 11, cy - 11, 22, 22, None, 0.8, lc=C["lapis_lt"])
        out += penc(cx, cy, 9.5, 8, C["red"], C["paper"], 0.7)
    out += rrect(39, 39, W - 78, H - 78, C["red"], 1.2)
    return out


KNOTS = ((980, 694, 30), (188, 910, 24))


def desk():
    """Plain dark wood: four boards, a quiet grain that parts round the knots,
    a bone fillet let into the edge."""
    g = np.random.default_rng(11)
    x0, y0, x1, y1 = 58, 52, W - 58, H - 52
    out = carpet()
    out += rrect(x0 - 8, y0 - 8, x1 - x0 + 16, y1 - y0 + 16, C["red_deep"], LINE, r=11)
    out += rrect(x0, y0, x1 - x0, y1 - y0, C["wood"], LINE, r=6)
    boards = 4
    bh = (y1 - y0) / boards
    grain = []
    for bi in range(boards):
        top = y0 + bi * bh
        for _ in range(11):
            yb = top + g.uniform(7, bh - 7)
            xa = g.uniform(x0 + 6, x1 - 420)
            ln = g.uniform(280, 980)
            xb = min(xa + ln, x1 - 6)
            xs = np.linspace(xa, xb, int((xb - xa) / 14) + 2)
            ph, am, wl = g.uniform(0, 6.28), g.uniform(1.0, 3.4), g.uniform(260, 620)
            ys = yb + am * np.sin(xs / wl * 2 * PI + ph)
            for kx, ky, kr in KNOTS:
                near = np.exp(-((xs - kx) / (kr * 2.6)) ** 2)
                push = np.sign(yb - ky) * kr * 1.15 * math.exp(-abs(yb - ky) / (kr * 1.5))
                ys = ys + near * push
            ys = np.clip(ys, top + 3, top + bh - 3)
            col = C["wood_lt"] if g.uniform() < 0.28 else C["wood_dk"]
            grain += brush(np.stack([xs, ys], 1), g.uniform(1.3, 2.5), col, (0.45, 0.45), "paint", breath=0.25, seed=int(g.integers(1 << 30)))
    for kx, ky, kr in KNOTS:
        for q, f in enumerate((1.0, 0.68, 0.38)):
            grain += [el("ellipse", "paint", stroke=C["wood_dk"], sw=1.5, cx=f"{kx}", cy=f"{ky}", rx=f"{kr * f:.1f}", ry=f"{kr * f * 0.46:.1f}")]
        grain += [el("ellipse", "paint", fill=C["wood_dk"], cx=f"{kx}", cy=f"{ky}", rx=f"{kr * 0.16:.1f}", ry=f"{kr * 0.08:.1f}")]
    out.append(G("damar", grain))
    for bi in range(1, boards):
        yy = y0 + bi * bh
        xs = np.linspace(x0 + 1, x1 - 1, 60)
        out += brush(np.stack([xs, yy + 0.8 * np.sin(xs / 190.0 + bi)], 1), 2.4, C["red_deep"], (0.02, 0.02), "paint", wmin=0.8, breath=0.18, seed=bi)
    # the fillet: a hair of bone set into the wood, knotted at the corners
    m = 13
    out += rrect(x0 + m, y0 + m, x1 - x0 - 2 * m, y1 - y0 - 2 * m, None, 1.5, r=3, lc=C["paper3"], role="paint")
    for cx, cy in ((x0 + m, y0 + m), (x1 - m, y0 + m), (x0 + m, y1 - m), (x1 - m, y1 - m)):
        out += fill(lobed(cx, cy, 7.5, 4, 0.3, phase=PI / 4), C["paper3"], 0.8)
        out += disc(cx, cy, 2.0, C["wood"], 0)
    return G("masa", out)


# ================================================================ the scribe's things
def flame_tongue(x, y, a, length, wd, color, line=1.0, curl=0.24):
    """One tongue of flame: swells, then curls to a point."""
    t = np.linspace(0, 1, 16)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    c = curl * length * t ** 2.3
    spine = np.stack([x + ux * length * t + px * c, y + uy * length * t + py * c], 1)
    width = 2 * wd * np.sin(PI * np.minimum(1, t * 1.2)) ** 0.9 * (1 - t) ** 0.4 + 0.02
    return fill(ribbon(spine, width, (0, 0), 1.0), color, line)


def kandil_isigi(r=62):
    """The lamp's light is a drawn thing: a pale medallion, the illuminator's
    needles round it for rays, and a plume of flame tongues rising in it."""
    cy = -r * 0.22
    out = []
    for k in range(24):
        a = 2 * PI * k / 24 + PI / 24
        out += tig(r * 1.06 * math.cos(a), cy + r * 1.06 * math.sin(a), a, 9 if k % 2 else 15, C["red"], dot=(k % 2 == 0))
    out += fill(lobed(0, cy, r * 1.04, 12, 0.10), C["light"], 1.2, C["red"])
    out += fill(lobed(0, cy, r * 0.80, 12, 0.10), C["light2"], 0.8, C["red_lt"])
    by = r * 0.16
    for k, a in enumerate(np.linspace(-PI / 2 - 0.95, -PI / 2 + 0.95, 7)):
        ln = r * (0.98 - 0.36 * abs(a + PI / 2)) * (0.92 if k % 2 else 1.04)
        out += flame_tongue(0, by, a, ln, r * 0.15, C["red"] if k % 2 == 0 else C["red_lt"], 1.0, 0.24 if a <= -PI / 2 else -0.24)
    for a in np.linspace(-PI / 2 - 0.42, -PI / 2 + 0.42, 3):
        out += flame_tongue(0, by - 1, a, r * 0.5, r * 0.105, C["glaze"], 0.9, 0.2 if a < -PI / 2 else -0.2)
    return out


def kandil():
    """A glazed oil lamp from above: ring handle, round bowl, spout and wick."""
    out = ring(-56, 0, 15, 8.5) + ring(-56, 0, 15, 5.5, C["lapis_dk"], "paint")
    out += fill([(18, -17), (62, -10), (80, -3.5), (80, 3.5), (62, 10), (18, 17)], C["lapis"])
    out += disc(0, 0, 41, C["glaze"])
    out += ring(0, 0, 35.5, 5.0, C["lapis"], "paint") + ring(0, 0, 38.2, 0.7) + ring(0, 0, 32.8, 0.7)
    for k in range(8):
        a = 2 * PI * k / 8 + PI / 8
        out += fill(xf(almond(15, 8.5, k=0.55, base=0.3, n=9), 11 * math.cos(a), 11 * math.sin(a), a), C["red"] if k % 2 else C["lapis"], 0.8)
    out += disc(0, 0, 10.5, C["lapis_dk"], 1.0) + disc(0, 0, 6.0, C["ink"], 0)
    out += disc(74, 0, 4.2, C["ink"], 0.8)
    return out


def kalemdan():
    """A lacquered pen case with its drawer drawn a little way out."""
    out = []
    # the drawer and the reeds in it
    out += rrect(214, 5, 118, 36, C["red_dk"], LINE, r=4)
    out += rrect(222, 9.5, 104, 27, C["wood_dk"], 1.0, r=2)
    for k, yy in enumerate((13.5, 20.5, 27.5)):
        ln = (96, 88, 92)[k]
        out += fill([(224, yy), (224 + ln - 12, yy), (224 + ln, yy + 2.6), (224 + ln - 12, yy + 5.2), (224, yy + 5.2)], C["paper2"], 0.9)
        out += stroke([(250 + 9 * k, yy), (250 + 9 * k, yy + 5.2)], 0.8)
        out += fill([(224 + ln - 7, yy + 1.2), (224 + ln, yy + 2.6), (224 + ln - 7, yy + 4.0)], C["ink"], 0)
    out += disc(335, 23, 4.5, C["lapis"], 1.0)
    # the case
    out += rrect(0, 0, 240, 46, C["red"], LINE, r=11)
    out += rrect(5.5, 5.5, 229, 35, None, 1.2, r=7, lc=C["red_pale"], role="paint")
    out += fill(kartus(120, 23, 150, 21), C["lapis"], 1.0)
    for k in range(-2, 3):
        cx = 120 + k * 22
        if k % 2 == 0:
            out += penc(cx, 23, 4.6, 5, C["paper"], C["red"], 0.6)
        else:
            out += rumi(cx - 5.5, 24.5, -0.5, 11, False, C["lapis_pale"], 0) + rumi(cx + 5.5, 21.5, PI - 0.5, 11, False, C["lapis_pale"], 0)
    for cx in (23, 217):
        out += disc(cx, 23, 8.5, C["lapis_dk"], 1.0) + gul(cx, 23, 6.0, 6, C["paper"], C["red"], 0)
    return out


def hokka():
    """The inkwells: black ink with its tuft of silk, a smaller pot of red, a lid laid by."""
    out = disc(0, 0, 33, C["glaze"])
    out += ring(0, 0, 25.5, 5.5, C["lapis"], "paint") + ring(0, 0, 28.5, 0.7) + ring(0, 0, 22.5, 0.7)
    for k in range(12):
        a = 2 * PI * k / 12
        out += disc(30.6 * math.cos(a), 30.6 * math.sin(a), 1.4, C["red"], 0)
    out += disc(0, 0, 18, C["ink"], 1.0)
    th = np.linspace(0.4, 4.6 * PI, 60)
    out += brush(np.stack([(1.2 + 2.9 * th / PI) * np.cos(th), (1.2 + 2.9 * th / PI) * np.sin(th)], 1), 1.3, "#56423a", (0.2, 0.3), "paint")
    # red ink
    rx, ry = 64, -36
    out += disc(rx, ry, 21, C["glaze"]) + ring(rx, ry, 16.5, 2.6, C["lapis"], "paint") + ring(rx, ry, 18.4, 0.7)
    out += disc(rx, ry, 12.5, C["red"], 1.0)
    th = np.linspace(0.6, 3.2 * PI, 36)
    out += brush(np.stack([rx + (1 + 2.6 * th / PI) * np.cos(th), ry + (1 + 2.6 * th / PI) * np.sin(th)], 1), 1.1, C["red_dk"], (0.2, 0.3), "paint")
    # lid
    lx, ly = 60, 30
    out += disc(lx, ly, 15, C["lapis"]) + ring(lx, ly, 11, 0.8, C["lapis_pale"], "paint")
    out += gul(lx, ly, 7.5, 8, C["paper"], C["red"], 0.6)
    return out


def makas():
    """Paper scissors: long blades, two bows worked into leaves."""
    out = []
    for sg in (-1, 1):
        out += fill([(92, sg * 0.3), (92, sg * 5.5), (250, sg * 0.5)], C["lapis_pale"], 1.0)
        out += stroke([(98, sg * 3.6), (228, sg * 1.0)], 0.7, C["lapis_lt"], "paint")
        bow = arc(26, sg * 13, 22, 0, 2 * PI, 28, ry=10.5)
        inner = arc(26, sg * 13, 16.5, 0, 2 * PI, 24, ry=6.2)
        out += holed(bow, [inner], C["lapis_lt"], 1.0)
        out += fill([(46, sg * 8.5), (92, sg * 1.2), (92, sg * 5.5), (47, sg * 17)], C["lapis_lt"], 1.0)
        out += rumi(4.5, sg * 13, PI, 12, mirror=(sg > 0), color=C["lapis_lt"], line=0.8)
    out += disc(94, 0, 5.2, C["red"], 1.0) + disc(94, 0, 1.6, C["paper"], 0)
    return out


def kalemtiras():
    """The penknife: a bone handle banded in red, a short curved blade."""
    out = fill(np.vstack([[(74, -5.0)], bez((74, -5.0), (104, -6.5), (128, -4.0), (140, 4.5), 10), [(74, 4.5)]]), C["lapis_pale"], 1.0)
    out += rrect(0, -6.5, 76, 13, C["glaze"], 1.0, r=5)
    for bx in (8, 14, 58, 64):
        out += rrect(bx, -6.5, 3.4, 13, C["red"], 0.7)
    out += fill(kartus(36, 0, 34, 6.5), C["lapis"], 0.7)
    return out


def makta():
    """The bone rest on which the reed is nibbed."""
    out = fill(np.vstack([[(0, -8), (78, -8)], bez((78, -8), (88, -8), (92, -4), (98, 0), 6), bez((98, 0), (92, 4), (88, 8), (78, 8), 6), [(0, 8)]]), C["glaze"], 1.0)
    out += rrect(4, -5, 70, 10, None, 0.7, r=2, lc=C["paper3"], role="paint")
    out += rrect(30, -2.2, 34, 4.4, C["paper2"], 0.7, r=2)
    for cx in (10, 17, 24):
        out += disc(cx, 0, 1.8, C["lapis"], 0)
    out += gul(84, 0, 4.2, 6, C["red"], C["glaze"], 0)
    return out


def muhre():
    """The burnisher: an agate egg on a turned handle."""
    out = rrect(0, -6, 118, 12, C["red"], 1.0, r=5)
    for bx in (10, 16, 96, 102):
        out += rrect(bx, -6, 3.2, 12, C["paper2"], 0.7)
    out += fill(kartus(56, 0, 52, 6), C["lapis"], 0.7)
    out += rrect(114, -8.5, 12, 17, C["lapis_dk"], 1.0, r=2)
    out += oval(150, 0, 27, 16, C["red_lt"], 1.2)
    for k, rr in enumerate((21, 14.5, 8)):
        out += [el("ellipse", "paint", stroke=C["red_pale"] if k % 2 == 0 else C["red"], sw=1.6, cx="151.5", cy="0", rx=f"{rr}", ry=f"{rr * 0.56:.1f}")]
    return out


def rihdan():
    """The sand shaker that dries the ink."""
    out = disc(0, 0, 25, C["lapis"]) + ring(0, 0, 20.5, 0.9, C["lapis_pale"], "paint")
    out += fill(lobed(0, 0, 17.5, 8, 0.2), C["glaze"], 0.8)
    for rr, n in ((0, 1), (5.2, 6), (10.4, 12)):
        for k in range(n):
            a = 2 * PI * k / n
            out += disc(rr * math.cos(a), rr * math.sin(a), 1.25, C["ink"], 0)
    for k in range(8):
        a = 2 * PI * k / 8 + PI / 8
        out += disc(22.8 * math.cos(a), 22.8 * math.sin(a), 1.2, C["red_lt"], 0)
    return out


def bohca(s=190):
    """The wrapping cloth of whoever brought the work: lapis, sown with çintemani."""
    h = s / 2
    out = fill([(0, -h), (h, 0), (0, h), (-h, 0)], C["lapis"])
    for i in range(-2, 3):
        for j in range(-2, 3):
            x, y = (i - j) * s / 7.2, (i + j) * s / 7.2
            if abs(x) + abs(y) < h - 22:
                out += cintemani(x, y, 0.5, C["red"], C["paper"], C["lapis"])
    out += stroke([(0, -h + 9), (h - 9, 0), (0, h - 9), (-h + 9, 0)], 1.3, C["paper"], "paint", closed=True)
    out += stroke([(0, -h + 13), (h - 13, 0), (0, h - 13), (-h + 13, 0)], 0.8, C["red_lt"], "paint", closed=True)
    for tx, ty in ((0, -h), (h, 0), (0, h), (-h, 0)):
        out += disc(tx, ty, 4.2, C["red"], 0.9)
    return out


def rulo(length=156, r=18):
    """A rolled letter, tied twice and sealed."""
    out = rrect(0, -r, length, 2 * r, C["paper"], LINE, r=6)
    out += stroke([(8, -r + 6), (length - 14, -r + 6)], 0.8, C["paper2"], "paint")
    out += oval(length, 0, 6.5, r, C["paper2"], 1.2)
    th = np.linspace(0, 3.4 * PI, 30)
    out += brush(np.stack([length + (0.5 + 1.1 * th / PI) * np.cos(th) * 0.9, (1.4 + 3.6 * th / PI) * np.sin(th)], 1), 0.9, C["ink"], (0.1, 0.3))
    for bx in (length * 0.28, length * 0.6):
        out += rrect(bx, -r - 1, 8, 2 * r + 2, C["red"], 1.0)
    out += disc(length * 0.455, r * 0.25, 14, C["red"], 1.2) + gul(length * 0.455, r * 0.25, 8.5, 8, C["red_dk"], C["red_lt"], 0)
    return out


def desk_plate():
    """The desk with the things that never leave it."""
    return [desk(),
            G("makas", makas(), place(322, 268, -37)),
            G("kalemtiras", kalemtiras(), place(408, 262, -15)),
            G("makta", makta(), place(486, 286, -4)),
            G("kandil_govde", kandil(), place(140, 160, -18)),
            G("kandil_isigi", kandil_isigi(), place(212, 140)),
            G("kalemdan", kalemdan(), place(700, 84, 1)),
            G("hokka", hokka(), place(1322, 142)),
            G("muhre", muhre(), place(1470, 96, 5)),
            G("rihdan", rihdan(), place(1560, 178)),
            G("bohca", bohca(190) + [G("rulo", rulo(), place(-80, -4, -18))], place(1838, 168))]


# ================================================================ papers
def cetvel(x, y, w, h):
    """The ruled frame of a page: a lapis line between two hairs, a red hair inside."""
    out = rrect(x, y, w, h, None, 3.0, lc=C["lapis"], role="ink")
    out += rrect(x - 2.4, y - 2.4, w + 4.8, h + 4.8, None, 0.7, role="ink")
    out += rrect(x + 2.4, y + 2.4, w - 4.8, h - 4.8, None, 0.7, role="ink")
    return out


def baslik(cx, cy, cw, ch, reach):
    """The title cartouche, with a sprig running out each side: two leaves,
    a rosette, a bud."""
    out = []
    for sg in (-1, 1):
        x0 = cx + sg * cw / 2
        a = 0 if sg > 0 else PI
        out += brush([(x0, cy), (x0 + sg * reach * 0.5, cy), (x0 + sg * reach, cy)], 1.5, C["lapis"], (0.0, 0.6), wmin=0.35)
        for da in (-0.62, 0.62):
            out += fill(xf(almond(10, 4.2, k=0.5), x0 + sg * reach * 0.16, cy, a + da), C["lapis"], 0)
        out += gul(x0 + sg * reach * 0.52, cy, 5.4, 6, C["red"], C["paper"], 0.7)
        out += fill(xf(almond(9, 4.6, k=0.4), x0 + sg * reach * 0.86, cy, a), C["lapis"], 0)
    out += fill(kartus(cx, cy, cw, ch), C["lapis"], 1.4)
    out += stroke(kartus(cx, cy, cw - 12, ch - 9), 0.8, C["lapis_lt"], "paint", closed=True)
    return out


def document_page(w, h, grand=False, seed=3):
    """Text first. On the desk: a ruled frame, a small title, corner pieces.
    In the reading view the same page shows its full illumination: a chain
    border inside the rule and needles round it."""
    out = fill(sheet(w, h, seed), C["paper"])
    m = 26
    if grand:
        for x in np.arange(m + 30, w - m - 20, 34.0):
            for yy, a in ((m - 3, -PI / 2), (h - m + 3, PI / 2)):
                out += tig(x, yy, a, 8 if int(x / 34) % 2 else 13, C["lapis"], dot=int(x / 34) % 2 == 0)
        for y in np.arange(m + 30, h - m - 20, 34.0):
            for xx, a in ((m - 3, PI), (w - m + 3, 0)):
                out += tig(xx, y, a, 8 if int(y / 34) % 2 else 13, C["lapis"], dot=int(y / 34) % 2 == 0)
        out += rrect(m, m, w - 2 * m, h - 2 * m, C["lapis"], 0)
        band = 20
        out += rrect(m + band, m + band, w - 2 * m - 2 * band, h - 2 * m - 2 * band, C["paper"], 0.9)
        b2 = band / 2
        out.append(G("zencerek_ust", zencerek(w - 2 * m - 2 * band), place(m + band, m + b2)))
        out.append(G("zencerek_alt", zencerek(w - 2 * m - 2 * band), place(m + band, h - m - b2)))
        out.append(G("zencerek_sol", zencerek(h - 2 * m - 2 * band), place(m + b2, m + band, 90)))
        out.append(G("zencerek_sag", zencerek(h - 2 * m - 2 * band), place(w - m - b2, m + band, 90)))
        for cx, cy in ((m + b2, m + b2), (w - m - b2, m + b2), (m + b2, h - m - b2), (w - m - b2, h - m - b2)):
            out += gul(cx, cy, 7.2, 8, C["paper"], C["red"], 0.6)
        out += cetvel(m, m, w - 2 * m, h - 2 * m)
        inner = m + band + 6
        out += rrect(inner, inner, w - 2 * inner, h - 2 * inner, None, 1.0, lc=C["red"], role="ink")
        ks, cw, reach = 40.0, 330, 120
    else:
        out += cetvel(m, m, w - 2 * m, h - 2 * m)
        inner = m + 7
        out += rrect(inner, inner, w - 2 * inner, h - 2 * inner, None, 1.0, lc=C["red"], role="ink")
        ks, cw, reach = 25.0, 312, 62
    for sx, sy, x, y in ((1, 1, inner, inner), (-1, 1, w - inner, inner), (1, -1, inner, h - inner), (-1, -1, w - inner, h - inner)):
        out += kosebent(x, y, sx, sy, ks)
    out += baslik(w / 2, 70, cw, 44, reach)
    return out


def copy_sheet(w=420, h=500):
    """New paper, blind-ruled with the mıstar; nothing else. The scribe's own work."""
    out = fill(sheet(w, h, 8, 0.6), C["fresh"])
    for i in range(6):
        yy = 96 + i * 70
        out += stroke([(30, yy), (w - 30, yy + 0.6)], 0.9, "#e6d8b8", "paint")
        out += disc(22, yy, 1.0, C["paper2"], 0) + disc(w - 22, yy, 1.0, C["paper2"], 0)
    return out


def slip(w=360, h=250):
    """A note from the requester: coarser paper, torn along the top, folded in
    three, a corner turned, a bead of wax."""
    g = np.random.default_rng(21)
    top = [(x, g.uniform(0, 3.2) + (1.6 if i % 2 else 0)) for i, x in enumerate(np.linspace(0, w, 34))]
    out = fill(top + [(w, h - 36), (w - 36, h), (0, h)], C["paper"])
    for fx in (w / 3, 2 * w / 3):
        out += brush([(fx + 2, 4), (fx, h / 2), (fx - 2, h - 3)], 1.2, C["paper2"], (0.05, 0.05), "paint", wmin=0.7)
    out += fill([(w, h - 36), (w - 31, h - 31), (w - 36, h)], C["paper2"], 1.2)
    out += disc(w - 64, h - 34, 13, C["red"], 1.2) + gul(w - 64, h - 34, 7.8, 6, C["red_dk"], C["red_lt"], 0)
    return out


def notebook(w=520, h=420):
    """The scribe's own book lying open: leather boards, the edges of the
    leaves, the sewing in the gutter, headbands, a ribbon."""
    out = rrect(-16, -16, w + 32, h + 32, C["red"], LINE, r=8)
    out += rrect(-11, -11, w + 22, h + 22, None, 1.3, r=5, lc=C["red_dk"], role="paint")
    for cx, cy in ((-9, -9), (w + 9, -9), (-9, h + 9), (w + 9, h + 9)):
        out += disc(cx, cy, 2.2, C["red_pale"], 0)
    for i in (3, 2, 1):
        out += rrect(-2.6 * i, 1.5 * i, w / 2 + 2.6 * i, h - 0.5 * i, C["paper2"], 0.8)
        out += rrect(w / 2, 1.5 * i, w / 2 + 2.6 * i, h - 0.5 * i, C["paper2"], 0.8)
    out += rrect(0, 0, w / 2, h, C["paper"], 1.2) + rrect(w / 2, 0, w / 2, h, C["paper"], 1.2)
    for k in range(12):
        yy = 69 + 27 * k
        out += stroke([(20, yy), (w / 2 - 16, yy)], 0.8, "#e2d0a8", "paint")
        out += stroke([(w / 2 + 18, yy), (w - 18, yy)], 0.8, "#e2d0a8", "paint")
    for dx in (-7, 7):
        out += stroke([(w / 2 + dx, 2), (w / 2 + dx * 0.8, h / 2), (w / 2 + dx, h - 2)], 0.8, C["paper2"], "paint")
    out += stroke([(w / 2, 0), (w / 2, h)], 1.8)
    for yy in (58, 160, 262, 364):
        out += stroke([(w / 2 - 5, yy), (w / 2 + 5, yy)], 2.6, cap="butt") + stroke([(w / 2 - 4.4, yy), (w / 2 + 4.4, yy)], 1.4, C["glaze"], "paint", cap="butt")
    for yy, sg in ((-1, -1), (h + 1, 1)):
        out += rrect(w / 2 - 24, min(yy, yy + sg * 8), 48, 8, C["paper"], 0.9, r=2)
        for k in range(8):
            x0 = w / 2 - 24 + k * 6
            col = (C["red"], C["lapis"])[k % 2]
            out += fill([(x0 + 0.6, yy), (x0 + 3.6, yy), (x0 + 5.6, yy + sg * 8), (x0 + 2.6, yy + sg * 8)], col, 0)
    out += fill([(w / 2 + 4, h - 8), (w / 2 + 11, h - 8), (w / 2 + 12, h + 18), (w / 2 + 8, h + 13), (w / 2 + 4.5, h + 19)], C["lapis"], 1.0)
    return out


# ================================================================ tiles and the tray
def tile_frame(w=150, h=200):
    """An İznik tile: white slip under the glaze, a cobalt line, a tulip in each corner."""
    out = rrect(0, 0, w, h, C["glaze"], LINE, r=7)
    out += rrect(7.5, 7.5, w - 15, h - 15, None, 3.2, r=4, lc=C["lapis"], role="ink")
    out += rrect(11.2, 11.2, w - 22.4, h - 22.4, None, 0.7, r=2.5, role="ink")
    for x, y, a in ((14, 14, PI / 4), (w - 14, 14, 3 * PI / 4), (14, h - 14, -PI / 4), (w - 14, h - 14, -3 * PI / 4)):
        out += lale(x, y, a, 0.62, C["red"], 0.8)
    yy = 108.5
    for sg in (-1, 1):
        out += brush([(w / 2 + sg * 9, yy), (w / 2 + sg * 22, yy), (w / 2 + sg * 38, yy)], 1.4, C["lapis"], (0.0, 0.8), wmin=0.3)
    out += fill([(w / 2 - 5, yy), (w / 2, yy - 3.4), (w / 2 + 5, yy), (w / 2, yy + 3.4)], C["red"], 0.7)
    return out


def _cob(pts, w, taper=(0.1, 0.1), wmin=0.5):
    """A stroke of cobalt under the glaze."""
    rb = ribbon(pts, w, taper, wmin, 0.07, 5)
    return [el("path", "paint", fill=C["lapis"], d=d_of(rb)), el("path", "ink", stroke=C["lapis_dk"], sw=0.9, d=d_of(rb))]


def _drop(x, y, r, a=PI / 2):
    """A falling drop: thin where it left, round where it leads."""
    d = d_of(xf(almond(3.2 * r, 2 * r, k=0.7, n=15), x, y, a))
    return [el("path", "paint", fill=C["lapis"], d=d), el("path", "ink", stroke=C["lapis_dk"], sw=0.9, d=d)]


def picto(rule, cx=75.0, cy=81.0):
    """What each sound rule does, as a tile painter would sign it."""
    o = np.array([cx, cy])
    dot = lambda x, y, r: disc(cx + x, cy + y, r, C["lapis"], 0.9, C["lapis_dk"])
    out = []
    if rule == "R1":        # soft waves harden into teeth
        xs = np.linspace(-58, -2, 30)
        soft = np.stack([xs, 11 * np.sin((xs + 58) / 56 * 3 * PI)], 1)
        hard = np.array([(-2, 0), (8, -15), (20, 15), (32, -15), (44, 15), (56, -12)], float)
        out += _cob(np.vstack([soft, hard[1:]]) + o, 8.5, (0.1, 0.1))
    elif rule == "R2":      # two short become one long
        out += dot(-48, -7, 8.6) + dot(-28, 7, 8.6)
        out += _cob(np.array([(-13, 0), (-3, 0)]) + o, 5, (0.4, 0.4))
        out += _cob(np.array([(6, 0), (30, 0), (58, 0)]) + o, 11)
    elif rule == "R3":      # the long vowel climbs
        out += _cob(np.array([(-58, 13), (-40, 13), (-22, 13)]) + o, 10)
        out += _cob(bez((-16, 12), (-2, 10), (2, -9), (16, -12), 12) + o, 6.5, (0.5, 0.15))
        out += _cob(np.array([(22, -13), (40, -13), (58, -13)]) + o, 10)
    elif rule == "R4":      # the long vowel slides forward
        out += _cob(np.array([(-58, -10), (-38, -10), (-18, -10)]) + o, 10)
        out += _cob(bez((-36, 6), (-12, 20), (18, 18), (38, 3), 14) + o, 6, (0.6, 0.12))
        out += _cob(np.array([(16, -10), (37, -10), (58, -10)]) + o, 10)
    elif rule == "R5":      # the last consonants fall away
        out += _cob(np.array([(-58, -11), (-20, -11), (20, -11)]) + o, 10.5)
        out += _drop(cx + 33, cy - 13, 4.8, 1.2) + _drop(cx + 45, cy + 3, 4.4, 1.35)
    elif rule == "R6":      # a hard edge softens into a curl
        out += _cob(np.array([(-60, -16), (-42, 14), (-24, -16)]) + o, 8.5, (0.12, 0.12))
        th = np.linspace(0, 7.6, 44)
        out += _cob(np.stack([30 + 23 * np.cos(th) * (1 - th / 9.2), 23 * np.sin(th) * (1 - th / 9.2) - 1], 1) + o, 7.5, (0.08, 0.45))
    elif rule == "R7":      # a stop turns to breath
        out += _cob(np.array([(-58, 0), (-34, 0), (-10, 0)]) + o, 12)
        for dy in (-12, 0, 12):
            xs = np.linspace(2, 58, 24)
            out += _cob(np.stack([xs, dy + 3.2 * np.sin((xs - 2) / 56 * 4 * PI)], 1) + o, 4.6, (0.25, 0.4))
    elif rule == "R8":      # the last vowel falls away
        out += _cob(np.array([(-58, -9), (-22, -9), (16, -9)]) + o, 10.5)
        out += dot(40, 11, 6.8)
        out += _cob(bez((27, -8), (34, -9), (39, -6), (40, -1), 8) + o, 3.0, (0.2, 0.7))
    return out


def tray(n=5, slot_w=162, slot_h=212):
    """The rule tray: a lacquered board with five wells. Pips on the rail and
    small pointers between the wells give the order."""
    w, h = n * slot_w + 24, slot_h + 24
    out = rrect(0, 0, w, h, C["red"], LINE, r=9)
    out += rrect(4.5, 4.5, w - 9, h - 9, None, 1.1, r=6, lc=C["red_pale"], role="paint")
    for k in range(n):
        x = 12 + k * slot_w + 3
        out += rrect(x, 12, slot_w - 6, slot_h, C["red_deep"], 1.4, r=5)
        out += rrect(x + 9, 21, slot_w - 24, slot_h - 18, None, 1.0, r=4, lc=C["wood"], role="paint")
        out += stroke(lobed(x + (slot_w - 6) / 2, 12 + slot_h / 2, 30, 8, 0.16), 1.0, C["wood"], "paint", closed=True)
        out += stroke(lobed(x + (slot_w - 6) / 2, 12 + slot_h / 2, 12, 8, 0.2), 1.0, C["wood"], "paint", closed=True)
        px = x + (slot_w - 6) / 2 - (k * 7) / 2
        for j in range(k + 1):
            out += disc(px + j * 7, h - 6.2, 1.9, C["red_pale"], 0)
        if k:
            out += fill([(x - 6.2, 6.2 - 3.4), (x - 0.4, 6.2), (x - 6.2, 6.2 + 3.4)], C["red_pale"], 0)
    return out, w, h


# ================================================================ small things
def durak(cx=14.0, cy=14.0, r=12.0):
    out = gul(cx, cy, r * 0.84, 6, C["red"], C["paper"], 0.9)
    out += disc(cx, cy, r * 0.11, C["red"], 0)
    for k in range(6):
        a = 2 * PI * k / 6 - PI / 2 + PI / 6
        out += disc(cx + r * 0.93 * math.cos(a), cy + r * 0.93 * math.sin(a), 1.15, C["lapis"], 0)
    return out


def seal(cx=40.0, cy=40.0):
    """The scribe's seal as it prints: red ink, a ring, a star of two squares, a rosette."""
    red = C["red"]
    out = ring(cx, cy, 34, 3.4, red) + ring(cx, cy, 28.6, 1.1, red)
    for a0 in (0, PI / 4):
        out += stroke([(cx + 24 * math.cos(a0 + k * PI / 2), cy + 24 * math.sin(a0 + k * PI / 2)) for k in range(4)], 2.0, red, closed=True)
    out += [el("path", "ink", fill=red, d=d_of(lobed(cx, cy, 12.5, 8, 0.24)) + d_of(arc(cx, cy, 3.4, 0, 2 * PI, 16)), **{"fill-rule": "evenodd"})]
    for k in range(8):
        a = 2 * PI * k / 8 + PI / 8
        out += [el("circle", "ink", fill=red, cx=f"{cx + 19.5 * math.cos(a):.1f}", cy=f"{cy + 19.5 * math.sin(a):.1f}", r="1.5")]
    out += [el("circle", "ink", fill=red, cx=f"{cx}", cy=f"{cy}", r="1.4")]
    return out


def pen(length=250.0):
    """A reed pen: two nodes, a slanted nib with its slit, the tip dark with ink."""
    hb = 6.5
    body = [(0, -hb + 1), (6, -hb), (length - 44, -hb), (length - 20, -3.2), (length, 1.2), (length - 22, hb), (6, hb), (0, hb - 1)]
    out = fill(body, C["paper2"], 1.2)
    out += stroke([(8, -hb + 2.6), (length - 52, -hb + 2.6)], 1.0, C["paper"], "paint")
    out += stroke([(8, hb - 2.4), (length - 46, hb - 2.4)], 1.0, C["paper3"], "paint")
    for nx in (length * 0.27, length * 0.56):
        out += stroke([(nx, -hb), (nx - 1.2, 0), (nx, hb)], 1.0) + stroke([(nx + 3, -hb), (nx + 1.8, 0), (nx + 3, hb)], 0.7)
    out += fill([(length - 20, -3.2), (length, 1.2), (length - 22, hb), (length - 30, hb), (length - 33, -5.0)], C["ink"], 0)
    out += stroke([(length - 44, 0.6), (length - 6, 1.1)], 0.8, C["paper3"], "paint")
    out += oval(1.5, 0, 2.0, hb - 1.6, C["paper3"], 0.8)
    return out


def page_grain():
    """One sheet under the whole screen, multiplied over everything: a breath
    of fibre, the burnisher's passes, a little age toward the edges. Quiet:
    the paper of a miniature is sized and polished."""
    fib = nk.field(H, W, 1.1, 31) * 0.006 + nk.field(H, W, 4.0, 32) * 0.007
    blot = nk.field(H, W, 34, 33) * 0.010 + nk.field(H, W, 210, 34) * 0.016
    burn = nk.streaks(H, W, 3.0, 180, 35, angle=27) * 0.005
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    edge = np.minimum.reduce([xx, W - 1 - xx, yy, H - 1 - yy])
    age = 0.035 * np.exp(-edge / 40.0)
    m = np.clip(0.982 + fib + blot + burn - age, 0, 1)
    rgb = np.stack([m ** 0.9, m, m ** 1.2], -1)
    Image.fromarray((rgb * 255 + 0.5).astype(np.uint8)).save(SPR / "sayfa_doku.png")


# ================================================================ export
def sprite(name, items, w, h, pad=8, seed=1, **kw):
    nk.paint_png(items, w, h, SPR / f"{name}.png", pad=pad, seed=seed, src=SRC / f"{name}.svg", **kw)
    print("  ", name)


def sprites():
    """name -> a function that paints it."""
    tr, tw, th = tray()
    todo = {
        "masa_cag2": lambda: sprite("masa_cag2", desk_plate(), W, H, 0, seed=7),
        "belge_kagit": lambda: sprite("belge_kagit", document_page(680, 440), 680, 440, seed=11, age=1.0),
        "belge_okuma": lambda: sprite("belge_okuma", document_page(1520, 760, True), 1520, 760, seed=12, age=1.0),
        "kopya_kagit": lambda: sprite("kopya_kagit", copy_sheet(), 420, 500, seed=13, age=0.25),
        "pusula": lambda: sprite("pusula", slip(), 360, 250, seed=14, age=0.7),
        "defter": lambda: sprite("defter", notebook(), 520, 420, 20, seed=15, age=0.0),
        "tepsi": lambda: sprite("tepsi", tr, tw, th, seed=16),
        "karo_cerceve": lambda: sprite("karo_cerceve", tile_frame(), 150, 200, seed=17, wobble=0.7),
        "durak": lambda: sprite("durak", durak(), 28, 28, 2, seed=18, wobble=0.4),
        "muhur": lambda: sprite("muhur", seal(), 80, 80, seed=19, wobble=0.6, stamp=0.75),
        "kalem": lambda: sprite("kalem", [G("kalem", pen(), place(0, 9))], 250, 18, seed=20, wobble=0.6),
        "sayfa_doku": page_grain,
    }
    for i in range(1, 9):
        todo[f"picto_R{i}"] = (lambda r=f"R{i}", s=30 + i: sprite(f"picto_{r}", picto(r), 150, 200, seed=s, wobble=0.6))
    return todo


def contact_sheet(path):
    """Every loose sprite on one wooden ground, for looking at."""
    names = ["belge_kagit", "kopya_kagit", "pusula", "defter", "tepsi", "karo_cerceve"] + [f"picto_R{i}" for i in range(1, 9)] + ["durak", "muhur", "kalem"]
    bg = Image.new("RGBA", (1920, 1500), C["wood"])
    x = y = 20
    row = 0
    tile = Image.open(SPR / "karo_cerceve.png")
    for n in names:
        im = Image.open(SPR / f"{n}.png").convert("RGBA")
        if n.startswith("picto_"):
            base = tile.copy()
            base.alpha_composite(im)
            im = base
        if x + im.width > 1900:
            x, y, row = 20, y + row + 20, 0
        bg.alpha_composite(im, (x, y))
        x += im.width + 20
        row = max(row, im.height)
    bg.convert("RGB").save(path)


if __name__ == "__main__":
    SPR.mkdir(parents=True, exist_ok=True)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    todo = sprites()
    for name, fn in todo.items():
        if not args or any(name.startswith(a) for a in args):
            fn()
    if "--sheet" in sys.argv:
        contact_sheet(ROOT / "assets/art/style/sprite_sayfasi.png")
