"""The desk plate of each era: the ground it stands on, the board itself, and
the scribe's things that never leave it. One function per thing; where the
schools differ, the thing has one drawing per school.

  I   Selçuklu      a braid for a border, a clay lamp under a star of light,
                    reeds on a rest, a stone inkwell, a knife, a rule
  II  Klasik        a running vine, a glazed lamp under a medallion of light,
                    lacquer pen case, two inkwells, scissors, burnisher, sand
  III Taşra         what the fire left: scorched boards, a patch, a burnt case
  IV  Batılılaşma   a moulded frame with garlands, a glass lamp that casts
                    real light, a quill, a watch, spectacles, and shadows
"""
import copy
import math

import numpy as np

import motif as m
from motif import (C, H, PI, W, almond, cintemani, celenk, flame_tongue, gecme, gul, kartus, kivrik_dal,
                   kivrik_dal_tasra, penc, rose, rumi, tig, yanik, yildiz)
from nakkas import G, LINE, arc, bez, brush, disc, el, fill, holed, lobed, oval, place, ring, rrect, spline, stroke, xf

X0, Y0, X1, Y1 = 58, 52, W - 58, H - 52          # the board


# ================================================================ the ground under the desk
def _bands(make, length_h, length_v):
    return [G("bordur_ust", make(length_h), place(39, 25)), G("bordur_alt", make(length_h), place(W - 39, H - 25, 180)),
            G("bordur_sol", make(length_v), place(25, H - 39, -90)), G("bordur_sag", make(length_v), place(W - 25, 39, 90))]


def carpet():
    """What shows of the floor carpet round the desk: guard stripes and a
    lapis border with a running vine, a rosette in each corner."""
    naive = m.era() == 3
    out = rrect(0, 0, W, H, C["red_dk"], 0)
    out += rrect(4, 4, W - 8, H - 8, C["paper"], 1.2)
    step = 13.0 if naive else 9.0
    for x in np.arange(13.0, W - 8, step):
        out += disc(x, 7.5, 2.0 if naive else 1.5, C["red"], 0) + disc(x, H - 7.5, 2.0 if naive else 1.5, C["red"], 0)
    for y in np.arange(13.0, H - 8, step):
        out += disc(7.5, y, 2.0 if naive else 1.5, C["red"], 0) + disc(W - 7.5, y, 2.0 if naive else 1.5, C["red"], 0)
    out += rrect(11, 11, W - 22, H - 22, C["lapis"], 1.2)
    out += _bands(kivrik_dal_tasra if naive else kivrik_dal, W - 78, H - 78)
    for cx, cy in ((25, 25), (W - 25, 25), (25, H - 25), (W - 25, H - 25)):
        out += rrect(cx - 14, cy - 14, 28, 28, C["lapis_dk"], 1.0)
        if not naive:
            out += rrect(cx - 11, cy - 11, 22, 22, None, 0.8, lc=C["lapis_lt"])
        out += penc(cx, cy, 9.5, 6 if naive else 8, C["red"], C["paper"], 0.7)
    out += rrect(39, 39, W - 78, H - 78, C["red"], 1.2)
    return out


def kilim():
    """First era: a flat-woven border. A braid of two reds on bare ground,
    a star in each corner, a row of small squares for a guard."""
    out = rrect(0, 0, W, H, C["red_dk"], 0)
    out += rrect(4, 4, W - 8, H - 8, C["red"], 1.2)
    for x in np.arange(13.0, W - 8, 10.0):
        out += rrect(x - 1.7, 5.8, 3.4, 3.4, C["paper"], 0) + rrect(x - 1.7, H - 9.2, 3.4, 3.4, C["paper"], 0)
    for y in np.arange(13.0, H - 8, 10.0):
        out += rrect(5.8, y - 1.7, 3.4, 3.4, C["paper"], 0) + rrect(W - 9.2, y - 1.7, 3.4, 3.4, C["paper"], 0)
    out += rrect(11, 11, W - 22, H - 22, C["paper"], 1.2)
    out += _bands(gecme, W - 78, H - 78)
    for cx, cy in ((25, 25), (W - 25, 25), (25, H - 25), (W - 25, H - 25)):
        out += rrect(cx - 14, cy - 14, 28, 28, C["red"], 1.0)
        out += fill(yildiz(cx, cy, 11.5, PI / 8), C["paper"], 0.8) + disc(cx, cy, 3.2, C["red"], 0.7)
    out += rrect(39, 39, W - 78, H - 78, C["red"], 1.2)
    return out


