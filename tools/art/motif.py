"""The palette, the four eras and the motif library.

An era is a school of painting (assets/art/STYLE.md): its pigments, how thick
and how sure its line is, how well its paint keeps inside the line. Objects ask
`C` for a colour by name and `era()` for the school; `use_era(n)` changes both,
so the same drawing comes out in the hand of another century.
"""
import math

import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from pathlib import Path
from scipy import ndimage as ndi

import nakkas as nk
from nakkas import (G, LINE, almond, arc, bez, brush, d_of, disc, el, fill, holed, lobed, oval, place, ribbon,
                    ring, rrect, spline, stroke, xf)

ROOT = Path(__file__).resolve().parents[2]
KATIP = ROOT / "assets/fonts/Katip-Regular.ttf"
W, H = 1920, 1080
PI = math.pi

BASE = {
    "paper": "#ecdcb9", "paper2": "#dcc69c", "paper3": "#c7ab7e", "fresh": "#f2e7cd", "glaze": "#f4ecdb",
    "ink": "#2a1b14",
    "lapis": "#2f4d9e", "lapis_dk": "#1e3171", "lapis_lt": "#8ca4d6", "lapis_pale": "#cdd8ef",
    "red": "#b33a29", "red_dk": "#6c2a1d", "red_deep": "#4c1c13", "red_lt": "#dc8a76", "red_pale": "#f1cbbb",
    "wood": "#5a2519", "wood_dk": "#47190f", "wood_lt": "#6b2f20", "light": "#f8e2d6", "light2": "#fcefe5",
    "char": "#2a130c",
}

# line: how heavy the tahrir is.  how: see nakkas.pigment().
ERAS = {
    1: {"name": "Selçuklu", "line": 1.5,
        "how": {"wobble": 1.2, "slip": 1.5, "breathe": 1.5, "grain": 1.25},
        # paint is scarce: paper, ink and two reds. What will be lapis is still brick.
        "pal": {"lapis": "#8c3020", "lapis_dk": "#5a2116", "lapis_lt": "#d6957f", "lapis_pale": "#efd3c3",
                "paper": "#e9d9b4", "fresh": "#efe2c4", "glaze": "#e4d1a8", "light": "#f6e2cc", "light2": "#fbefdd"}},
    2: {"name": "Klasik Osmanlı", "line": 1.0, "how": {}, "pal": {}},
    3: {"name": "Taşra", "line": 1.45,
        "how": {"wobble": 2.0, "slip": 3.2, "spill": 1.35, "breathe": 2.0, "grain": 1.5},
        # cheaper pigments: indigo for lapis, ochre red, browner paper
        "pal": {"lapis": "#3f5687", "lapis_dk": "#2a3a61", "lapis_lt": "#8e9ec0", "lapis_pale": "#cfd5e2",
                "red": "#a5482f", "red_dk": "#65301f", "red_deep": "#45200f", "red_lt": "#d39279", "red_pale": "#ecd0bf",
                "paper": "#e2cfa4", "paper2": "#cfb688", "paper3": "#b99c6c", "fresh": "#e9dab6", "glaze": "#ebe0c8",
                "wood": "#55291b", "wood_dk": "#3e1b10", "wood_lt": "#6a3722"}},
    4: {"name": "Batılılaşma", "line": 0.8,
        "how": {"wobble": 0.45, "slip": 0.5, "breathe": 0.6, "grain": 0.7},
        # the colours go pastel, the ink softer, the wood polished
        "pal": {"lapis": "#6f93c9", "lapis_dk": "#46669e", "lapis_lt": "#abc2e4", "lapis_pale": "#dde7f4",
                "red": "#cc7868", "red_dk": "#93503f", "red_deep": "#6b382c", "red_lt": "#e6ab9c", "red_pale": "#f5dcd3",
                "paper": "#f0e6d0", "paper2": "#e0d2b4", "paper3": "#cbb894", "fresh": "#f5eedd", "glaze": "#f7f2e6",
                "ink": "#3b2d28", "wood": "#74442f", "wood_dk": "#5c3322", "wood_lt": "#8a573c",
                "light": "#fbeede", "light2": "#fff8ee", "char": "#3b2d28"}},
}

