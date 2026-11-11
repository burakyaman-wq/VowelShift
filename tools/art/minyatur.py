"""The game's look: a classical Ottoman miniature (after Nakkaş Osman) of the
scribe's desk, seen straight from above.

    python3 tools/art/minyatur.py      ->  assets/art/style/*.svg + *.png

The rules live here so every object is drawn by the same hand:
  * flat colour fields, no gradients, no light, no cast shadow
  * one thin, even outline (tahrir) in dark ink on every field
  * palette: paper, ink, lapis, red, and their tints and shades; no gold
  * important things are drawn larger (document, tiles, notebook)
  * the whole frame is one painted page: one paper grain over everything
SVG groups carry ids so the file opens in Illustrator with named layers.
Text is converted to outlines with the Katip font.
"""
import math
import subprocess
from pathlib import Path

import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image

from tex_core import paper

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/art/style"
KATIP = ROOT / "assets/fonts/Katip-Regular.ttf"

C = {
    "paper": "#ecdcb9", "paper2": "#dcc69c", "glaze": "#f3ead8", "ink": "#2a1b14",
    "lapis": "#2f4d9e", "lapis_dk": "#1e3171", "lapis_lt": "#8ca4d6", "lapis_pale": "#cdd8ef",
    "red": "#b33a29", "red_dk": "#6c2a1d", "red_deep": "#4c1c13", "red_lt": "#dc8a76", "red_pale": "#f1cbbb",
}
LINE = 2.0                      # tahrir width at 1920 x 1080
W, H = 1920, 1080

_font = TTFont(KATIP)
_gs = _font.getGlyphSet()
_cmap = _font.getBestCmap()


# ---------------------------------------------------------------- svg helpers
def text_path(s, x, y, size, anchor="start"):
    sc = size / 1000.0
    names = [_cmap.get(ord(c)) for c in s]
    width = sum(_gs[n].width for n in names if n) * sc
    x0 = x - width / 2 if anchor == "middle" else (x - width if anchor == "end" else x)
    pen = SVGPathPen(_gs)
    cx = x0
    for n in names:
        if not n:
            continue
        _gs[n].draw(TransformPen(pen, (sc, 0, 0, -sc, cx, y)))
        cx += _gs[n].width * sc
    return pen.getCommands(), width


def text(s, x, y, size, fill=None, anchor="start", rot=0.0):
    d, _ = text_path(s, x, y, size, anchor)
    t = f' transform="rotate({rot:.2f} {x:.1f} {y:.1f})"' if rot else ""
    return f'<path d="{d}" fill="{fill or C["ink"]}"{t}/>'


def poly(pts, fill, line=LINE, stroke=None, closed=True):
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + (" Z" if closed else "")
    st = f' stroke="{stroke or C["ink"]}" stroke-width="{line}" stroke-linejoin="round" stroke-linecap="round"' if line else ""
    return f'<path d="{d}" fill="{fill}"{st}/>'


def rect(x, y, w, h, fill, line=LINE, r=0, stroke=None):
    st = f' stroke="{stroke or C["ink"]}" stroke-width="{line}"' if line else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}"{st}/>'


def circle(x, y, r, fill, line=LINE, stroke=None):
    st = f' stroke="{stroke or C["ink"]}" stroke-width="{line}"' if line else ""
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"{st}/>'


def ellipse(x, y, rx, ry, fill, line=LINE, rot=0.0):
    t = f' transform="rotate({rot:.1f} {x:.1f} {y:.1f})"' if rot else ""
    return f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" stroke="{C["ink"]}" stroke-width="{line}"{t}/>'


def line(pts, width=LINE, color=None, cap="round"):
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<path d="{d}" fill="none" stroke="{color or C["ink"]}" stroke-width="{width}" stroke-linecap="{cap}" stroke-linejoin="round"/>'


def group(gid, items, transform=""):
    t = f' transform="{transform}"' if transform else ""
    return f'<g id="{gid}"{t}>' + "".join(items) + "</g>"


