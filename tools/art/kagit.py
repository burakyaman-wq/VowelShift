"""Paper: the document to be copied, the sheet it is copied onto, the
requester's slip and the scribe's notebook.

The document is drawn once per school, because it is the thing each age
decorated its own way:
  I   a heavy red rule, the title in a tablet with ears, knots in the corners
  II  a lapis rule between hairs, a pointed cartouche with sprigs, corner pieces
  III the second, patched and mended
  IV  an engraved double rule, the title on a ribbon, roses in the corners
In the reading view each shows its full illumination.
"""
import math

import numpy as np

import motif as m
from motif import C, PI, almond, celenk, gecme, gul, kartus, kosebent, rose, sheet, tig, yanik, yildiz, zencerek
from nakkas import G, LINE, arc, bez, brush, disc, el, fill, lobed, place, rrect, stroke, xf


def cetvel(x, y, w, h, col=None, sw=3.0):
    """The ruled frame of a page: a coloured line between two hairs."""
    out = rrect(x, y, w, h, None, sw, lc=col or C["lapis"], role="ink")
    out += rrect(x - sw * 0.8, y - sw * 0.8, w + sw * 1.6, h + sw * 1.6, None, 0.7, role="ink")
    out += rrect(x + sw * 0.8, y + sw * 0.8, w - sw * 1.6, h - sw * 1.6, None, 0.7, role="ink")
    return out


def baslik(cx, cy, cw, ch, reach):
    """Second era: the title cartouche, with a sprig running out each side:
    two leaves, a rosette, a bud."""
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


def _bands(make, pw, ph, m0, band):
    b2 = band / 2
    return [G("kenar_ust", make(pw - 2 * m0 - 2 * band), place(m0 + band, m0 + b2)),
            G("kenar_alt", make(pw - 2 * m0 - 2 * band), place(m0 + band, ph - m0 - b2)),
            G("kenar_sol", make(ph - 2 * m0 - 2 * band), place(m0 + b2, m0 + band, 90)),
            G("kenar_sag", make(ph - 2 * m0 - 2 * band), place(pw - m0 - b2, m0 + band, 90))]


def _yama(x, y, w, h, a, seed):
    """A mend: a slip of other paper pasted over a hole, its edge still showing."""
    g = np.random.default_rng(seed)
    pts = [(0, 0), (w, g.uniform(-2, 2)), (w + g.uniform(-3, 3), h), (g.uniform(-2, 2), h + g.uniform(-2, 2))]
    return [G("yama", fill(pts, C["paper2"], 1.0) + stroke([(4, 4), (w - 5, 5)], 0.7, C["paper3"], "paint"), place(x, y, a))]