def cerceve():
    """Fourth era: no carpet but a moulded frame, lit from the upper left,
    hung with garlands; a rose at each corner."""
    o, ix, iy = 5, 50, 44
    out = rrect(0, 0, W, H, C["wood_dk"], 0)
    out += fill([(o, o), (W - o, o), (W - ix, iy), (ix, iy)], C["glaze"], 1.0)                     # top, in the light
    out += fill([(o, o), (ix, iy), (ix, H - iy), (o, H - o)], C["paper"], 1.0)                     # left
    out += fill([(W - o, o), (W - o, H - o), (W - ix, H - iy), (W - ix, iy)], C["paper2"], 1.0)    # right, turning away
    out += fill([(o, H - o), (ix, H - iy), (W - ix, H - iy), (W - o, H - o)], C["paper3"], 1.0)    # bottom, in shade
    out += rrect(12, 11, W - 24, H - 22, None, 0.8, lc=C["paper3"], role="paint")
    out.append(G("celenk_ust", celenk(W - 190), place(95, 25)))
    out.append(G("celenk_alt", celenk(W - 190), place(95, H - 27)))
    out.append(G("celenk_sol", celenk(H - 190, 160), place(27, H - 95, -90)))
    out.append(G("celenk_sag", celenk(H - 190, 160), place(W - 27, 95, 90)))
    for cx, cy in ((30, 27), (W - 30, 27), (30, H - 27), (W - 30, H - 27)):
        for a in (0.4, 1.9, 3.5, 5.1):
            out += fill(xf(almond(15, 7, k=0.5), cx, cy, a), C["lapis"], 0.7)
        out += rose(cx, cy, 8.5)
    out += rrect(ix - 6, iy - 6, W - 2 * ix + 12, H - 2 * iy + 12, C["red_deep"], 1.0)
    return out