def place(x, y, rot=0.0, s=1.0):
    return f"translate({x:.1f} {y:.1f}) rotate({rot:.2f}) scale({s})"


# ---------------------------------------------------------------- motifs
def durak(x, y, r=11, fill=None):
    """Sentence stop and the hover mark: an eight-petal red rose."""
    out = []
    for k in range(8):
        a = math.pi * k / 4
        out.append(circle(x + 0.55 * r * math.cos(a), y + 0.55 * r * math.sin(a), 0.42 * r, fill or C["red"], 1.2))
    out.append(circle(x, y, 0.38 * r, C["paper"], 1.2))
    return "".join(out)


def cintemani(x, y, s, col_balls, col_waves):
    out = [circle(x + dx * s, y + dy * s, 7 * s, col_balls, 1.2) for dx, dy in ((-9, 0), (9, 0), (0, -14))]
    for k in (0, 1):
        pts = [(x - 24 * s + t * 48 * s, y + (16 + 8 * k) * s + 3.5 * s * math.sin(t * 4 * math.pi)) for t in np.linspace(0, 1, 24)]
        out.append(line(pts, 3.2 * s, col_waves))
    return "".join(out)


def flame_tongue(x, y, a, L, wd, fill):
    """One tongue of a flaming nimbus: swells, then curls to a point."""
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    left, right = [], []
    for t in np.linspace(0, 1, 14):
        width = wd * math.sin(math.pi * min(1, t * 1.15)) * (1 - t) ** 0.35
        curl = 0.22 * L * t ** 2.4
        cxp = x + ux * L * t + px * curl
        cyp = y + uy * L * t + py * curl
        left.append((cxp + px * width, cyp + py * width))
        right.append((cxp - px * width, cyp - py * width))
    return poly(left + right[::-1], fill, 1.2)


def flame_halo(x, y, r):
    """The lamp's light as a drawn thing: a flat disc of light, then a plume of
    rising flame tongues around a pale core."""
    out = [circle(x, y - r * 0.25, r * 1.05, C["red_pale"], 1.2), circle(x, y - r * 0.25, r * 0.82, "#f6dccf", 0)]
    g = np.random.default_rng(5)
    for k, a in enumerate(np.linspace(-math.pi / 2 - 0.95, -math.pi / 2 + 0.95, 7)):
        L = r * (0.95 - 0.35 * abs(a + math.pi / 2)) * g.uniform(0.85, 1.05)
        out.append(flame_tongue(x, y + r * 0.1, a, L, r * 0.15, C["red"] if k % 2 else C["red_lt"]))
    for a in np.linspace(-math.pi / 2 - 0.5, -math.pi / 2 + 0.5, 3):
        out.append(flame_tongue(x, y + r * 0.08, a, r * 0.45, r * 0.1, C["paper"]))
    return "".join(out)


def _unused_flame_rings(x, y, r):
    out = []
    for ring, (L, n, wd, col) in enumerate(((r, 13, r * 0.17, C["red_pale"]), (r * 0.76, 10, r * 0.16, C["red_lt"]), (r * 0.52, 8, r * 0.15, C["red"]))):
        for k in range(n):
            a = 2 * math.pi * k / n + ring * 0.24
            up = -math.pi / 2
            d = (a - up + math.pi) % (2 * math.pi) - math.pi
            a2 = up + d * 0.78
            L2 = L * (0.72 + 0.38 * (1 + math.cos(d)) / 2)
            out.append(flame_tongue(x, y, a2, L2, wd, col))
    out.append(circle(x, y, r * 0.2, C["red_pale"], 1.2))
    out.append(flame_tongue(x - r * 0.08, y + r * 0.02, -0.3, r * 0.3, r * 0.08, C["paper"]))
    return "".join(out)


