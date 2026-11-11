"""Rule tiles and their tray, and the small marks: the sentence stop, the seal.

A tile keeps the look of the age that made it. The rules of the first era
are cut in stone-coloured clay and filled with red; those of the second are
İznik, cobalt and tulips under a white glaze; the third's are a country
potter's; the fourth's are printed in pastel, with a bevel that takes the light.
"""
import math

import numpy as np

import motif as m
from motif import C, PI, almond, gul, lale, rose, yildiz
from nakkas import LINE, bez, brush, d_of, disc, el, fill, lobed, ribbon, ring, rrect, stroke, xf, arc


def tile_frame(w=150, h=200):
    e = m.era()
    yy = 108.5
    if e == 1:
        out = rrect(0, 0, w, h, C["glaze"], LINE, r=3)
        out += rrect(8, 8, w - 16, h - 16, None, 4.4, r=1, lc=C["red"], role="ink")
        out += rrect(12.6, 12.6, w - 25.2, h - 25.2, None, 0.8, role="ink")
        for cx, cy in ((8, 8), (w - 8, 8), (8, h - 8), (w - 8, h - 8)):
            out += rrect(cx - 6, cy - 6, 12, 12, C["lapis_dk"], 0.8) + disc(cx, cy, 1.8, C["paper"], 0)
        for dx, r, col in ((0, 3.6, C["red"]), (-12, 2.5, C["ink"]), (12, 2.5, C["ink"]), (-22, 1.7, C["red"]), (22, 1.7, C["red"])):
            out += fill([(w / 2 + dx - r, yy), (w / 2 + dx, yy - r), (w / 2 + dx + r, yy), (w / 2 + dx, yy + r)], col, 0)
        return out
    if e == 4:
        out = rrect(0, 0, w, h, C["glaze"], LINE, r=5)
        out += fill([(0, h - 5), (5, h), (w - 5, h), (w, h - 5), (w, 6), (w - 7, 12), (w - 7, h - 7), (7, h - 7)], C["paper2"], 0)   # bevel in shade
        out += fill([(0, 6), (5, 0), (w - 6, 0), (w - 7, 7), (7, 7), (7, h - 7), (0, h - 6)], "#fffdf8", 0)                          # bevel in light
        out += rrect(0, 0, w, h, None, LINE, r=5, role="ink")
        out += rrect(11, 11, w - 22, h - 22, None, 1.3, lc=C["lapis_dk"], role="ink") + rrect(14.5, 14.5, w - 29, h - 29, None, 0.6, lc=C["lapis"], role="ink")
        for sx, sy, cx, cy in ((1, 1, 19, 19), (-1, 1, w - 19, 19), (1, -1, 19, h - 19), (-1, -1, w - 19, h - 19)):
            for ang in ((0.0 if sx > 0 else PI), (PI / 2 if sy > 0 else -PI / 2)):
                out += fill(xf(almond(11, 4.2, k=0.5), cx, cy, ang), C["lapis"], 0)
            out += rose(cx, cy, 4.4, None, 0.6)
        out += brush([(w / 2 - 40, yy), (w / 2, yy), (w / 2 + 40, yy)], 1.4, C["lapis_dk"], (0.5, 0.5), wmin=0.2)
        out += fill(arc(w / 2, yy, 4.2, 0, 2 * PI, 14, ry=2.8), C["red"], 0.6)
        return out
    naive = e == 3
    out = rrect(0, 0, w, h, C["glaze"], LINE, r=7)
    out += rrect(7.5, 7.5, w - 15, h - 15, None, 4.0 if naive else 3.2, r=4, lc=C["lapis"], role="ink")
    if not naive:
        out += rrect(11.2, 11.2, w - 22.4, h - 22.4, None, 0.7, r=2.5, role="ink")
    for x, y, a in ((14, 14, PI / 4), (w - 14, 14, 3 * PI / 4), (14, h - 14, -PI / 4), (w - 14, h - 14, -3 * PI / 4)):
        if naive:
            out += disc(x + 2.5 * math.cos(a), y + 2.5 * math.sin(a), 4.6, C["red"], 0.8)
        else:
            out += lale(x, y, a, 0.62, C["red"], 0.8)
    for sg in (-1, 1):
        out += brush([(w / 2 + sg * 9, yy), (w / 2 + sg * 22, yy + (1.5 if naive else 0)), (w / 2 + sg * 38, yy)], 1.4, C["lapis"], (0.0, 0.8), wmin=0.3)
    out += fill([(w / 2 - 5, yy), (w / 2, yy - 3.4), (w / 2 + 5, yy), (w / 2, yy + 3.4)], C["red"], 0.7)
    return out


def _cob(pts, w, taper=(0.1, 0.1), wmin=0.5):
    """A stroke of colour under the glaze."""
    rb = ribbon(pts, w, taper, wmin, 0.07, 5)
    return [el("path", "paint", fill=C["lapis"], d=d_of(rb)), el("path", "ink", stroke=C["lapis_dk"], sw=0.9, d=d_of(rb))]


def _drop(x, y, r, a=PI / 2):
    """A falling drop: thin where it left, round where it leads."""
    d = d_of(xf(almond(3.2 * r, 2 * r, k=0.7, n=15), x, y, a))
    return [el("path", "paint", fill=C["lapis"], d=d), el("path", "ink", stroke=C["lapis_dk"], sw=0.9, d=d)]


RULE_ERA = {"R1": 1, "R2": 1, "R3": 2, "R4": 2, "R5": 3, "R6": 3, "R7": 4, "R8": 4}


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
    e = m.era()
    out = rrect(0, 0, w, h, C["red"], LINE, r=3 if e == 1 else 9)
    out += rrect(4.5, 4.5, w - 9, h - 9, None, 1.1, r=2 if e == 1 else 6, lc=C["red_pale"], role="paint")
    for k in range(n):
        x = 12 + k * slot_w + 3
        cx, cy = x + (slot_w - 6) / 2, 12 + slot_h / 2
        out += rrect(x, 12, slot_w - 6, slot_h, C["red_deep"], 1.4, r=2 if e == 1 else 5)
        if e == 4:
            out += fill([(x, 12), (x + slot_w - 6, 12), (x + slot_w - 6, 19), (x + 7, 19), (x + 7, 12 + slot_h), (x, 12 + slot_h)], "#3a1b12", 0)    # the well's own shadow
        out += rrect(x + 9, 21, slot_w - 24, slot_h - 18, None, 1.0, r=4, lc=C["wood"], role="paint")
        if e == 1:
            out += stroke(yildiz(cx, cy, 30, PI / 8), 1.0, C["wood"], "paint", closed=True, join="miter") + stroke(yildiz(cx, cy, 13, 0), 1.0, C["wood"], "paint", closed=True, join="miter")
        else:
            out += stroke(lobed(cx, cy, 30, 8, 0.16), 1.0, C["wood"], "paint", closed=True) + stroke(lobed(cx, cy, 12, 8, 0.2), 1.0, C["wood"], "paint", closed=True)
        px = cx - (k * 7) / 2
        for j in range(k + 1):
            out += disc(px + j * 7, h - 6.2, 1.9, C["red_pale"], 0)
        if k:
            out += fill([(x - 6.2, 6.2 - 3.4), (x - 0.4, 6.2), (x - 6.2, 6.2 + 3.4)], C["red_pale"], 0)
    return out, w, h


def durak(cx=14.0, cy=14.0, r=12.0):
    """The sentence stop, and the mark beside whatever the hand is over."""
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