# ================================================================ the board
def desk(boards=4, seed=11, knots=((980, 694, 30), (188, 910, 24))):
    """Plain dark wood: boards, a quiet grain that parts round the knots.
    The second era lets a hair of bone into the edge; the first pegs its
    boards and cuts a star in each corner; the third has rough, unequal planks."""
    e = m.era()
    g = np.random.default_rng(seed)
    out = {1: kilim, 2: carpet, 3: carpet, 4: cerceve}[e]()
    out += rrect(X0 - 8, Y0 - 8, X1 - X0 + 16, Y1 - Y0 + 16, C["red_deep"], LINE, r=4 if e == 1 else 11)
    out += rrect(X0, Y0, X1 - X0, Y1 - Y0, C["wood"], LINE, r=2 if e == 1 else 6)
    cuts = np.linspace(Y0, Y1, boards + 1)
    if e == 3:
        cuts[1:-1] += g.uniform(-34, 34, boards - 1)
    grain = []
    for bi in range(boards):
        top, bh = cuts[bi], cuts[bi + 1] - cuts[bi]
        for _ in range(int(bh / 24)):
            yb = top + g.uniform(7, bh - 7)
            xa = g.uniform(X0 + 6, X1 - 420)
            xb = min(xa + g.uniform(280, 980), X1 - 6)
            xs = np.linspace(xa, xb, int((xb - xa) / 14) + 2)
            ph, am, wl = g.uniform(0, 6.28), g.uniform(1.0, 3.4), g.uniform(260, 620)
            ys = yb + am * np.sin(xs / wl * 2 * PI + ph)
            for kx, ky, kr in knots:
                ys = ys + np.exp(-((xs - kx) / (kr * 2.6)) ** 2) * np.sign(yb - ky) * kr * 1.15 * math.exp(-abs(yb - ky) / (kr * 1.5))
            ys = np.clip(ys, top + 3, top + bh - 3)
            col = C["wood_lt"] if g.uniform() < 0.28 else C["wood_dk"]
            grain += brush(np.stack([xs, ys], 1), g.uniform(1.3, 2.5) * (1.3 if e == 3 else 1.0), col, (0.45, 0.45), "paint", breath=0.25, seed=int(g.integers(1 << 30)))
    for kx, ky, kr in knots:
        for f in (1.0, 0.68, 0.38):
            grain += [el("ellipse", "paint", stroke=C["wood_dk"], sw=1.5, cx=f"{kx}", cy=f"{ky}", rx=f"{kr * f:.1f}", ry=f"{kr * f * 0.46:.1f}")]
        grain += [el("ellipse", "paint", fill=C["wood_dk"], cx=f"{kx}", cy=f"{ky}", rx=f"{kr * 0.16:.1f}", ry=f"{kr * 0.08:.1f}")]
    out.append(G("damar", grain))
    for bi in range(1, boards):
        xs = np.linspace(X0 + 1, X1 - 1, 60)
        out += brush(np.stack([xs, cuts[bi] + 0.8 * np.sin(xs / 190.0 + bi)], 1), 3.6 if e == 3 else 2.4, C["red_deep"], (0.02, 0.02), "paint", wmin=0.8, breath=0.18, seed=bi)
    if e in (1, 3):                                   # pegs, or nails, at the ends of every board
        for bi in range(boards):
            cy = (cuts[bi] + cuts[bi + 1]) / 2
            for px in (X0 + 16, X1 - 16):
                for dy in (-0.28, 0.28):
                    out += disc(px, cy + dy * (cuts[bi + 1] - cuts[bi]), 3.2 if e == 1 else 2.4, C["wood_dk"] if e == 1 else C["char"], 0.8)
    if e == 1:
        for cx, cy in ((X0 + 44, Y0 + 40), (X1 - 44, Y0 + 40), (X0 + 44, Y1 - 40), (X1 - 44, Y1 - 40)):
            out += stroke(yildiz(cx, cy, 15, PI / 8), 1.5, C["paper3"], "paint", closed=True, join="miter")
            out += stroke(yildiz(cx, cy, 7, 0), 1.2, C["paper3"], "paint", closed=True, join="miter")
    if e == 2:
        k = 13
        out += rrect(X0 + k, Y0 + k, X1 - X0 - 2 * k, Y1 - Y0 - 2 * k, None, 1.5, r=3, lc=C["paper3"], role="paint")
        for cx, cy in ((X0 + k, Y0 + k), (X1 - k, Y0 + k), (X0 + k, Y1 - k), (X1 - k, Y1 - k)):
            out += fill(lobed(cx, cy, 7.5, 4, 0.3, phase=PI / 4), C["paper3"], 0.8) + disc(cx, cy, 2.0, C["wood"], 0)
    if e == 4:
        k = 10
        out += rrect(X0 + k, Y0 + k, X1 - X0 - 2 * k, Y1 - Y0 - 2 * k, None, 2.2, r=2, lc=C["wood_lt"], role="paint")
        out += rrect(X0 + k + 2.4, Y0 + k + 2.4, X1 - X0 - 2 * k - 4.8, Y1 - Y0 - 2 * k - 4.8, None, 1.0, r=2, lc=C["wood_dk"], role="paint")
    return G("masa", out)


# ================================================================ lamps and their light
def kandil_isigi(r=62):
    """The lamp's light is a drawn thing: a pale medallion, the illuminator's
    needles round it for rays, and a plume of flame tongues rising in it."""
    naive = m.era() == 3
    lobes = 8 if naive else 12
    cy = -r * 0.22
    out = []
    for k in range(lobes * 2):
        a = 2 * PI * k / (lobes * 2) + PI / (lobes * 2)
        if naive and k % 2:
            continue
        out += tig(r * 1.06 * math.cos(a), cy + r * 1.06 * math.sin(a), a, 9 if k % 2 else 15, C["red"], dot=(k % 2 == 0))
    out += fill(lobed(0, cy, r * 1.04, lobes, 0.10), C["light"], 1.2, C["red"])
    out += fill(lobed(0, cy, r * 0.80, lobes, 0.10), C["light2"], 0.8, C["red_lt"])
    by = r * 0.16
    for k, a in enumerate(np.linspace(-PI / 2 - 0.95, -PI / 2 + 0.95, 5 if naive else 7)):
        ln = r * (0.98 - 0.36 * abs(a + PI / 2)) * (0.92 if k % 2 else 1.04)
        out += flame_tongue(0, by, a, ln, r * (0.19 if naive else 0.15), C["red"] if k % 2 == 0 else C["red_lt"], 1.0, 0.24 if a <= -PI / 2 else -0.24)
    for a in np.linspace(-PI / 2 - 0.42, -PI / 2 + 0.42, 3):
        out += flame_tongue(0, by - 1, a, r * 0.5, r * 0.105, C["glaze"], 0.9, 0.2 if a < -PI / 2 else -0.2)
    return out