# ---------------------------------------------------------------- objects
def carpet_band():
    """A strip of the floor carpet shows round the desk: a red field, a lapis
    border with a running cintamani-and-lozenge chain."""
    out = [rect(0, 0, W, H, C["red"], 0)]
    b = 30
    out.append(rect(6, 6, W - 12, H - 12, C["lapis_dk"], 1.4))
    for k, x in enumerate(np.arange(24, W, 46)):
        for y in (21, H - 21):
            out.append(poly([(x, y - 9), (x + 9, y), (x, y + 9), (x - 9, y)], C["paper"] if k % 2 else C["red_lt"], 1.0))
    for k, y in enumerate(np.arange(24, H, 46)):
        for x in (21, W - 21):
            out.append(poly([(x, y - 9), (x + 9, y), (x, y + 9), (x - 9, y)], C["paper"] if k % 2 else C["red_lt"], 1.0))
    out.append(rect(b + 6, b + 6, W - 2 * b - 12, H - 2 * b - 12, C["red"], 1.4))
    return out


def desk():
    g = np.random.default_rng(3)
    x0, y0, x1, y1 = 58, 52, W - 58, H - 52
    out = carpet_band()
    out.append(rect(x0 - 8, y0 - 8, x1 - x0 + 16, y1 - y0 + 16, C["red_deep"], LINE, r=10))
    out.append(rect(x0, y0, x1 - x0, y1 - y0, "#5a2519", LINE, r=6))
    for k in range(1, 4):
        yy = y0 + (y1 - y0) * k / 4
        out.append(line([(x0, yy), (x1, yy)], 1.6, C["red_deep"]))
    for k in range(26):
        yb = y0 + g.uniform(8, y1 - y0 - 8)
        xa = g.uniform(x0, x1 - 500)
        L = g.uniform(260, 760)
        amp = g.uniform(2, 6)
        pts = [(xa + t * L, yb + amp * math.sin(t * math.pi * g.uniform(1, 3))) for t in np.linspace(0, 1, 30)]
        out.append(line(pts, 1.0, "#47190f"))
    for _ in range(3):
        x, y = g.uniform(x0 + 200, x1 - 200), g.uniform(y0 + 100, y1 - 100)
        for r in (24, 15, 7):
            out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r}" ry="{r * 0.38:.1f}" fill="none" stroke="#47190f" stroke-width="1.1"/>')
    return group("masa", out)


def cartouche(cx, cy, w, h, fill):
    """Title cartouche: a band whose ends break into split-leaf (rumi) tips."""
    pts = []
    for t in np.linspace(-1, 1, 9):
        pts.append((cx + t * (w / 2 - h * 0.6), cy - h / 2))
    for a in np.linspace(-math.pi / 2, math.pi / 2, 9):
        pts.append((cx + w / 2 - h * 0.6 + h * 0.6 * math.cos(a) + (h * 0.35 if abs(a) < 0.2 else 0), cy + h / 2 * math.sin(a)))
    for t in np.linspace(1, -1, 9):
        pts.append((cx + t * (w / 2 - h * 0.6), cy + h / 2))
    for a in np.linspace(math.pi / 2, 3 * math.pi / 2, 9):
        pts.append((cx - w / 2 + h * 0.6 + h * 0.6 * math.cos(a) - (h * 0.35 if abs(a - math.pi) < 0.2 else 0), cy + h / 2 * math.sin(a)))
    return poly(pts, fill)


def corner_piece(x, y, sx, sy, s=26):
    pts = [(x, y), (x + sx * s, y), (x + sx * s * 0.75, y + sy * s * 0.28), (x + sx * s * 0.28, y + sy * s * 0.75), (x, y + sy * s)]
    return poly(pts, C["lapis"], 1.4) + circle(x + sx * s * 0.32, y + sy * s * 0.32, 4, C["red"], 1.0)


