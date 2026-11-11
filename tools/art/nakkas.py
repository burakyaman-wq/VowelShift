"""Nakkaş: the drawing kernel behind the game's miniature look.

A picture is a display list of elements, each either *paint* (a flat field of
body colour) or *ink* (the tahrir outline, writing, fine linework). The list is
written three ways:

  all    one layered SVG, groups named, for Illustrator
  paint  the colour fields alone
  ink    the lines alone, with every later colour field knocking out the lines
         it covers, so layering survives the separation

`pigment()` then paints the picture the way a miniature is painted: the colour
goes down first and settles (grain of the ground pigment, a darker rim where
the wash pooled against its edge, a trace of the brush), and the line is drawn
over it with a reed that breathes and an ink that thins. One slow tremor of
the hand moves paint and line together.

Nothing here knows about the game. The objects live in minyatur.py.
"""
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

INK = "#2a1b14"
LINE = 2.0                      # tahrir width at 1920 x 1080


# ---------------------------------------------------------------- geometry
def rot(pts, a):
    p = np.asarray(pts, float)
    c, s = math.cos(a), math.sin(a)
    return np.stack([p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c], 1)


def xf(pts, x=0.0, y=0.0, a=0.0, s=1.0, mirror=False):
    """Place a shape drawn along +x: mirror across x, scale, turn, move."""
    p = np.asarray(pts, float).copy()
    if mirror:
        p[:, 1] = -p[:, 1]
    p = rot(p * s, a)
    p[:, 0] += x
    p[:, 1] += y
    return p


def bez(p0, p1, p2, p3, n=12):
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def spline(ctrl, n=8, closed=False):
    """A smooth curve through the control points (Catmull-Rom)."""
    p = np.asarray(ctrl, float)
    q = np.vstack([p[-1], p, p[0], p[1]]) if closed else np.vstack([p[0], p, p[-1]])
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    out = []
    for i in range(len(q) - 3):
        p0, p1, p2, p3 = q[i:i + 4]
        out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out = np.vstack(out)
    return out if closed else np.vstack([out, p[-1]])


def arc(cx, cy, r, a0, a1, n=16, ry=None):
    a = np.linspace(a0, a1, n)
    return np.stack([cx + r * np.cos(a), cy + (ry or r) * np.sin(a)], 1)


