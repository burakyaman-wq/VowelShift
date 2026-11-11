"""Build *Katip*, the scribe's hand used for every manuscript in the game.

Method: take the Latin letterforms of Aref Ruqaa (SIL OFL 1.1; its Latin is
drawn after Zapf's Euler), reduce each glyph to its skeleton, then re-draw
that skeleton with a reed-pen nib held at an Arabic angle (about 70 degrees
to the baseline). The result has thick horizontals and thin verticals, the
reverse of a European broad pen, which gives Latin letters a Naskh rhythm.
Diacritics the source lacks (macron, cedilla, breve, dot) are drawn as nib
strokes; the macron comes out as a heavy bar, so long vowels read clearly.

    python3 tools/art/katip_font.py          # writes assets/fonts/Katip-Regular.ttf

The output is a derivative of an OFL font and stays under the OFL (see
assets/fonts/OFL.txt). It must not be named "EURM10" or "Aref Ruqaa".
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.signal import fftconvolve
from skimage.measure import approximate_polygon, find_contours
from skimage.morphology import skeletonize
from fontTools.agl import UV2AGL
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets/fonts/src/ArefRuqaa-Latin.ttf"
OUT = ROOT / "assets/fonts/Katip-Regular.ttf"

UPM = 1000
NIB_L, NIB_T, NIB_ANGLE = 110, 16, 70      # nib width, nib thickness, degrees
SMOOTH = 2.4                                # contour smoothing (px = units)
PRUNE = 48                                  # drop skeleton spurs shorter than this
PAD = 170
ASC, DESC = 1000, 320                       # canvas above / below the baseline
XH, CAP = 462, 683                          # source x-height and cap height
SIDE = 5                                    # extra side bearing for the nib
TRACK = 0.95                                # tighten the source spacing
DOT = 0.27                                  # rhombic dot: drag length as a share of the nib

# composed letters the source does not have, or that we redraw: base + mark
COMPOSE = {
    "ā": ("a", "macron"), "ē": ("e", "macron"), "ī": ("ı", "macron"),
    "ō": ("o", "macron"), "ū": ("u", "macron"),
    "Ā": ("A", "macron"), "Ē": ("E", "macron"), "Ī": ("I", "macron"),
    "Ō": ("O", "macron"), "Ū": ("U", "macron"),
    "ş": ("s", "cedilla"), "Ş": ("S", "cedilla"),
    "ğ": ("g", "breve"), "Ğ": ("G", "breve"), "İ": ("I", "dot"),
    "â": ("a", "circ"), "î": ("ı", "circ"), "û": ("u", "circ"),
    "Â": ("A", "circ"), "Î": ("I", "circ"), "Û": ("U", "circ"),
}
EXTRA = "ıçÇöÖüÜ·«»‘’“”–—…"

# drawn signs for rule cards and notes: (advance, list of skeleton polylines)
# in font units with y up from the baseline
SIGNS = {
    "→": (640, [[(70, 250), (560, 250)], [(430, 360), (565, 250), (430, 140)]]),
    "∅": (600, [[(300 + 200 * np.cos(a), 270 + 200 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 60)],
                [(130, 20), (470, 520)]]),
}


def nib_kernel(L=NIB_L, t=NIB_T, angle=NIB_ANGLE):
    r = int(np.ceil(L / 2 + t)) + 1
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1].astype(float)
    th = np.radians(angle)
    ux, uy = np.cos(th), -np.sin(th)
    along = xx * ux + yy * uy
    perp = -xx * uy + yy * ux
    return ((np.abs(along) <= L / 2) & (np.abs(perp) <= t / 2)).astype(np.float32)


KERNEL = nib_kernel()


def neighbours(sk):
    k = np.ones((3, 3), int)
    return ndi.convolve(sk.astype(int), k, mode="constant") - sk.astype(int)


def prune(sk, limit=PRUNE, rounds=2):
    """Remove short spurs (serif ghosts) that end in a junction."""
    sk = sk.copy()
    h, w = sk.shape
    for _ in range(rounds):
        nb = neighbours(sk)
        for y, x in np.argwhere(sk & (nb == 1)):
            path, cy, cx, hit = [(y, x)], y, x, False
            seen = {(y, x)}
            while len(path) <= limit:
                nxt = [(cy + dy, cx + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                       if (dy or dx) and 0 <= cy + dy < h and 0 <= cx + dx < w
                       and sk[cy + dy, cx + dx] and (cy + dy, cx + dx) not in seen]
                if not nxt:
                    break
                if len(nxt) > 1 or nb[nxt[0]] >= 3:
                    hit = True
                    break
                cy, cx = nxt[0]
                seen.add((cy, cx))
                path.append((cy, cx))
            if hit and len(path) < limit:
                for p in path:
                    sk[p] = False
        sk = skeletonize(sk)
    return sk


def polyline(img, pts):
    ImageDraw.Draw(img).line([tuple(map(float, p)) for p in pts], fill=255, width=1)


def mark_skeleton(kind, w, h, cx, base_y, upper):
    """Draw a diacritic as a one-pixel path; the nib gives it its body."""
    im = Image.new("L", (w, h), 0)
    top = base_y - (CAP if upper else XH)
    if kind == "macron":
        y = top - (118 if upper else 150)
        polyline(im, [(cx - 92, y + 4), (cx + 92, y - 4)])
    elif kind == "cedilla":
        t = np.linspace(0, 1, 24)
        p0, p1, p2 = np.array([cx + 6, base_y + 8]), np.array([cx + 58, base_y + 70]), np.array([cx - 52, base_y + 112])
        pts = [(1 - s) ** 2 * p0 + 2 * (1 - s) * s * p1 + s ** 2 * p2 for s in t]
        polyline(im, pts)
    elif kind == "breve":
        y = top - (128 if upper else 168)
        a = np.linspace(np.pi * 0.08, np.pi * 0.92, 30)
        pts = [(cx - 78 * np.cos(v), y + 48 * np.sin(v)) for v in a]
        polyline(im, pts)
    elif kind == "circ":
        y = top - (120 if upper else 150)
        polyline(im, [(cx - 70, y + 40), (cx, y - 36), (cx + 70, y + 40)])
    elif kind == "dot":
        y = top - 120
        th = np.radians(NIB_ANGLE - 90)
        polyline(im, [(cx - 18 * np.cos(th), y + 18 * np.sin(th)), (cx + 18 * np.cos(th), y - 18 * np.sin(th))])
    return np.array(im) > 0


def render_skeleton(font, ch, adv):
    w, h = adv + 2 * PAD, PAD + ASC + DESC + PAD
    base_y = PAD + ASC
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).text((PAD, base_y), ch, font=font, fill=255, anchor="ls")
    m = np.array(im) > 127
    if not m.any():
        return None, base_y
    sk = prune(skeletonize(m))
    return rhombic_dots(sk), base_y


def rhombic_dots(sk):
    """A pressed reed pen leaves a rhombus, not a hairline: dots, periods and
    umlauts become a short drag perpendicular to the nib edge."""
    lab, n = ndi.label(sk, structure=np.ones((3, 3)))
    if n == 0:
        return sk
    out = sk.copy()
    th = np.radians(NIB_ANGLE - 90)
    ux, uy = np.cos(th), -np.sin(th)
    d = DOT * NIB_L
    for i, sl in enumerate(ndi.find_objects(lab), start=1):
        hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if max(hh, ww) < 40:
            ys, xs = np.nonzero(lab[sl] == i)
            cy, cx = ys.mean() + sl[0].start, xs.mean() + sl[1].start
            out[lab == i] = False
            im = Image.new("L", (sk.shape[1], sk.shape[0]), 0)
            polyline(im, [(cx - d * ux, cy - d * uy), (cx + d * ux, cy + d * uy)])
            out |= np.array(im) > 0
    return out


def nib_stroke(sk):
    ink = fftconvolve(sk.astype(np.float32), KERNEL, mode="same") > 0.5
    return ndi.gaussian_filter(ink.astype(np.float32), SMOOTH)


def contains(poly, pt):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


def area(poly):
    p = np.asarray(poly, float)
    return 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])


SHIFT = 0


def glyph_from_field(field, base_y):
    padded = np.pad(field, 1)
    polys = []
    for c in find_contours(padded, 0.5):
        c = approximate_polygon(c, tolerance=0.7)
        pts = [(round((col - 1 - PAD) - SHIFT + SIDE), round(base_y - (row - 1))) for row, col in c]
        clean = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        if clean and clean[0] == clean[-1]:
            clean = clean[:-1]
        if len(clean) >= 3 and abs(area(clean)) > 30:
            polys.append(clean)
    pen = TTGlyphPen(None)
    for i, poly in enumerate(polys):
        depth = sum(contains(other, poly[0]) for j, other in enumerate(polys) if j != i)
        a = area(poly)
        outer = depth % 2 == 0
        if (outer and a > 0) or (not outer and a < 0):
            poly = poly[::-1]
        pen.moveTo(poly[0])
        for p in poly[1:]:
            pen.lineTo(p)
        pen.closePath()
    return pen.glyph()


def build():
    global SHIFT
    src = TTFont(SRC)
    cmap = src.getBestCmap()
    hmtx = src["hmtx"]
    font = ImageFont.truetype(str(SRC), UPM)

    chars = [chr(c) for c in range(0x21, 0x7F) if c in cmap]
    chars += [c for c in EXTRA if ord(c) in cmap]
    chars += list(COMPOSE)

    glyphs, metrics, cmap_out = {}, {}, {}
    order = [".notdef", "space"]
    glyphs[".notdef"] = TTGlyphPen(None).glyph()
    metrics[".notdef"] = (500, 0)
    glyphs["space"] = TTGlyphPen(None).glyph()
    metrics["space"] = (hmtx[cmap[0x20]][0] + 70, 0)
    cmap_out[0x20] = "space"
    cmap_out[0xA0] = "space"

    for ch, (adv, paths) in SIGNS.items():
        w, h = adv + 2 * PAD, PAD + ASC + DESC + PAD
        base_y = PAD + ASC
        im = Image.new("L", (w, h), 0)
        for path in paths:
            polyline(im, [(PAD + x, base_y - y) for x, y in path])
        field = nib_stroke(np.array(im) > 0)
        SHIFT = 0
        name = UV2AGL.get(ord(ch), f"uni{ord(ch):04X}")
        glyphs[name] = glyph_from_field(field, base_y)
        metrics[name] = (adv + 2 * SIDE, 0)
        cmap_out[ord(ch)] = name
        order.append(name)

    for ch in chars:
        base, mark = COMPOSE.get(ch, (ch, None))
        adv = hmtx[cmap[ord(base)]][0]
        sk, base_y = render_skeleton(font, base, adv)
        if sk is None:
            continue
        if mark:
            ys, xs = np.nonzero(sk)
            cx = (xs.min() + xs.max()) / 2
            if base in "aeou":
                cx += 6
            sk = sk | mark_skeleton(mark, sk.shape[1], sk.shape[0], cx, base_y, base.isupper())
        field = nib_stroke(sk)
        SHIFT = adv * (1 - TRACK) / 2
        name = UV2AGL.get(ord(ch), f"uni{ord(ch):04X}")
        glyphs[name] = glyph_from_field(field, base_y)
        metrics[name] = (int(adv * TRACK) + 2 * SIDE, 0)
        cmap_out[ord(ch)] = name
        order.append(name)

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap_out)
    fb.setupGlyf(glyphs)
    glyf = fb.font["glyf"]
    hm = {}
    for name in order:
        g = glyf[name]
        g.recalcBounds(glyf)
        lsb = getattr(g, "xMin", 0) if g.numberOfContours else 0
        hm[name] = (metrics[name][0], lsb)
    fb.setupHorizontalMetrics(hm)
    fb.setupHorizontalHeader(ascent=1050, descent=-360)
    fb.setupNameTable({
        "familyName": "Katip",
        "styleName": "Regular",
        "uniqueFontIdentifier": "Katip-Regular;VowelShift",
        "fullName": "Katip Regular",
        "psName": "Katip-Regular",
        "version": "Version 1.000",
        "copyright": "Copyright 2015-2021 The Aref Ruqaa Project Authors "
                     "(https://github.com/alif-type/aref-ruqaa). Katip derivative 2026 VowelShift.",
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1.",
        "licenseInfoURL": "https://openfontlicense.org",
    })
    fb.setupOS2(sTypoAscender=1050, sTypoDescender=-360, sTypoLineGap=80,
                usWinAscent=1150, usWinDescent=420, sxHeight=XH + 20, sCapHeight=CAP + 20,
                achVendID="VWSH", fsType=0, yStrikeoutSize=46, yStrikeoutPosition=250)
    fb.setupPost(underlinePosition=-110, underlineThickness=46)
    fb.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} with {len(order)} glyphs")


if __name__ == "__main__":
    build()