def document_page(w, h, title, lines, size, seed=0):
    """Text first: two thin rules, a small title, corner pieces; the rest is writing."""
    out = [rect(0, 0, w, h, C["paper"])]
    m = 26
    out.append(rect(m, m, w - 2 * m, h - 2 * m, "none", 2.4, stroke=C["lapis"]))
    out.append(rect(m + 6, m + 6, w - 2 * m - 12, h - 2 * m - 12, "none", 1.1, stroke=C["red"]))
    for sx, sy, x, y in ((1, 1, m + 6, m + 6), (-1, 1, w - m - 6, m + 6), (1, -1, m + 6, h - m - 6), (-1, -1, w - m - 6, h - m - 6)):
        out.append(corner_piece(x, y, sx, sy))
    cw, ch = min(w * 0.5, 300), 46
    cx, cy = w / 2, m + 44
    out.append(cartouche(cx, cy, cw, ch, C["lapis"]))
    out.append(text(title, cx, cy + 13, 34, C["paper"], "middle"))
    widest = max(text_path(ln, 0, 0, 100)[1] for ln in lines) / 100
    size = min(size, (w - 2 * m - 110) / widest)
    y = cy + ch / 2 + 26 + size
    for i, ln in enumerate(lines):
        out.append(text(ln, m + 34, y + i * size * 1.62, size))
        if ln.endswith("."):
            _, wd = text_path(ln, 0, 0, size)
            out.append(durak(m + 34 + wd + 20, y + i * size * 1.62 - size * 0.3, 10))
    return out


def copy_sheet(w, h, lines, size, note=None):
    out = [rect(0, 0, w, h, C["paper"])]
    for i in range(7):
        out.append(line([(40, 92 + i * size * 1.75), (w - 40, 92 + i * size * 1.75)], 0.8, C["paper2"]))
    for i, ln in enumerate(lines):
        out.append(text(ln, 44, 84 + i * size * 1.75, size))
    if note:
        out.append(text(note, w - 30, h - 120, 22, C["red"], "end", rot=-28))
    return out


PICTO = {
    "R1": [[(-60, 0), (-45, -14), (-30, 0), (-15, 14), (0, 0)], [(0, 0), (14, -18), (28, 18), (42, -18), (58, 14)]],
    "R2": "two",
    "R3": [[(-58, 26), (-14, 26)], [(14, -22), (58, -22)], [(-36, 14), (-6, -12), (22, -22)]],
    "R4": [[(-58, 14), (-12, 14)], [(12, -8), (58, -8)], [(-6, 4), (14, -4)]],
    "R5": [[(-60, -14), (28, -14), (28, 22)], [(46, 6), (52, 16)]],
    "R6": [[(-62, -20), (-40, 18), (-18, -20)], "curl"],
    "R7": [[(-60, 6), (-8, 6)], [(6, 6), (16, -6), (28, 6), (40, -6), (52, 6)]],
    "R8": [[(-60, -10), (20, -10)], [(36, 0), (40, 14)]],
}


def tulip(x, y, a, s=1.0):
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    pts = [(x, y), (x + (ux * 6 + px * 6) * s, y + (uy * 6 + py * 6) * s), (x + (ux * 13 + px * 3) * s, y + (uy * 13 + py * 3) * s),
           (x + ux * 9 * s, y + uy * 9 * s), (x + (ux * 13 - px * 3) * s, y + (uy * 13 - py * 3) * s), (x + (ux * 6 - px * 6) * s, y + (uy * 6 - py * 6) * s)]
    return poly(pts, C["red"], 1.0)


def tile_frame(w=150, h=200):
    out = [rect(0, 0, w, h, C["glaze"], LINE, r=6), rect(9, 9, w - 18, h - 18, "none", 3.0, r=3, stroke=C["lapis"])]
    for x, y, a in ((16, 16, math.pi / 4), (w - 16, 16, 3 * math.pi / 4), (16, h - 16, -math.pi / 4), (w - 16, h - 16, -3 * math.pi / 4)):
        out.append(tulip(x, y, a, 0.9))
    return out


def picto_only(rule, w=150, h=200):
    full = tile(rule, "", [], w, h)
    return full[7:]          # drop the frame, the empty name and the four tulips