def ribbon(pts, w, taper=(0.35, 0.35), wmin=0.12, breath=0.0, seed=0):
    """The outline of a brush stroke along a polyline. `w` is a width or one
    width per point; the stroke swells in from its two ends."""
    p = np.asarray(pts, float)
    seg = np.hypot(*np.diff(p, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = s / max(s[-1], 1e-6)
    tan = np.gradient(p, axis=0)
    tan /= np.linalg.norm(tan, axis=1, keepdims=True) + 1e-9
    nor = np.stack([-tan[:, 1], tan[:, 0]], 1)
    prof = np.ones_like(t)
    a, b = taper
    if a > 0:
        prof *= np.sin(0.5 * np.pi * np.clip(t / a, 0, 1))
    if b > 0:
        prof *= np.sin(0.5 * np.pi * np.clip((1 - t) / b, 0, 1))
    prof = wmin + (1 - wmin) * prof
    if breath:
        g = np.random.default_rng(seed)
        prof *= 1 + breath * np.sin(t * g.uniform(5, 11) + g.uniform(0, 6.28))
    half = 0.5 * np.asarray(w, float) * prof
    return np.vstack([p + nor * half[:, None], (p - nor * half[:, None])[::-1]])


def almond(length, width, k=0.45, n=13, sharp=1.0, base=0.0):
    """A leaf or petal lying along +x from (0,0) to (length,0); widest at k."""
    t = np.linspace(0, 1, n)
    hw = np.where(t < k, base + (1 - base) * np.sin(0.5 * np.pi * t / k),
                  np.cos(0.5 * np.pi * (t - k) / (1 - k)) ** sharp) * width / 2
    up = np.stack([length * t, -hw], 1)
    dn = np.stack([length * t, hw], 1)[::-1]
    return np.vstack([up, dn[1:] if base else dn[1:-1]])


def lobed(cx, cy, r, lobes, depth=0.14, n=None, phase=0.0, point=0.0):
    """A scalloped medallion outline (şemse): `lobes` round lobes with inward
    cusps; `point` > 0 gives each lobe an ogee tip."""
    n = n or lobes * 14
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    u = np.abs(np.sin(lobes * (a - phase) / 2))
    rr = r * (1 - depth + depth * u ** 0.55 + point * depth * np.clip(u - 0.9, 0, 1) * 10 * 0.6)
    return np.stack([cx + rr * np.cos(a), cy + rr * np.sin(a)], 1)


# ---------------------------------------------------------------- display list
def el(tag, role, fill=None, stroke=None, sw=0.0, cap="round", join="round", **attrs):
    return {"tag": tag, "role": role, "fill": fill, "stroke": stroke, "sw": sw, "cap": cap, "join": join, "a": attrs}


def G(gid, items, t=""):
    """A named group; in Illustrator a layer."""
    return {"g": gid, "items": items, "t": t}


def place(x, y, a=0.0, s=1.0):
    return f"translate({x:.1f} {y:.1f}) rotate({a:.2f}) scale({s})"


def d_of(pts, closed=True):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in np.asarray(pts)) + ("Z" if closed else "")


def fill(pts, color, line=LINE, lc=None):
    """A colour field with its outline."""
    d = d_of(pts)
    out = [el("path", "paint", fill=color, d=d)]
    if line:
        out.append(el("path", "ink", stroke=lc or INK, sw=line, d=d))
    return out


def holed(outer, holes, color, line=LINE, lc=None):
    """A colour field with holes cut in it."""
    d = d_of(outer) + "".join(d_of(h) for h in holes)
    out = [el("path", "paint", fill=color, d=d, **{"fill-rule": "evenodd"})]
    if line:
        out.append(el("path", "ink", stroke=lc or INK, sw=line, d=d))
    return out


def stroke(pts, w=LINE, color=None, role="ink", closed=False, cap="round", join="round"):
    return [el("path", role, stroke=color or INK, sw=w, cap=cap, join=join, d=d_of(pts, closed))]


def brush(pts, w, color=None, taper=(0.35, 0.35), role="ink", wmin=0.12, breath=0.0, seed=0):
    """A stroke of the brush: thin at both ends, full in the middle."""
    return [el("path", role, fill=color or INK, d=d_of(ribbon(pts, w, taper, wmin, breath, seed)))]


def disc(x, y, r, color, line=LINE, lc=None):
    out = [el("circle", "paint", fill=color, cx=f"{x:.1f}", cy=f"{y:.1f}", r=f"{r:.1f}")]
    if line:
        out.append(el("circle", "ink", stroke=lc or INK, sw=line, cx=f"{x:.1f}", cy=f"{y:.1f}", r=f"{r:.1f}"))
    return out


def ring(x, y, r, w=LINE, color=None, role="ink"):
    return [el("circle", role, stroke=color or INK, sw=w, cx=f"{x:.1f}", cy=f"{y:.1f}", r=f"{r:.1f}")]


def oval(x, y, rx, ry, color, line=LINE, a=0.0, lc=None):
    att = dict(cx=f"{x:.1f}", cy=f"{y:.1f}", rx=f"{rx:.1f}", ry=f"{ry:.1f}")
    if a:
        att["transform"] = f"rotate({a:.1f} {x:.1f} {y:.1f})"
    out = [el("ellipse", "paint", fill=color, **att)]
    if line:
        out.append(el("ellipse", "ink", stroke=lc or INK, sw=line, **att))
    return out


def rrect(x, y, w, h, color, line=LINE, r=0.0, lc=None, role="paint"):
    att = dict(x=f"{x:.1f}", y=f"{y:.1f}", width=f"{w:.1f}", height=f"{h:.1f}", rx=f"{r:.1f}")
    out = []
    if color:
        out.append(el("rect", role, fill=color, **att))
    if line:
        out.append(el("rect", "ink" if color else role, stroke=lc or INK, sw=line, **att))
    return out


def _emit(items, mode, ls=1.0):
    out = []
    for it in items:
        if it is None:
            continue
        if isinstance(it, (list, tuple)):
            out.append(_emit(it, mode, ls))
            continue
        if "g" in it:
            gid = f' id="{it["g"]}"' if it["g"] and mode == "all" else ""
            t = f' transform="{it["t"]}"' if it["t"] else ""
            out.append(f"<g{gid}{t}>{_emit(it['items'], mode, ls)}</g>")
            continue
        role, fl, st = it["role"], it["fill"], it["stroke"]
        if mode == "paint" and role != "paint":
            continue
        if mode in ("inkc", "inka"):
            if role == "paint":
                fl, st = ("#fff" if fl else None), ("#fff" if st else None)
            elif mode == "inka":
                fl, st = ("#000" if fl else None), ("#000" if st else None)
        att = "".join(f' {k}="{v}"' for k, v in it["a"].items()) + f' fill="{fl or "none"}"'
        if st:
            sw = it["sw"] * (ls if role == "ink" else 1.0)
            att += f' stroke="{st}" stroke-width="{sw:.2f}" stroke-linejoin="{it["join"]}" stroke-linecap="{it["cap"]}"'
        out.append(f'<{it["tag"]}{att}/>')
    return "".join(out)


def svg(items, w, h, pad=0, mode="all", scale=1, ls=1.0):
    vb = (-pad, -pad, w + 2 * pad, h + 2 * pad)
    bg = "" if mode in ("all", "paint") else f'<rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="#fff"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{vb[2] * scale}" height="{vb[3] * scale}" '
            f'viewBox="{vb[0]} {vb[1]} {vb[2]} {vb[3]}">{bg}{_emit(items, mode, ls)}</svg>')