C = dict(BASE)
_now = {"era": 2}


def era():
    return _now["era"]


def use_era(n):
    _now["era"] = n
    C.clear()
    C.update(BASE)
    C.update(ERAS[n]["pal"])
    nk.INK = C["ink"]


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




def flame_tongue(x, y, a, length, wd, color, line=1.0, curl=0.24):
    """One tongue of flame: swells, then curls to a point."""
    t = np.linspace(0, 1, 16)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    c = curl * length * t ** 2.3
    spine = np.stack([x + ux * length * t + px * c, y + uy * length * t + py * c], 1)
    width = 2 * wd * np.sin(PI * np.minimum(1, t * 1.2)) ** 0.9 * (1 - t) ** 0.4 + 0.02
    return fill(ribbon(spine, width, (0, 0), 1.0), color, line)


# ---------------------------------------------------------------- the first era: geometry
def yildiz(x, y, r, a0=0.0, n=8, inner=0.765):
    """The Seljuk star: two squares laid across each other."""
    k = np.arange(2 * n)
    a = a0 + k * PI / n
    rr = np.where(k % 2 == 0, r, r * inner)
    return np.stack([x + rr * np.cos(a), y + rr * np.sin(a)], 1)


def gecme(length, hb=11.0, period=46.0, w=3.4, col_a=None, col_b=None):
    """A braid of two angular strands, over and under in turn, along +x:
    the interlace of Seljuk stone and woodwork."""
    n = max(2, round(length / period))
    p = length / n
    amp = hb - 3.6
    k = np.arange(2 * n + 1)
    a = np.stack([k * p / 2, amp * np.where(k % 2 == 0, 1.0, -1.0)], 1)
    b = a * [1, -1]
    ca, cb = col_a or C["red"], col_b or C["lapis"]
    out = []
    for i in range(2 * n + 1):
        x = i * p / 2
        out += fill([(x - 3.2, 0), (x, -3.2), (x + 3.2, 0), (x, 3.2)], C["ink"], 0)
    out += stroke(a, w + 1.5, cap="butt", join="miter") + stroke(a, w, ca, "paint", cap="butt", join="miter")
    out += stroke(b, w + 1.5, cap="butt", join="miter") + stroke(b, w, cb, "paint", cap="butt", join="miter")
    for i in range(0, 2 * n, 2):
        seg = a[i] + (a[i + 1] - a[i]) * np.array([[0.3], [0.7]])
        out += stroke(seg, w + 1.5, cap="butt") + stroke(seg, w, ca, "paint", cap="butt")
    return out