def tile(rule, name, lines, w=150, h=200):
    out = [rect(0, 0, w, h, C["glaze"], LINE, r=6),
           rect(9, 9, w - 18, h - 18, "none", 3.0, r=3, stroke=C["lapis"]),
           text(name, w / 2, 36, 17, C["lapis_dk"], "middle")]
    for x, y, a in ((16, 16, math.pi / 4), (w - 16, 16, 3 * math.pi / 4), (16, h - 16, -math.pi / 4), (w - 16, h - 16, -3 * math.pi / 4)):
        out.append(tulip(x, y, a, 0.9))
    cx, cy = w / 2, 82
    p = PICTO.get(rule)
    if p == "two":
        out += [circle(cx - 46, cy - 6, 9, C["lapis"], 1.2), circle(cx - 24, cy + 8, 9, C["lapis"], 1.2),
                line([(cx - 4, cy), (cx + 14, cy)], 4, C["lapis"]), line([(cx + 26, cy), (cx + 58, cy)], 9, C["lapis"])]
    elif p:
        for path in p:
            if path == "curl":
                pts = [(cx + 30 + 26 * math.cos(a) * (1 - a / 9), cy + 26 * math.sin(a) * (1 - a / 9)) for a in np.linspace(0, 7.5, 40)]
            else:
                pts = [(cx + x * 0.9, cy + y * 0.9) for x, y in path]
            out.append(line(pts, 8.0, C["lapis_dk"]))
            out.append(line(pts, 5.0, C["lapis"]))
        if rule == "R5":
            out.append(circle(cx + 50, cy + 30, 6, C["lapis"], 1.2))
        if rule == "R8":
            out.append(circle(cx + 44, cy + 22, 5, C["lapis"], 1.2))
    for i, ln in enumerate(lines):
        out.append(text(ln, 22, 136 + i * 26, 21))
    return out


def tray(n=5, slot_w=162, slot_h=212):
    w, h = n * slot_w + 24, slot_h + 24
    out = [rect(0, 0, w, h, C["red"], LINE, r=8)]
    for k in range(n):
        out.append(rect(12 + k * slot_w + 3, 12, slot_w - 6, slot_h, C["red_deep"], 1.4, r=4))
    return out, w, h


def notebook(w=460, h=330, left=(), right=()):
    out = [rect(-14, -14, w + 28, h + 28, C["red"], LINE, r=6),
           rect(-8, -8, w + 16, h + 16, "none", 2.0, r=4, stroke=C["red_pale"]),
           rect(0, 0, w / 2, h, C["paper"]), rect(w / 2, 0, w / 2, h, C["paper"])]
    for i in range(1, int((h - 40) / 27) + 1):
        y = 46 + (i - 1) * 27
        out.append(line([(16, y + 6), (w / 2 - 14, y + 6)], 0.7, C["paper2"]))
        out.append(line([(w / 2 + 14, y + 6), (w - 16, y + 6)], 0.7, C["paper2"]))
    out.append(line([(w / 2, 0), (w / 2, h)], 2.2))
    for i, ln in enumerate(left):
        out.append(text(ln, 22, 46 + i * 31, 21 if i else 25, C["red"] if i == 0 else None))
    for i, ln in enumerate(right):
        out.append(text(ln, w / 2 + 22, 46 + i * 31, 21 if i else 25, C["red"] if i == 0 else None))
    return out


def lamp():
    """A glazed oil lamp from above: round bowl, filling hole, ring handle, spout."""
    out = [circle(-64, 0, 17, "none", 7, C["lapis_dk"]),
           poly([(20, -16), (66, -9), (78, 0), (66, 9), (20, 16)], C["lapis"]),
           circle(0, 0, 40, C["lapis"]),
           circle(0, 0, 31, "none", 1.2, C["lapis_pale"])]
    for k in range(8):
        a = 2 * math.pi * k / 8
        out.append(ellipse(22 * math.cos(a), 22 * math.sin(a), 6, 3, C["paper"], 1.0, math.degrees(a)))
    out += [circle(0, 0, 11, C["ink"], 1.2), circle(70, 0, 4, C["ink"], 1.0)]
    return out