def yildiz_isigi(r=62):
    """First era: the light is a star of two squares, a short ray in each notch,
    three plain tongues of flame."""
    cy = -r * 0.22
    out = []
    for k in range(8):
        a = k * PI / 4
        out += brush([(r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a)), (r * 1.28 * math.cos(a), cy + r * 1.28 * math.sin(a))], 3.4, C["red"], (0.0, 0.7), wmin=0.3)
    out += fill(yildiz(0, cy, r * 1.1, PI / 8), C["light"], 1.4, C["red"])
    out += fill(yildiz(0, cy, r * 0.8, 0), C["light2"], 0.9, C["red_lt"])
    by = r * 0.16
    for a, ln, col in ((-PI / 2 - 0.55, 0.62, C["red_lt"]), (-PI / 2 + 0.55, 0.62, C["red_lt"]), (-PI / 2, 0.95, C["red"])):
        out += flame_tongue(0, by, a, r * ln, r * 0.2, col, 1.0, 0.0)
    out += flame_tongue(0, by - 1, -PI / 2, r * 0.45, r * 0.11, C["glaze"], 0.9, 0.0)
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


def canak_kandil():
    """First era: a lamp of fired clay, a bowl pinched to a spout, a lug to hold it by."""
    out = rrect(-56, -9, 20, 18, C["red_lt"], LINE, r=4)
    body = [(-40, 0), (-32, -27), (-4, -38), (26, -31), (50, -15), (76, -5), (81, 0), (76, 5), (50, 15), (26, 31), (-4, 38), (-32, 27)]
    out += fill(spline(body, 6, closed=True), C["red_lt"])
    zig = [((31.5 if k % 2 else 35.5) * math.cos(a) - 4, (31.5 if k % 2 else 35.5) * math.sin(a)) for k, a in enumerate(np.linspace(0.75, 2 * PI - 0.75, 31))]
    out += stroke(zig, 0.9, join="miter")
    out += disc(-4, 0, 25, C["red_dk"], LINE) + disc(-4, 0, 17, C["red_deep"], 0)
    out += disc(74, 0, 4.2, C["ink"], 0.8)
    return out


def lamba():
    """Fourth era: a lamp with a glass chimney, seen from above. Its light is
    no longer drawn; it falls on the desk (see `isik` in the export)."""
    out = disc(0, 0, 46, C["paper3"], LINE)                                  # brass foot
    out += ring(0, 0, 39, 1.0, C["paper2"], "paint") + ring(0, 0, 41.5, 0.7)
    for k in range(16):
        a = 2 * PI * k / 16
        out += disc(35.5 * math.cos(a), 35.5 * math.sin(a), 1.5, C["wood_lt"], 0)
    out += disc(0, 0, 29, C["lapis_pale"], 1.0)                              # the glass
    out += disc(0, 0, 21, C["light2"], 0.7)
    out += disc(0, 0, 9, C["red_lt"], 0) + disc(0, 0, 5, C["light2"], 0)     # the flame, small and steady
    out += brush(arc(0, 0, 25, PI * 1.05, PI * 1.45, 10), 2.4, C["glaze"], (0.3, 0.3), "paint")   # glint on the glass
    out += rrect(42, -5, 16, 10, C["paper3"], 1.0, r=3) + disc(60, 0, 6.5, C["paper3"], 1.0)      # the wick wheel
    for k in range(8):
        a = 2 * PI * k / 8
        out += stroke([(60 + 4 * math.cos(a), 4 * math.sin(a)), (60 + 6.5 * math.cos(a), 6.5 * math.sin(a))], 0.7)
    return out


# ================================================================ pens and their keeping
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