def _doc1(w, h, grand, seed):
    out = fill(sheet(w, h, seed, 1.4), C["paper"])
    mg = 26
    if grand:
        for x in np.arange(mg + 12, w - mg - 6, 12.0):
            out += fill([(x - 4.2, mg - 4), (x, mg - 10), (x + 4.2, mg - 4)], C["red"], 0) + fill([(x - 4.2, h - mg + 4), (x, h - mg + 10), (x + 4.2, h - mg + 4)], C["red"], 0)
        for y in np.arange(mg + 12, h - mg - 6, 12.0):
            out += fill([(mg - 4, y - 4.2), (mg - 10, y), (mg - 4, y + 4.2)], C["red"], 0) + fill([(w - mg + 4, y - 4.2), (w - mg + 10, y), (w - mg + 4, y + 4.2)], C["red"], 0)
        band = 22
        out += rrect(mg, mg, w - 2 * mg, h - 2 * mg, C["paper2"], 0)
        out += rrect(mg + band, mg + band, w - 2 * mg - 2 * band, h - 2 * mg - 2 * band, C["paper"], 1.0)
        out += _bands(lambda n: gecme(n, 11.0, 40.0, 3.0), w, h, mg, band)
        for cx, cy in ((mg + 11, mg + 11), (w - mg - 11, mg + 11), (mg + 11, h - mg - 11), (w - mg - 11, h - mg - 11)):
            out += rrect(cx - 11, cy - 11, 22, 22, C["red"], 0.9) + fill(yildiz(cx, cy, 8.5, PI / 8), C["paper"], 0.7)
        inner, ks, cw = mg + band + 7, 34.0, 336
    else:
        inner, ks, cw = mg + 9, 21.0, 316
    out += cetvel(mg, mg, w - 2 * mg, h - 2 * mg, C["red"], 4.0)
    out += rrect(inner, inner, w - 2 * inner, h - 2 * inner, None, 1.2, role="ink")
    for sx, sy, x, y in ((1, 1, inner, inner), (-1, 1, w - inner, inner), (1, -1, inner, h - inner), (-1, -1, w - inner, h - inner)):
        cx, cy = x + sx * ks / 2, y + sy * ks / 2
        out += rrect(min(x, x + sx * ks), min(y, y + sy * ks), ks, ks, C["red"], 1.0)
        out += fill(yildiz(cx, cy, ks * 0.38, PI / 8), C["paper"], 0.8) + disc(cx, cy, ks * 0.1, C["lapis"], 0)
    cx, cy, x0, x1 = w / 2, 70.0, w / 2 - cw / 2, w / 2 + cw / 2
    panel = [(x0 + 22, cy - 22), (x1 - 22, cy - 22), (x1 - 22, cy - 9), (x1, cy), (x1 - 22, cy + 9), (x1 - 22, cy + 22),
             (x0 + 22, cy + 22), (x0 + 22, cy + 9), (x0, cy), (x0 + 22, cy - 9)]
    out += fill(panel, C["red"], 1.6)
    out += rrect(x0 + 28, cy - 17, cw - 56, 34, None, 0.9, lc=C["red_pale"], role="paint")
    for sg in (-1, 1):
        for j in range(3):
            xx, r = (x1 if sg > 0 else x0) + sg * (12 + 13 * j), 4.2 - j * 0.9
            out += fill([(xx - r, cy), (xx, cy - r), (xx + r, cy), (xx, cy + r)], C["red"] if j % 2 == 0 else C["ink"], 0)
    return out


def _doc2(w, h, grand, seed):
    out = fill(sheet(w, h, seed), C["paper"])
    mg = 26
    naive = m.era() == 3
    if naive:
        out += _yama(w - 196, h - 60, 150, 48, -2.5, seed) + _yama(w - 62, h * 0.36, 52, 88, 2, seed + 1)
    if grand:
        for x in np.arange(mg + 30, w - mg - 20, 34.0):
            for yy, a in ((mg - 3, -PI / 2), (h - mg + 3, PI / 2)):
                out += tig(x, yy, a, 8 if int(x / 34) % 2 else 13, C["lapis"], dot=int(x / 34) % 2 == 0)
        for y in np.arange(mg + 30, h - mg - 20, 34.0):
            for xx, a in ((mg - 3, PI), (w - mg + 3, 0)):
                out += tig(xx, y, a, 8 if int(y / 34) % 2 else 13, C["lapis"], dot=int(y / 34) % 2 == 0)
        band = 20
        out += rrect(mg, mg, w - 2 * mg, h - 2 * mg, C["lapis"], 0)
        out += rrect(mg + band, mg + band, w - 2 * mg - 2 * band, h - 2 * mg - 2 * band, C["paper"], 0.9)
        out += _bands(zencerek, w, h, mg, band)
        for cx, cy in ((mg + 10, mg + 10), (w - mg - 10, mg + 10), (mg + 10, h - mg - 10), (w - mg - 10, h - mg - 10)):
            out += gul(cx, cy, 7.2, 8, C["paper"], C["red"], 0.6)
        out += cetvel(mg, mg, w - 2 * mg, h - 2 * mg)
        inner, ks, cw, reach = mg + band + 6, 40.0, 330, 120
    else:
        out += cetvel(mg, mg, w - 2 * mg, h - 2 * mg)
        inner, ks, cw, reach = mg + 7, 25.0, 312, 62
    out += rrect(inner, inner, w - 2 * inner, h - 2 * inner, None, 1.0, lc=C["red"], role="ink")
    for sx, sy, x, y in ((1, 1, inner, inner), (-1, 1, w - inner, inner), (1, -1, inner, h - inner), (-1, -1, w - inner, h - inner)):
        out += kosebent(x, y, sx, sy, ks)
    out += baslik(w / 2, 70, cw, 44, reach)
    return out