def inkwell():
    return [circle(0, 0, 32, C["glaze"]), circle(0, 0, 24, "none", 3, C["lapis"]),
            circle(0, 0, 15, C["ink"], 1.4)] + [circle(22 * math.cos(a), 22 * math.sin(a), 3, C["lapis"], 0) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]


def pen(length=230):
    return [poly([(0, -5), (length - 34, -5), (length, 0), (length - 34, 5), (0, 5)], C["paper2"]),
            line([(length * 0.33, -5), (length * 0.33, 5)], 1.2), line([(length * 0.66, -5), (length * 0.66, 5)], 1.2),
            poly([(length - 16, -2.6), (length, 0), (length - 16, 2.6)], C["ink"], 0)]


def pen_case(w=330, h=46):
    return [rect(0, 0, w, h, C["red"], LINE, r=h / 2), rect(10, 8, w - 20, h - 16, "none", 1.4, r=(h - 16) / 2, stroke=C["red_pale"]),
            circle(w - 26, h / 2, 6, C["lapis"], 1.2)]


def bohca(s=250):
    """Wrapping cloth with cintamani: one of the few patterned things."""
    out = [poly([(0, -s / 2), (s / 2, 0), (0, s / 2), (-s / 2, 0)], C["lapis"])]
    for i in range(-2, 3):
        for j in range(-2, 3):
            x, y = (i - j) * s / 7.0, (i + j) * s / 7.0
            if abs(x) + abs(y) < s / 2 - 26:
                out.append(cintemani(x, y, 0.62, C["red"], C["paper"]))
    out.append(poly([(0, -s / 2 + 12), (s / 2 - 12, 0), (0, s / 2 - 12), (-s / 2 + 12, 0)], "none", 1.4, C["paper"]))
    return out


def scroll(length=210, r=22):
    return [rect(0, -r, length, 2 * r, C["paper"], LINE, r=6),
            ellipse(length, 0, 7, r, C["paper2"], 1.4),
            rect(length * 0.3, -r - 1, 10, 2 * r + 2, C["red"], 1.2), rect(length * 0.62, -r - 1, 10, 2 * r + 2, C["red"], 1.2),
            circle(length * 0.47, r * 0.2, 17, C["red"], LINE), circle(length * 0.47, r * 0.2, 10, "none", 1.2, C["red_pale"])]


def slip(w=300, h=180, lines=()):
    out = [poly([(0, 0), (w, 0), (w, h - 34), (w - 34, h), (0, h)], C["paper"]),
           poly([(w, h - 34), (w - 30, h - 30), (w - 34, h)], C["paper2"], 1.4)]
    for i, ln in enumerate(lines):
        out.append(text(ln, 20, 40 + i * 30, 21))
    out.append(circle(w - 62, h - 34, 13, C["red"], 1.4))
    out.append(circle(w - 62, h - 34, 7, "none", 1.0, C["red_pale"]))
    return out


# ---------------------------------------------------------------- frames
DOC2 = ["Mīros Mērom ageti.", "Mēros nākos."]