# ---------------------------------------------------------------- the third era: a provincial hand
def kivrik_dal_tasra(length, hb=11.0, period=128.0, amp=5.6):
    """The court's running vine as a country painter remembers it: fewer,
    fatter flowers, one leaf where there were two, and some never coloured."""
    g = np.random.default_rng(int(length))
    n = max(1, round(length / period))
    p = length / n
    u = np.linspace(0, length, n * 20 + 1)
    out = stroke(np.stack([u, amp * np.sin(2 * PI * u / p) + 0.9 * np.sin(u / 17.0)], 1), 2.8, C["paper"], "paint")
    for k in range(2 * n):
        uc = (k + 0.5) * p / 2
        sg = 1.0 if k % 2 == 0 else -1.0
        vb = -sg * 2.6
        side = 1.0 if (k // 2) % 2 else -1.0
        out += stroke([(uc, sg * amp), (uc - side * 5, vb + sg * 4)], 2.0, C["paper"], "paint")
        out += rumi(uc + side * 3, sg * (amp - 1.4), math.atan2(-sg * 4, side * 13), 20, mirror=(side * sg > 0), color=C["paper"], line=0)
        col = C["red"] if k % 2 == 0 else C["lapis_pale"]
        if g.uniform() < 0.2:
            col = C["lapis"]            # the colour never came
        out += penc(uc - side * 6, vb, 7.4, 4 if k % 2 == 0 else 5, col, C["paper"], 0.8, a0=-sg * PI / 2 + g.uniform(-0.3, 0.3))
    return out


def yanik(x, y, rx, ry, seed=0, cols=None):
    """A place where the fire reached: scorched wood round a charred heart."""
    g = np.random.default_rng(seed)
    n = 36
    a = np.linspace(0, 2 * PI, n, endpoint=False)
    out = []
    for f, col in zip((1.0, 0.66), cols or (C["wood_dk"], C["char"])):
        rad = f * (1 + 0.5 * ndi.gaussian_filter1d(g.standard_normal(n), 1.5, mode="wrap"))
        out += fill(spline(np.stack([x + rx * rad * np.cos(a), y + ry * rad * np.sin(a)], 1), 3, closed=True), col, 0)
    for _ in range(5):
        t = g.uniform(0, 2 * PI)
        r0, r1 = g.uniform(0.1, 0.3), g.uniform(0.45, 0.6)
        out += brush([(x + rx * r0 * math.cos(t), y + ry * r0 * math.sin(t)), (x + rx * r1 * math.cos(t + 0.2), y + ry * r1 * math.sin(t + 0.2))],
                     1.4, C["wood"], (0.2, 0.6), "paint")
    return out


# ---------------------------------------------------------------- the fourth era: the western manner
def rose(x, y, r, color=None, line=0.8):
    """A rose as the new painters draw it: round, with a turn at its heart."""
    out = disc(x, y, r, color or C["red"], line)
    out += disc(x + r * 0.18, y + r * 0.2, r * 0.82, C["red_dk"], 0)      # its own shade, low and right
    out += disc(x - r * 0.1, y - r * 0.12, r * 0.72, color or C["red"], 0)
    th = np.linspace(0.5, 3.6 * PI, 26)
    out += brush(np.stack([x - r * 0.1 + r * 0.17 * th / PI * np.cos(th), y - r * 0.12 + r * 0.17 * th / PI * np.sin(th)], 1), 0.9, C["red_dk"], (0.1, 0.4))
    out += disc(x - r * 0.38, y - r * 0.42, r * 0.2, C["red_pale"], 0)    # a touch of light
    return out


def celenk(length, period=150.0, drop=6.5):
    """A garland hung in swags along +x, a rose where each swag is tied."""
    n = max(1, round(length / period))
    p = length / n
    out = []
    for k in range(n):
        u = np.linspace(k * p, (k + 1) * p, 26)
        t = (u - k * p) / p
        v = -drop + 2 * drop * (1 - (2 * t - 1) ** 2)
        out += stroke(np.stack([u, v + 1.6], 1), 3.2, C["lapis_dk"], "paint")          # the shade under the swag
        out += stroke(np.stack([u, v], 1), 3.2, C["lapis_lt"], "paint")
        for j in range(2, 25, 3):
            ang = math.atan2(v[j + 1] - v[j - 1], u[j + 1] - u[j - 1])
            for sd in (-1, 1):
                out += fill(xf(almond(8.5, 3.6, k=0.5), u[j], v[j], ang + sd * 0.9), C["lapis"], 0)
        out += rose(k * p + p / 2, drop + 0.5, 4.6)
    for k in range(n + 1):
        x = k * p
        for sd in (-1, 1):
            out += fill(xf(almond(11, 6, k=0.55, base=0.3), x, -drop, PI / 2 + sd * 1.15), C["red_lt"], 0.7)
            out += brush([(x, -drop), (x + sd * 4, -drop + 9), (x + sd * 2.5, -drop + 17)], 2.6, C["red_lt"], (0.1, 0.6), "paint")
        out += disc(x, -drop, 2.6, C["red"], 0.7)
    return out