def _raster(items, w, h, pad, mode, scale, ls=1.0):
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "a.svg", Path(tmp) / "a.png"
        src.write_text(svg(items, w, h, pad, mode, scale, ls))
        subprocess.run(["rsvg-convert", "-o", str(dst), str(src)], check=True)
        return np.asarray(Image.open(dst).convert("RGBA")).astype(np.float32) / 255.0


# ---------------------------------------------------------------- noise
def field(h, w, sigma, seed):
    """Smooth noise, zero mean and unit variance, with grain about `sigma` px."""
    g = np.random.default_rng(seed)
    if sigma <= 5:
        f = ndi.gaussian_filter(g.standard_normal((h, w), dtype=np.float32), sigma, mode="wrap")
    else:
        k = sigma / 2.5
        small = ndi.gaussian_filter(g.standard_normal((int(h / k) + 3, int(w / k) + 3), dtype=np.float32), 2.5, mode="wrap")
        f = np.asarray(Image.fromarray(small).resize((w, h), Image.BICUBIC))
    return (f - f.mean()) / (f.std() + 1e-6)


def streaks(h, w, across, along, seed, angle=0.0):
    """Noise drawn out one way, like the trail of a brush."""
    g = np.random.default_rng(seed)
    k = max(1.0, along / 3.0)
    small = ndi.gaussian_filter(g.standard_normal((h, int(w / k) + 3), dtype=np.float32), (across, 3.0), mode="wrap")
    f = np.asarray(Image.fromarray(small).resize((w, h), Image.BILINEAR))
    if angle:
        f = ndi.rotate(f, angle, reshape=False, order=1, mode="wrap")
    return (f - f.mean()) / (f.std() + 1e-6)