def era2_desk():
    parts = [desk()]
    parts.append(group("kandil_govde", lamp(), place(140, 160, -18)))
    parts.append(group("kandil", [flame_halo(0, 0, 66)], place(212, 140)))
    parts.append(group("kalemdan", pen_case(), place(720, 88, 1)))
    parts.append(group("hokka", inkwell(), place(1330, 140)))
    parts.append(group("belge", document_page(680, 440, "Kerdāgros", DOC2, 74), place(610, 150, -1.2)))
    parts.append(group("kopya", copy_sheet(420, 500, ["Mīros Mīrom ageti.", "Mīros nēkos."], 40, "nēkos: sürgün mü, ölü mü?"), place(1330, 250, 3)))
    parts.append(group("kalem1", pen(), place(1300, 800, -12)))
    parts.append(group("kalem2", pen(200), place(1250, 850, -4)))
    left = ["Sözlük", "rīgos — bey", "grēnos — tahıl", "ēgros — tarla", "thītos — borç", "nēkos — sürgün", "nīkos — ölü"]
    right = ["Duyduklarım", "rīgos", "grēnos", "ēgros", "thītos"]
    parts.append(group("defter", notebook(470, 350, left, right), place(84, 400, 2)))
    tr, tw, th = tray()
    tiles = [("R3", "ē yükselir", ["ē → ī"]), ("R4", "ā kayar", ["ā → ē"]), ("R1", "Sert ünsüzler", ["bh → ph", "dh → th", "gh → kh"]),
             ("R2", "Çift ünlüler", ["ei → ī", "eu → ū"])]
    titems = list(tr)
    for k, (r, n, ls) in enumerate(tiles):
        titems.append(group(f"karo_{r}", tile(r, n, ls), f"translate({12 + k * 162 + 6:.0f} 18)"))
    parts.append(group("tepsi", titems, place(600, 790)))
    parts.append(group("bohca", bohca(250) + [group("rulo", scroll(), place(-100, -6, -18))], place(1700, 210)))
    parts.append(group("pusula", slip(300, 190, ["Rīgos kurucuların", "kaydını istiyor.", "Kopyan bugünün", "diliyle olmalı.", "Acele et."]), place(1560, 790, -6)))
    parts.append(group("secim", [durak(1820, 320, 13)]))
    return parts


def reading_view():
    parts = [desk()]
    parts.append(group("belge", document_page(1520, 720, "Kerdāgros", DOC2, 150), place(200, 180, 0)))
    return parts


def sprite(name, parts, w, h, pad=8):
    """One object on a transparent ground, for the game."""
    out = ROOT / "assets/art/sprites"
    out.mkdir(parents=True, exist_ok=True)
    flt = ('<defs><filter id="el" x="-5%" y="-5%" width="110%" height="110%">'
           '<feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="2" seed="7" result="n"/>'
           '<feDisplacementMap in="SourceGraphic" in2="n" scale="2.2" xChannelSelector="R" yChannelSelector="G"/>'
           '</filter></defs>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w + 2 * pad}" height="{h + 2 * pad}" '
           f'viewBox="{-pad} {-pad} {w + 2 * pad} {h + 2 * pad}">' + flt + '<g filter="url(#el)">' + "".join(parts) + "</g></svg>")
    src = OUT / "sprites_src"
    src.mkdir(parents=True, exist_ok=True)
    (src / f"{name}.svg").write_text(svg)
    subprocess.run(["rsvg-convert", "-o", str(out / f"{name}.png"), str(src / f"{name}.svg")], check=True)


def desk_plate():
    """The desk with its fixed things: lamp and flame, pen case, inkwell, pens, cloth and scroll."""
    return [desk(),
            group("kandil_govde", lamp(), place(140, 160, -18)),
            group("kandil", [flame_halo(0, 0, 66)], place(212, 140)),
            group("kalemdan", pen_case(), place(720, 88, 1)),
            group("hokka", inkwell(), place(1330, 140)),
            group("bohca", bohca(190) + [group("rulo", scroll(156, 18), place(-78, -6, -18))], place(1838, 168))]