def tuy(length=250.0):
    """Fourth era: a quill. The barrel is cut to a nib; the vane keeps its curve."""
    t = np.linspace(0, 1, 24)
    spine = np.stack([length * (1 - t), -7 * np.sin(PI * t * 0.9) * t], 1)            # nib at +x, feather curving away
    vane = np.clip(np.sin(PI * np.clip((t - 0.2) / 0.8, 0, 1)) ** 0.7, 0, 1)
    up = spine + np.stack([np.zeros_like(t), -9.5 * vane], 1)
    dn = spine + np.stack([np.zeros_like(t), 6.0 * vane], 1)
    out = fill(np.vstack([up[4:], dn[4:][::-1]]), C["glaze"], 1.0)
    for i in range(6, 23, 2):
        out += stroke([spine[i], up[i] + [5, 0.8]], 0.6, C["paper2"], "paint") + stroke([spine[i], dn[i] + [4, -0.6]], 0.6, C["paper2"], "paint")
    out += brush(spine, 3.4, C["paper2"], (0.0, 0.25), "paint", wmin=0.5) + stroke(spine[:8], 0.8)
    out += fill([(length - 16, -1.8), (length, 0.4), (length - 15, 2.2)], C["ink"], 0)
    return out


def kalemdan():
    """A lacquered pen case with its drawer drawn a little way out."""
    out = rrect(214, 5, 118, 36, C["red_dk"], LINE, r=4)
    out += rrect(222, 9.5, 104, 27, C["wood_dk"], 1.0, r=2)
    for k, yy in enumerate((13.5, 20.5, 27.5)):
        ln = (96, 88, 92)[k]
        out += fill([(224, yy), (224 + ln - 12, yy), (224 + ln, yy + 2.6), (224 + ln - 12, yy + 5.2), (224, yy + 5.2)], C["paper2"], 0.9)
        out += stroke([(250 + 9 * k, yy), (250 + 9 * k, yy + 5.2)], 0.8)
        out += fill([(224 + ln - 7, yy + 1.2), (224 + ln, yy + 2.6), (224 + ln - 7, yy + 4.0)], C["ink"], 0)
    out += disc(335, 23, 4.5, C["lapis"], 1.0)
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


def kalemlik():
    """First era: no case yet. Two reeds across a notched block of wood."""
    out = rrect(40, 4, 152, 34, C["paper3"], LINE, r=2)
    for nx in (54, 168):
        out += rrect(nx, 4, 11, 34, C["wood_lt"], 0.8)
    out += stroke(yildiz(116.5, 21, 10, PI / 8), 1.2, C["wood_lt"], "paint", closed=True, join="miter")
    out.append(G("kamis1", pen(238), place(-8, 13, 2.2)))
    out.append(G("kamis2", pen(222), place(10, 30, -2.0)))
    return out


def hokkalik():
    """Fourth era: a pen tray with a quill laid in it."""
    out = rrect(0, 0, 320, 46, C["red_dk"], LINE, r=8)
    out += rrect(7, 7, 306, 32, C["red_deep"], 1.0, r=5)
    out += stroke([(12, 36), (308, 36)], 1.2, C["red"], "paint")             # the lit lip of the well
    out.append(G("tuy", tuy(270), place(22, 26, -3)))
    return out


# ================================================================ ink
def _lika(x, y, turns, col):
    th = np.linspace(0.4, turns * PI, int(13 * turns))
    return brush(np.stack([x + (1.2 + 2.9 * th / PI) * np.cos(th), y + (1.2 + 2.9 * th / PI) * np.sin(th)], 1), 1.3, col, (0.2, 0.3), "paint")


def hokka(second=True):
    """The inkwells: black ink with its tuft of silk, a smaller pot of red, a lid laid by."""
    out = disc(0, 0, 33, C["glaze"])
    out += ring(0, 0, 25.5, 5.5, C["lapis"], "paint") + ring(0, 0, 28.5, 0.7) + ring(0, 0, 22.5, 0.7)
    for k in range(12):
        a = 2 * PI * k / 12
        out += disc(30.6 * math.cos(a), 30.6 * math.sin(a), 1.4, C["red"], 0)
    out += disc(0, 0, 18, C["ink"], 1.0) + _lika(0, 0, 4.6, "#56423a")
    if second:
        rx, ry = 64, -36
        out += disc(rx, ry, 21, C["glaze"]) + ring(rx, ry, 16.5, 2.6, C["lapis"], "paint") + ring(rx, ry, 18.4, 0.7)
        out += disc(rx, ry, 12.5, C["red"], 1.0)
        th = np.linspace(0.6, 3.2 * PI, 36)
        out += brush(np.stack([rx + (1 + 2.6 * th / PI) * np.cos(th), ry + (1 + 2.6 * th / PI) * np.sin(th)], 1), 1.1, C["red_dk"], (0.2, 0.3), "paint")
        lx, ly = 60, 30
        out += disc(lx, ly, 15, C["lapis"]) + ring(lx, ly, 11, 0.8, C["lapis_pale"], "paint") + gul(lx, ly, 7.5, 8, C["paper"], C["red"], 0.6)
    return out