def _ribbon(cx, cy, cw, ch):
    """Fourth era: the title on a ribbon, its ends folded back and forked."""
    out = []
    for sg in (-1, 1):
        x0 = cx + sg * (cw / 2 - 30)
        tail = [(x0, cy - ch / 2 + 9), (x0 + sg * 46, cy - ch / 2 + 9), (x0 + sg * 34, cy + 2), (x0 + sg * 46, cy + ch / 2 + 4), (x0, cy + ch / 2 + 4)]
        out += fill(tail, C["lapis"], 1.0)
        out += fill([(x0, cy + ch / 2 - 5), (x0 + sg * 16, cy + ch / 2 - 5), (x0, cy + ch / 2 + 4)], C["lapis_dk"], 0.8)     # the fold, in shade
    t = np.linspace(-1, 1, 21)
    top = np.stack([cx + t * (cw / 2 - 16), cy - ch / 2 - 2.5 * (1 - t * t)], 1)
    bot = np.stack([cx + t * (cw / 2 - 16), cy + ch / 2 - 5 - 2.5 * (1 - t * t)], 1)
    out += fill(np.vstack([top, bot[::-1]]), C["lapis_dk"], 1.2)
    out += stroke(top + [0, 3.5], 0.9, C["lapis_lt"], "paint")
    return out


def _doc4(w, h, grand, seed):
    out = fill(sheet(w, h, seed, 0.4), C["paper"])
    mg = 26
    out += rrect(mg, mg, w - 2 * mg, h - 2 * mg, None, 1.4, role="ink") + rrect(mg + 5, mg + 5, w - 2 * mg - 10, h - 2 * mg - 10, None, 0.7, role="ink")
    inner = mg + 5
    if grand:
        side = w / 2 - 250 - mg - 70
        out.append(G("celenk_sol", celenk(side, 170.0, 7.0), place(mg + 70, mg + 26)))
        out.append(G("celenk_sag", celenk(side, 170.0, 7.0), place(w / 2 + 250, mg + 26)))
        out.append(G("celenk_alt", celenk(w - 2 * mg - 200, 170.0, 7.0), place(mg + 100, h - mg - 30)))
    ks = 30.0 if grand else 19.0
    for sx, sy, x, y in ((1, 1, inner, inner), (-1, 1, w - inner, inner), (1, -1, inner, h - inner), (-1, -1, w - inner, h - inner)):
        cx, cy = x + sx * ks * 0.55, y + sy * ks * 0.55
        for ang in ((0.0 if sx > 0 else PI), (PI / 2 if sy > 0 else -PI / 2)):
            out += fill(xf(almond(ks * 0.95, ks * 0.34, k=0.5), cx, cy, ang), C["lapis"], 0.7)
        out += brush(bez((cx, cy), (cx + sx * ks * 0.2, cy + sy * ks * 0.9), (cx + sx * ks * 0.9, cy + sy * ks * 1.2), (cx + sx * ks * 1.5, cy + sy * ks * 0.7), 10),
                     1.3, C["lapis_dk"], (0.0, 0.7), wmin=0.3)
        out += rose(cx, cy, ks * 0.3)
    out += _ribbon(w / 2, 70, 360 if grand else 340, 44)
    return out