def export_sprites():
    OUT.mkdir(parents=True, exist_ok=True)
    out = ROOT / "assets/art/sprites"
    out.mkdir(parents=True, exist_ok=True)
    plate = OUT / "sprites_src" / "masa_cag2.svg"
    plate.parent.mkdir(parents=True, exist_ok=True)
    plate.write_text(svg_doc(desk_plate()))
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-o", str(out / "masa_cag2.png"), str(plate)], check=True)
    sprite("karo_cerceve", tile_frame(), 150, 200)
    for r in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"):
        sprite(f"picto_{r}", picto_only(r), 150, 200)
    tr, tw, th = tray()
    sprite("tepsi", tr, tw, th)
    sprite("durak", [durak(14, 14, 13)], 28, 28, 2)
    sprite("belge_kagit", document_page(680, 440, "", ["x"], 10)[:8], 680, 440)
    sprite("kopya_kagit", copy_sheet(420, 500, [], 40), 420, 500)
    sprite("pusula", slip(360, 250, []), 360, 250)
    sprite("kalem", pen(), 230, 10, 8)
    sprite("belge_okuma", document_page(1520, 760, "", ["x"], 10)[:8], 1520, 760)
    seal_parts = [circle(40, 40, 36, C["red"]), circle(40, 40, 27, "none", 1.4, C["red_pale"])]
    for k in range(8):
        a = math.pi * k / 4
        seal_parts.append(circle(40 + 12 * math.cos(a), 40 + 12 * math.sin(a), 5, C["red_pale"], 1.0))
    seal_parts.append(circle(40, 40, 5, C["red"], 1.0))
    sprite("muhur", seal_parts, 80, 80)
    sprite("defter", notebook(520, 420), 520, 420, 20)
    from tex_core import fbm
    grain_path = OUT / "kagit_doku.png"
    if not grain_path.exists():
        g, _ = paper(W, H, 9, tone=(236, 226, 204), age=0.6, laid=False)
        Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).save(grain_path)
    grain = np.asarray(Image.open(grain_path).convert("RGB")).astype(np.float32) / 255
    rel = np.clip(grain / grain.mean(axis=(0, 1), keepdims=True), 0.75, 1.1) ** 0.8
    mottle = 1 + 0.08 * (fbm(W, H, 5, 6, 0.6, 21) - 0.5)[..., None] + 0.06 * (fbm(W, H, 3, 160, 0.6, 22) - 0.5)[..., None]
    mult = np.clip(rel * mottle, 0, 1)
    Image.fromarray((mult * 255).astype(np.uint8)).save(out / "sayfa_doku.png")


def svg_doc(parts):
    flt = ('<defs><filter id="el" x="-2%" y="-2%" width="104%" height="104%">'
           '<feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="2" seed="7" result="n"/>'
           '<feDisplacementMap in="SourceGraphic" in2="n" scale="2.2" xChannelSelector="R" yChannelSelector="G"/>'
           '</filter></defs>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + flt
            + '<g id="resim" filter="url(#el)">' + "".join(parts) + "</g></svg>")


def render(name, parts):
    OUT.mkdir(parents=True, exist_ok=True)
    svg = OUT / f"{name}.svg"
    svg.write_text(svg_doc(parts))
    png = OUT / f"{name}.png"
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-o", str(png), str(svg)], check=True)
    grain_path = OUT / "kagit_doku.png"
    if not grain_path.exists():
        g, _ = paper(W, H, 9, tone=(236, 226, 204), age=0.6, laid=False)
        Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).save(grain_path)
    grain = np.asarray(Image.open(grain_path).convert("RGB")).astype(np.float32) / 255
    im = np.asarray(Image.open(png).convert("RGB")).astype(np.float32)
    from tex_core import fbm
    rel = grain / grain.mean(axis=(0, 1), keepdims=True)
    mottle = 1 + 0.08 * (fbm(W, H, 5, 6, 0.6, 21) - 0.5)[..., None] + 0.06 * (fbm(W, H, 3, 160, 0.6, 22) - 0.5)[..., None]
    blue = np.clip((im[..., 2] - im[..., 0]) / 120, 0, 1)[..., None]
    mottle = mottle * (1 + blue * 0.10 * (fbm(W, H, 2, 300, 0.6, 23) - 0.5)[..., None])
    out = np.clip(im * np.clip(rel, 0.75, 1.1) ** 0.8 * mottle, 0, 255)
    Image.fromarray(out.astype(np.uint8)).save(png)
    return png


if __name__ == "__main__":
    import sys
    if "--sprites" in sys.argv:
        export_sprites()
        print("sprites written")
    else:
        print(render("cag2_masa", era2_desk()))
        print(render("cag2_okuma", reading_view()))