def tas_hokka():
    """First era: an inkwell cut from stone, and red ground in a shell."""
    out = fill(yildiz(0, 0, 37, PI / 8, inner=0.9), C["paper2"])
    out += disc(0, 0, 26, C["paper3"], 1.2) + disc(0, 0, 18.5, C["ink"], 1.0) + _lika(0, 0, 4.4, "#56423a")
    sx, sy = 64, -20
    a = np.linspace(0.3, PI - 0.3, 15)
    rim = [(sx + 27 * math.cos(t) * (1 + 0.05 * (k % 2)), sy - 31 * math.sin(t) * (1 + 0.05 * (k % 2))) for k, t in enumerate(a)]
    out += fill([(sx - 7, sy + 5), *rim[::-1], (sx + 7, sy + 5)], C["paper"], 1.2)
    for t in a[1:-1:2]:
        out += stroke([(sx, sy + 3), (sx + 25 * math.cos(t), sy - 29 * math.sin(t))], 0.7)
    out += oval(sx, sy - 12, 13, 8.5, C["red"], 1.0)
    return out


def cam_hokka():
    """Fourth era: a square inkwell of cut glass with a brass collar."""
    out = rrect(-33, -33, 66, 66, C["lapis_pale"], LINE, r=9)
    out += fill([(-33 + 9, 33), (33, 33), (33, -33 + 9), (24, -24 + 6), (24, 24), (-24 + 6, 24)], C["lapis_lt"], 0)    # the far faces in shade
    out += rrect(-24, -24, 48, 48, C["lapis_pale"], 0.8, r=5)
    out += stroke([(-27, 20), (-27, -27), (20, -27)], 2.0, C["glaze"], "paint")                                       # the near edge catches light
    out += disc(0, 0, 17, C["paper3"], 1.0) + disc(0, 0, 11.5, C["ink"], 0.8)
    out += disc(58, 26, 13, C["paper3"], 1.0) + disc(58, 26, 8, C["paper2"], 0.7) + disc(58, 26, 3, C["paper3"], 0.7)  # the cap
    return out


# ================================================================ tools
def makas():
    """Paper scissors: long blades, two bows worked into leaves."""
    out = []
    for sg in (-1, 1):
        out += fill([(92, sg * 0.3), (92, sg * 5.5), (250, sg * 0.5)], C["lapis_pale"], 1.0)
        out += stroke([(98, sg * 3.6), (228, sg * 1.0)], 0.7, C["lapis_lt"], "paint")
        out += holed(arc(26, sg * 13, 22, 0, 2 * PI, 28, ry=10.5), [arc(26, sg * 13, 16.5, 0, 2 * PI, 24, ry=6.2)], C["lapis_lt"], 1.0)
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


def bicak():
    """First era: one knife for everything. Iron blade, wooden grip, three rivets."""
    out = fill([(70, -6.5), (150, -5.5), (174, 2), (150, 6.5), (70, 6.5)], C["paper3"], 1.0)
    out += stroke([(76, 3.2), (150, 3.2)], 0.9, C["paper2"], "paint")
    out += rrect(0, -7.5, 74, 15, C["wood_lt"], 1.0, r=4)
    for rx in (14, 36, 58):
        out += disc(rx, 0, 2.3, C["paper2"], 0.7)
    return out


def cetvel_tahtasi():
    """First era: a wooden rule, notched by hand."""
    out = rrect(0, -6.5, 196, 13, C["paper2"], 1.0, r=1)
    for k in range(1, 20):
        out += stroke([(k * 9.8, -6.5), (k * 9.8, -6.5 + (7 if k % 5 == 0 else 4))], 0.8)
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