def document_page(w, h, grand=False, seed=3):
    """Text first. On the desk: a ruled frame, a small title, corner pieces.
    In the reading view the same page shows its full illumination."""
    return {1: _doc1, 2: _doc2, 3: _doc2, 4: _doc4}[m.era()](w, h, grand, seed)


def copy_sheet(w=420, h=500):
    """New paper, blind-ruled with the mıstar; nothing else. The scribe's own work."""
    out = fill(sheet(w, h, 8, 0.6), C["fresh"])
    for i in range(6):
        yy = 96 + i * 70
        out += stroke([(30, yy), (w - 30, yy + 0.6)], 0.9, C["paper"], "paint")
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
    leaves, the sewing in the gutter, headbands, a ribbon. In the third era
    it is the half that came out of the fire."""
    out = rrect(-16, -16, w + 32, h + 32, C["red"], LINE, r=8)
    out += rrect(-11, -11, w + 22, h + 22, None, 1.3, r=5, lc=C["red_dk"], role="paint")
    for cx, cy in ((-9, -9), (w + 9, -9), (-9, h + 9), (w + 9, h + 9)):
        out += disc(cx, cy, 2.2, C["red_pale"], 0)
    for i in (3, 2, 1):
        out += rrect(-2.6 * i, 1.5 * i, w / 2 + 2.6 * i, h - 0.5 * i, C["paper2"], 0.8)
        out += rrect(w / 2, 1.5 * i, w / 2 + 2.6 * i, h - 0.5 * i, C["paper2"], 0.8)
    out += rrect(0, 0, w / 2, h, C["paper"], 1.2) + rrect(w / 2, 0, w / 2, h, C["paper"], 1.2)
    rule = "#e2d0a8" if m.era() != 3 else C["paper2"]
    for k in range(12):
        yy = 69 + 27 * k
        out += stroke([(20, yy), (w / 2 - 16, yy)], 0.8, rule, "paint") + stroke([(w / 2 + 18, yy), (w - 18, yy)], 0.8, rule, "paint")
    for dx in (-7, 7):
        out += stroke([(w / 2 + dx, 2), (w / 2 + dx * 0.8, h / 2), (w / 2 + dx, h - 2)], 0.8, C["paper2"], "paint")
    out += stroke([(w / 2, 0), (w / 2, h)], 1.8)
    for yy in (58, 160, 262, 364):
        out += stroke([(w / 2 - 5, yy), (w / 2 + 5, yy)], 2.6, cap="butt") + stroke([(w / 2 - 4.4, yy), (w / 2 + 4.4, yy)], 1.4, C["glaze"], "paint", cap="butt")
    for yy, sg in ((-1, -1), (h + 1, 1)):
        out += rrect(w / 2 - 24, min(yy, yy + sg * 8), 48, 8, C["paper"], 0.9, r=2)
        for k in range(8):
            x0 = w / 2 - 24 + k * 6
            out += fill([(x0 + 0.6, yy), (x0 + 3.6, yy), (x0 + 5.6, yy + sg * 8), (x0 + 2.6, yy + sg * 8)], (C["red"], C["lapis"])[k % 2], 0)
    out += fill([(w / 2 + 4, h - 8), (w / 2 + 11, h - 8), (w / 2 + 12, h + 18), (w / 2 + 8, h + 13), (w / 2 + 4.5, h + 19)], C["lapis"], 1.0)
    if m.era() == 3:                                  # the fire took the corners and browned the edges
        burnt = ("#3a1a10", "#1c0c07")
        out += yanik(w + 4, -6, 62, 46, 31, burnt) + yanik(w + 8, h * 0.56, 22, 70, 32, burnt) + yanik(-8, h + 6, 54, 30, 33, burnt) + yanik(w * 0.8, h + 12, 70, 16, 34, burnt)
    return out