# ---------------------------------------------------------------- the painting
def pigment(paint, inkc, inka, S=2, seed=1, wobble=1.0, age=0.0, stamp=0.0, slip=1.0, spill=0.0, breathe=1.0, grain=1.0):
    """Lay the colour and draw the line. Arrays are at S times the final size:
    paint RGBA, the ink colour render and the ink coverage render.

    wobble   the tremor of the hand, shared by paint and line
    slip     how far the line misses the paint it outlines
    spill    how far the paint wanders on its own (a hurried or unsure hand)
    breathe  how much the line swells and thins
    grain    how coarse the pigment and the wash are
    age      toning and foxing of paper toward its edges
    stamp    for a seal: how much of the ink fails to print"""
    H, W = inka.shape[:2]
    a = paint[..., 3]
    pm = paint[..., :3] * a[..., None]
    ia = 1.0 - inka[..., :3].mean(-1)
    ipm = np.clip(inkc[..., :3] - (1.0 - ia)[..., None], 0, 1)

    if wobble > 0:
        yy, xx = np.meshgrid(np.arange(H, dtype=np.float32), np.arange(W, dtype=np.float32), indexing="ij")
        dx = (field(H, W, 30 * S, seed + 1) * 0.85 + field(H, W, 7 * S, seed + 2) * 0.28) * S * wobble
        dy = (field(H, W, 30 * S, seed + 3) * 0.85 + field(H, W, 7 * S, seed + 4) * 0.28) * S * wobble
        co = [yy + dy, xx + dx]
        pc = co if spill <= 0 else [co[0] + field(H, W, 16 * S, seed + 7) * spill * S, co[1] + field(H, W, 16 * S, seed + 8) * spill * S]
        pm = np.stack([ndi.map_coordinates(pm[..., i], pc, order=1, mode="nearest") for i in range(3)], -1)
        a = ndi.map_coordinates(a, pc, order=1, mode="nearest")
        # the line is drawn afterwards and does not sit exactly on the paint
        k = 0.3 * S * wobble * slip
        co = [co[0] + field(H, W, 70 * S, seed + 5) * k, co[1] + field(H, W, 70 * S, seed + 6) * k]
        ipm = np.stack([ndi.map_coordinates(ipm[..., i], co, order=1, mode="nearest") for i in range(3)], -1)
        ia = ndi.map_coordinates(ia, co, order=1, mode="nearest")
        del yy, xx, co

    rgb = pm / np.maximum(a, 1e-4)[..., None]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    v = rgb.max(-1)
    sat = (v - rgb.min(-1)) / (v + 1e-4)
    w_blue = np.clip((b - r) / 0.22, 0, 1)
    w_dark = np.clip((0.52 - v) / 0.2, 0, 1) * (1 - w_blue)
    w_paper = np.clip((v - 0.70) / 0.12, 0, 1) * np.clip((0.5 - sat) / 0.2, 0, 1) * (1 - w_blue)
    w_red = np.clip(1 - w_blue - w_dark - w_paper, 0, 1)

    # where one colour meets another, or meets a line, the wash pooled
    def edge(c):
        e = np.zeros_like(c)
        gx, gy = np.abs(c[:, 1:] - c[:, :-1]), np.abs(c[1:] - c[:-1])
        e[:, 1:] = gx
        e[:, :-1] = np.maximum(e[:, :-1], gx)
        e[1:] = np.maximum(e[1:], gy)
        e[:-1] = np.maximum(e[:-1], gy)
        return e
    bound = np.maximum.reduce([edge(pm[..., i]) for i in range(3)] + [edge(a)]) > 0.07
    bound |= ia > 0.5
    d = (ndi.distance_transform_edt(~bound).astype(np.float32) / S) if bound.any() else np.full((H, W), 1e3, np.float32)
    pool = 0.55 * np.exp(-d / 2.4) + 0.45 * np.exp(-d / 9.0)

    fine = field(H, W, 0.75 * S, seed + 10)
    mid = field(H, W, 3.5 * S, seed + 11)
    blot = field(H, W, 24 * S, seed + 12)
    big = field(H, W, 110 * S, seed + 13)
    drag = streaks(H, W, 1.1 * S, 34 * S, seed + 14)
    tex = (w_blue * (0.050 * fine + 0.045 * mid + 0.045 * blot + 0.030 * big + 0.02 * drag - 0.17 * pool)
           + w_red * (0.018 * fine + 0.026 * mid + 0.032 * blot + 0.022 * big + 0.025 * drag - 0.13 * pool)
           + w_dark * (0.028 * fine + 0.034 * mid + 0.045 * blot + 0.035 * big + 0.045 * drag - 0.14 * pool)
           + w_paper * (0.008 * fine + 0.009 * mid + 0.009 * blot + 0.012 * big - 0.028 * pool))
    tex = np.clip(1 + grain * tex, 0.6, 1.25)
    rgb = rgb * tex[..., None]
    # ground lapis is never even: pale crystals catch
    fleck = np.clip(fine - 1.7, 0, 1.5) * w_blue * 0.07
    rgb = rgb + fleck[..., None] * np.array([0.7, 0.8, 1.0], np.float32)

    if age > 0:
        inside = ndi.distance_transform_edt(a > 0.5).astype(np.float32) / S
        tone = age * w_paper * (0.06 * np.exp(-inside / 7.0) + 0.035 * np.exp(-inside / 50.0)
                                + 0.016 * np.clip(field(H, W, 60 * S, seed + 15), 0, 2))
        fox = np.clip(field(H, W, 3.2 * S, seed + 16) - 2.9, 0, 1) * age * w_paper * 0.22
        rgb = rgb * (1 - (tone + fox)[..., None] * np.array([0.75, 1.0, 1.45], np.float32))
    rgb = np.clip(rgb, 0, 1)

    # the line: a reed that swells and thins, an ink that is not everywhere black
    breath = np.clip(field(H, W, 45 * S, seed + 20) * 0.55 * breathe, -1, 1) * 0.85
    wide, thin = ndi.grey_dilation(ia, size=S + 1), ndi.grey_erosion(ia, size=S + 1)
    line = np.where(breath > 0, ia + (wide - ia) * breath, ia + (thin - ia) * -breath)
    line = 0.82 * line + 0.18 * ndi.gaussian_filter(line, 0.55 * S)
    dens = 0.90 + 0.10 * np.tanh(field(H, W, 9 * S, seed + 21))
    if stamp > 0:
        # a seal pressed by hand: the ink misses in places
        miss = np.clip(field(H, W, 2.2 * S, seed + 22) * 0.6 + field(H, W, 9 * S, seed + 23) * 0.6 + 0.9, 0, 1)
        dens = dens * (1 - stamp + stamp * miss)
    ic = ipm / np.maximum(ia, 1e-4)[..., None]
    far = ia < 0.2
    if far.any() and not far.all():
        idx = ndi.distance_transform_edt(far, return_distances=False, return_indices=True)
        ic = ic[idx[0], idx[1]]
    thinning = (1 - dens)[..., None] * (ic.max(-1, keepdims=True) < 0.35) * 2.2
    ic = ic * (1 - thinning) + np.array([0.33, 0.20, 0.13], np.float32) * thinning
    line = np.clip(line * dens, 0, 1)

    out_a = a * (1 - line) + line
    out_pm = rgb * (a * (1 - line))[..., None] + ic * line[..., None]
    out = np.concatenate([out_pm, out_a[..., None]], -1)
    out = out.reshape(H // S, S, W // S, S, 4).mean((1, 3))
    out[..., :3] /= np.maximum(out[..., 3:], 1e-4)
    return np.clip(out, 0, 1)


def paint_png(items, w, h, path, pad=0, S=2, seed=1, src=None, line=1.0, post=None, **how):
    """Draw a display list as a painted PNG; optionally keep its layered SVG.
    `line` scales every ink line; `how` goes to pigment(); `post` may rework
    the finished RGBA array (shadows, light)."""
    if src:
        Path(src).parent.mkdir(parents=True, exist_ok=True)
        Path(src).write_text(svg(items, w, h, pad, ls=line))
    layers = [_raster(items, w, h, pad, mode, S, line) for mode in ("paint", "inkc", "inka")]
    out = pigment(*layers, S=S, seed=seed, **how)
    if post:
        out = post(out)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA").save(path)
    return out