def saat():
    """Fourth era: a watch. Time is kept by a machine now."""
    out = []
    ch = bez((30, -8), (70, -34), (96, 6), (132, -14), 26)
    for p in ch[::2]:
        out += ring(p[0], p[1], 3.0, 1.4, C["paper3"], "paint") + ring(p[0], p[1], 3.0, 0.5)
    out += rrect(26, -7, 10, 14, C["paper3"], 0.9, r=3)
    out += disc(0, 0, 31, C["paper3"], LINE) + disc(0, 0, 25.5, C["glaze"], 0.9)
    for k in range(12):
        a = 2 * PI * k / 12
        out += stroke([(20.5 * math.cos(a), 20.5 * math.sin(a)), (24 * math.cos(a), 24 * math.sin(a))], 1.4 if k % 3 == 0 else 0.7)
    out += brush([(0, 0), (-7, -9), (-12, -15)], 2.2, C["ink"], (0.0, 0.5)) + brush([(0, 0), (9, -3), (19, -6)], 1.6, C["ink"], (0.0, 0.5))
    out += disc(0, 0, 2.2, C["red"], 0.6)
    out += brush(arc(0, 0, 28.3, PI * 1.05, PI * 1.45, 10), 1.8, C["glaze"], (0.3, 0.3), "paint")
    return out


def gozluk():
    """Fourth era: spectacles, folded."""
    out = []
    for cx in (-24, 24):
        out += disc(cx, 0, 19, C["wood_lt"], 0) + ring(cx, 0, 19, 2.6, C["paper3"], "paint") + ring(cx, 0, 20.4, 0.6) + ring(cx, 0, 17.6, 0.6)
        out += brush(arc(cx, 0, 13, PI * 1.05, PI * 1.5, 8), 2.0, C["lapis_pale"], (0.3, 0.3), "paint")
    out += brush(bez((-6, -3), (-2, -9), (2, -9), (6, -3), 8), 2.4, C["paper3"], (0, 0), "paint", wmin=1.0)
    out += brush([(-43, -3), (-30, 14), (20, 24), (40, 23)], 1.8, C["paper3"], (0.0, 0.2), "paint", wmin=0.6)
    out += brush([(43, -3), (36, 16), (-16, 27), (-36, 26)], 1.8, C["paper3"], (0.0, 0.2), "paint", wmin=0.6)
    return out


# ================================================================ what the requester brought
def bohca(s=190):
    """The wrapping cloth of whoever brought the work. Second era: lapis sown
    with çintemani. First: a lattice of diamonds. Third: coarse stripes."""
    e = m.era()
    h = s / 2
    out = fill([(0, -h), (h, 0), (0, h), (-h, 0)], C["paper3"] if e == 3 else C["lapis"])
    for i in range(-2, 3):
        for j in range(-2, 3):
            x, y = (i - j) * s / 7.2, (i + j) * s / 7.2
            if abs(x) + abs(y) >= h - 22:
                continue
            if e == 1:
                out += fill([(x, y - 8), (x + 8, y), (x, y + 8), (x - 8, y)], C["paper"], 0.8) + fill([(x, y - 3), (x + 3, y), (x, y + 3), (x - 3, y)], C["red"], 0)
            elif e == 3:
                continue
            else:
                out += cintemani(x, y, 0.5, C["red"], C["paper"], C["lapis"])
    if e == 3:
        t = h / 2 - 6
        for k in range(-3, 4):
            c = k * h / 4
            out += stroke([(c / 2 - t, -c / 2 - t), (c / 2 + t, -c / 2 + t)], 5.0 if k % 2 == 0 else 2.6,
                          C["red"] if k % 2 == 0 else C["lapis"], "paint", cap="butt")
    out += stroke([(0, -h + 9), (h - 9, 0), (0, h - 9), (-h + 9, 0)], 1.3, C["paper"], "paint", closed=True)
    if e == 2:
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


def zarf():
    """Fourth era: letters come in envelopes, closed with wax."""
    w, h = 196, 124
    out = rrect(-w / 2, -h / 2, w, h, C["glaze"], LINE, r=2)
    out += stroke([(-w / 2, -h / 2), (0, 10), (w / 2, -h / 2)], 1.0) + stroke([(-w / 2, h / 2), (-28, -6)], 0.7) + stroke([(w / 2, h / 2), (28, -6)], 0.7)
    out += fill([(-w / 2 + 3, -h / 2 + 3), (0, 8), (-w / 2 + 3, h / 2 - 3)], C["paper"], 0)                       # the side in half shade
    out += stroke([(-w / 2, -h / 2), (0, 10), (w / 2, -h / 2)], 1.0)
    out += fill(lobed(0, 10, 16, 9, 0.16), C["red"], 1.0) + rose(0, 10, 7.5, C["red_lt"], 0.6)
    out += rrect(w / 2 - 38, -h / 2 + 10, 26, 30, C["lapis_pale"], 0.8) + ring(w / 2 - 25, -h / 2 + 25, 8, 0.8, C["lapis"])
    return out


# ================================================================ the four plates
def golge(node, dx=7.0, dy=9.0, color="#55301f"):
    """The cast shadow of a thing: its colour fields, flattened and moved."""
    def conv(items):
        out = []
        for it in items:
            if it is None:
                continue
            if isinstance(it, (list, tuple)):
                out += conv(it)
            elif "g" in it:
                out.append({"g": None, "items": conv(it["items"]), "t": it["t"]})
            elif it["role"] == "paint":
                c = copy.copy(it)
                c["fill"], c["stroke"] = (color if it["fill"] else None), (color if it["stroke"] else None)
                out.append(c)
        return out
    return G(None, conv([node]), f"translate({dx} {dy})")


def desk_plate():
    """The desk of the era in use, with the things that never leave it."""
    e = m.era()
    if e == 1:
        return [desk(3, 5, ((1010, 690, 32), (210, 905, 22))),
                G("bicak", bicak(), place(322, 266, -33)),
                G("cetvel_tahtasi", cetvel_tahtasi(), place(392, 288, -7)),
                G("kandil_govde", canak_kandil(), place(140, 160, -18)),
                G("kandil_isigi", yildiz_isigi(), place(212, 140)),
                G("kalemlik", kalemlik(), place(700, 76, 1)),
                G("hokka", tas_hokka(), place(1322, 142)),
                G("bohca", bohca(190) + [G("rulo", rulo(), place(-80, -4, -18))], place(1838, 168))]
    if e == 3:
        return [desk(5, 23, ((930, 700, 30), (240, 930, 26), (1560, 420, 22))),
                G("yama", rrect(0, 0, 330, 44, C["wood_lt"], LINE, r=2) + [x for px in (14, 316) for py in (11, 33) for x in disc(px, py, 2.6, C["char"], 0.7)]
                  + stroke([(30, 15), (300, 13)], 1.2, C["wood"], "paint") + stroke([(40, 30), (290, 31)], 1.2, C["wood"], "paint"), place(120, 862, -2.5)),
                G("yanik1", yanik(1560, 120, 210, 62, 3)),
                G("yanik2", yanik(1838, 520, 54, 150, 4)),
                G("yanik3", yanik(480, 62, 120, 22, 6)),
                G("kalemdan", kalemdan() + yanik(255, 22, 96, 34, 9), place(700, 84, 2.5)),
                G("bicak", bicak(), place(330, 258, -31)),
                G("kandil_govde", kandil(), place(140, 160, -18)),
                G("kandil_isigi", kandil_isigi(), place(212, 140)),
                G("hokka", hokka(False), place(1322, 142)),
                G("bohca", bohca(190) + [G("rulo", rulo(), place(-80, -4, -18))], place(1838, 168))]
    if e == 4:
        things = [G("gozluk", gozluk(), place(420, 236, -18)),
                  G("lamba", lamba(), place(176, 150)),
                  G("hokkalik", hokkalik(), place(690, 78, 1)),
                  G("hokka", cam_hokka(), place(1340, 142, 6)),
                  G("saat", saat(), place(1530, 150, -8)),
                  G("zarf", zarf(), place(1806, 170, 24))]
        return [desk(3, 31, ((1000, 690, 30),))] + [golge(t) for t in things] + things
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


def isik(out):
    """Fourth era: light falls. The lamp warms the wood near it, the far
    corner goes dim, and a polished board gives back a little of the window."""
    h, w = out.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    glow = np.exp(-(((xx - 176) / 330) ** 2 + ((yy - 150) / 300) ** 2))
    far = np.clip(((xx / w) + (yy / h)) / 2, 0, 1) ** 1.4
    sheen = np.exp(-(((xx * 0.5 + yy) - 520) / 120) ** 2) + 0.6 * np.exp(-(((xx * 0.5 + yy) - 1180) / 70) ** 2)
    inside = ((xx > X0) & (xx < X1) & (yy > Y0) & (yy < Y1)).astype(np.float32)
    k = 1 + 0.30 * glow - 0.20 * far + 0.045 * sheen * inside
    out[..., :3] = np.clip(out[..., :3] * k[..., None] + glow[..., None] * np.array([0.05, 0.035, 0.0], np.float32), 0, 1)
    return out
