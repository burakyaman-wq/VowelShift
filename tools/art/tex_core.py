"""Shared building blocks for the procedural textures (no generated imagery).

Everything works on float32 numpy arrays: colour images are (h, w, 3) in
0..255, masks and maps are (h, w) in 0..1. Line work is drawn with PIL at
SS-times supersampling and reduced, so edges stay soft like ink on paper.
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
KATIP = ROOT / "assets/fonts/Katip-Regular.ttf"
OUT = ROOT / "assets/art/tex"
SS = 2

INK = (30, 23, 20)            # carbon ink with gum arabic
INK_BROWN = (62, 40, 26)      # iron-gall ink gone brown
RED_INK = (150, 46, 32)       # rubric red
LAPIS = (34, 58, 132)
TURQ = (52, 120, 118)
VERMILION = (168, 56, 38)
WHITE_LEAD = (232, 226, 208)
GOLD = (206, 166, 82)


# ---------------------------------------------------------------- noise
def fbm(w, h, octaves=6, base=3, persist=0.55, seed=0):
    g = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        nx = max(2, int(base * 2 ** o))
        ny = max(2, int(round(nx * h / w)))
        small = g.random((ny, nx)).astype(np.float32)
        out += amp * np.asarray(Image.fromarray(small, "F").resize((w, h), Image.BICUBIC))
        tot += amp
        amp *= persist
    out /= tot
    lo, hi = np.percentile(out, 0.5), np.percentile(out, 99.5)
    return np.clip((out - lo) / (hi - lo + 1e-6), 0, 1)


def ridged(w, h, base, seed, width=0.03, octaves=4):
    n = fbm(w, h, octaves, base, 0.5, seed)
    return np.clip(1 - np.abs(n - 0.5) / width, 0, 1)


def blur(a, s):
    if a.ndim == 3:
        return np.stack([ndi.gaussian_filter(a[..., c], s) for c in range(a.shape[2])], -1)
    return ndi.gaussian_filter(a, s)


def comp(base, color, alpha):
    a = np.clip(alpha, 0, 1)[..., None]
    col = color if isinstance(color, np.ndarray) else np.array(color, np.float32)
    return base * (1 - a) + col * a


def flat(w, h, color):
    return np.ones((h, w, 3), np.float32) * np.array(color, np.float32)


def save_rgb(a, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(path)


def save_gray(a, path):
    Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), "L").save(path)


def save_rgba(rgb, alpha, path):
    im = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
    Image.fromarray(im, "RGBA").save(path)


# ---------------------------------------------------------------- drawing
class Canvas:
    """A supersampled 8-bit mask canvas; .mask() returns the reduced 0..1 array."""

    def __init__(self, w, h, ss=SS):
        self.w, self.h, self.ss = w, h, ss
        self.im = Image.new("L", (w * ss, h * ss), 0)
        self.d = ImageDraw.Draw(self.im)

    def p(self, pts):
        return [(x * self.ss, y * self.ss) for x, y in pts]

    def line(self, pts, width, fill=255):
        self.d.line(self.p(pts), fill=fill, width=max(1, int(round(width * self.ss))), joint="curve")

    def poly(self, pts, fill=255):
        self.d.polygon(self.p(pts), fill=fill)

    def ellipse(self, cx, cy, rx, ry, fill=255):
        s = self.ss
        self.d.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=fill)

    def mask(self):
        return np.asarray(self.im.resize((self.w, self.h), Image.LANCZOS)).astype(np.float32) / 255


def font(size, path=KATIP):
    return ImageFont.truetype(str(path), int(size))


def text_mask(w, h, lines, size, origin, leading, align="center", seed=0, wobble=1.0, path=KATIP, angle=0.0):
    """Ink coverage for lines of text. Each word is set separately with a small
    baseline drift, rotation and scale change, as a hand would write it."""
    g = np.random.default_rng(seed)
    f = font(size, path)
    canvas = Image.new("L", (w, h), 0)
    x0, y0 = origin
    space = f.getlength(" ")
    for i, line in enumerate(lines):
        y = y0 + i * leading
        words = line.split(" ")
        widths = [f.getlength(wd) for wd in words]
        total = sum(widths) + space * (len(words) - 1)
        x = {"center": x0 - total / 2, "right": x0 - total}.get(align, x0)
        line_rot = g.normal(0, 0.22 * wobble)
        for wd, ww in zip(words, widths):
            pad = int(size * 0.7)
            tw, th = int(ww + 2 * pad), int(size * 2.4)
            wim = Image.new("L", (tw, th), 0)
            ImageDraw.Draw(wim).text((pad, int(size * 1.5)), wd, font=f, fill=255, anchor="ls")
            sc = 1 + g.normal(0, 0.012 * wobble)
            wim = wim.resize((max(1, int(tw * sc)), max(1, int(th * sc))), Image.BICUBIC)
            wim = wim.rotate(line_rot + g.normal(0, 0.3 * wobble) + angle, resample=Image.BICUBIC)
            dy = g.normal(0, size * 0.012 * wobble)
            canvas.paste(255, (int(round(x - pad)), int(round(y - size * 1.5 + dy))), wim)
            x += ww + space
    return np.asarray(canvas).astype(np.float32) / 255


def rotated_text(w, h, text, size, center, angle, seed=0, path=KATIP):
    """A single line of text rotated about its centre (margin notes, labels)."""
    f = font(size, path)
    tw = int(f.getlength(text) + size * 2)
    th = int(size * 2.6)
    im = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(im).text((tw / 2, th * 0.62), text, font=f, fill=255, anchor="ms")
    im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    canvas = Image.new("L", (w, h), 0)
    canvas.paste(255, (int(center[0] - im.width / 2), int(center[1] - im.height / 2)), im)
    return np.asarray(canvas).astype(np.float32) / 255


def apply_ink(img, cov, color=INK, seed=0, density=0.94, rim=0.45, bleed=0.18):
    """Lay ink: uneven density, darker rims where it dried, a faint feathering."""
    h, w = cov.shape
    n = fbm(w, h, 5, max(8, w // 60), 0.6, seed)
    broad = fbm(w, h, 3, 4, 0.5, seed + 1)
    a = cov * np.clip(density * (0.84 + 0.2 * n + 0.14 * (broad - 0.5)), 0, 1)
    col = np.array(color, np.float32)
    out = comp(img, col, a)
    halo = np.clip(ndi.gaussian_filter(cov, 1.6) - cov, 0, 1) * bleed
    out = comp(out, col * 0.7 + 60, halo)
    edge = np.clip(cov - ndi.gaussian_filter(cov, 1.0), 0, 1) * rim * 2
    out = comp(out, col * 0.5, edge)
    return out, a


# ---------------------------------------------------------------- substrates
def fibres(w, h, count, seed, length=(6, 26), alpha=(10, 40)):
    g = np.random.default_rng(seed)
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for _ in range(count):
        x, y = g.uniform(0, w), g.uniform(0, h)
        a, l = g.uniform(0, math.pi), g.uniform(*length)
        bend = g.normal(0, 0.25)
        pts = [(x + t * l * math.cos(a + bend * t), y + t * l * math.sin(a + bend * t)) for t in np.linspace(0, 1, 5)]
        d.line(pts, fill=int(g.uniform(*alpha)), width=1)
    return ndi.gaussian_filter(np.asarray(im).astype(np.float32) / 255, 0.5)


def edge_distance(w, h, seed, rough=0.05):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    warp = (fbm(w, h, 5, 6, 0.6, seed) - 0.5) * rough * min(w, h)
    return d + warp


def paper(w, h, seed=0, tone=(234, 220, 188), age=0.5, laid=True):
    """Burnished (aharli) paper: cream, smooth, toned at the edges."""
    n1, n2, n3 = fbm(w, h, 7, 3, 0.55, seed), fbm(w, h, 5, 30, 0.6, seed + 1), fbm(w, h, 3, 2, 0.5, seed + 2)
    img = np.array(tone, np.float32) * (0.93 + 0.055 * n1[..., None] + 0.03 * n2[..., None])
    img[..., 2] -= 12 * n3 * age
    img[..., 1] -= 4 * n3 * age
    img = comp(img, (176, 146, 104), fibres(w, h, int(w * h / 260), seed + 3) * 0.35)
    img = comp(img, (250, 244, 228), fibres(w, h, int(w * h / 900), seed + 4, alpha=(10, 30)) * 0.4)
    tone_edge = np.clip(1 - edge_distance(w, h, seed + 5) / (0.06 * min(w, h)), 0, 1) ** 1.6
    img = comp(img, (170, 128, 80), tone_edge * 0.45 * age)
    height = 0.5 + 0.03 * (n2 - 0.5) + 0.02 * (n1 - 0.5)
    if laid:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        lines = 0.5 + 0.5 * np.sin(yy / max(2.0, h / 900) * math.pi)
        chains = np.exp(-((xx % (w / 9.0)) - w / 18.0) ** 2 / (2 * (w / 600) ** 2))
        height += 0.006 * lines + 0.01 * chains
        img *= (1 - 0.012 * chains)[..., None]
    return img, height


def parchment(w, h, seed=0, tone=(222, 202, 160), age=0.6):
    """Skin: uneven, follicle speckles, translucent veins, cockled."""
    n1, n2, n3 = fbm(w, h, 7, 2, 0.6, seed), fbm(w, h, 5, 14, 0.6, seed + 1), fbm(w, h, 4, 3, 0.55, seed + 2)
    img = np.array(tone, np.float32) * (0.86 + 0.14 * n1[..., None] + 0.04 * n2[..., None])
    img[..., 2] -= 18 * n3 * age
    g = np.random.default_rng(seed + 3)
    spots = Canvas(w, h, 1)
    clusters = g.uniform(0, 1, (40, 2)) * [w, h]
    for _ in range(int(w * h / 1400)):
        c = clusters[g.integers(len(clusters))]
        x, y = c + g.normal(0, min(w, h) * 0.08, 2)
        r = g.uniform(0.6, 1.8)
        spots.ellipse(x, y, r, r, fill=int(g.uniform(80, 200)))
    sp = ndi.gaussian_filter(spots.mask(), 0.7)
    img = comp(img, (120, 92, 60), sp * 0.55)
    veins = ridged(w, h, 3, seed + 4, 0.02) * fbm(w, h, 3, 3, 0.5, seed + 5)
    img = comp(img, (238, 222, 186), veins * 0.25)
    img = comp(img, (150, 112, 66), np.clip(1 - edge_distance(w, h, seed + 6, 0.08) / (0.08 * min(w, h)), 0, 1) ** 1.4 * 0.5 * age)
    height = 0.5 + 0.12 * (fbm(w, h, 3, 2, 0.5, seed + 7) - 0.5) + 0.03 * (n2 - 0.5)
    return img, height


def clay(w, h, seed=0, tone=(176, 134, 94)):
    n1, n2, n3 = fbm(w, h, 7, 3, 0.55, seed), fbm(w, h, 5, 40, 0.6, seed + 1), fbm(w, h, 4, 6, 0.5, seed + 2)
    img = np.array(tone, np.float32) * (0.82 + 0.2 * n1[..., None] + 0.08 * n2[..., None])
    img = comp(img, (120, 84, 56), np.clip((n3 - 0.6) / 0.3, 0, 1) * 0.5)      # firing clouds
    grit = (np.random.default_rng(seed + 3).random((h, w)) > 0.985).astype(np.float32)
    img = comp(img, (226, 206, 170), ndi.gaussian_filter(grit, 0.6) * 0.8)      # temper grains
    height = 0.5 + 0.05 * (n1 - 0.5) + 0.04 * (n2 - 0.5)
    return img, height


# ---------------------------------------------------------------- ageing
def stains(w, h, seed, count=3, size=(0.08, 0.2)):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    warp = (fbm(w, h, 5, 5, 0.6, seed) - 0.5)
    for _ in range(count):
        cx, cy = g.uniform(0, w), g.uniform(0, h)
        r = g.uniform(*size) * min(w, h)
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) + warp * r * 0.6
        ring = np.exp(-((d - r) ** 2) / (2 * (r * 0.02) ** 2))
        inner = np.clip(1 - d / r, 0, 1) ** 0.6 * 0.22
        out = np.maximum(out, np.clip(ring * 0.8 + inner, 0, 1) * g.uniform(0.4, 0.8))
    return out


def foxing(w, h, seed, count=80, rmax=9):
    g = np.random.default_rng(seed)
    c = Canvas(w, h, 1)
    for _ in range(count):
        x, y, r = g.uniform(0, w), g.uniform(0, h), g.uniform(1.5, rmax)
        c.ellipse(x, y, r, r * g.uniform(0.7, 1.2), fill=int(g.uniform(60, 200)))
    m = c.mask()
    return np.clip(ndi.gaussian_filter(m, 2.2) * 1.3 + ndi.gaussian_filter(m, 0.8) * 0.5, 0, 1)


def thumb_grime(w, h, seed, corner=(1, 1), reach=0.22):
    """Readers turn pages at the same corner for centuries."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = corner[0] * w, corner[1] * h
    d = np.sqrt(((xx - cx) / w) ** 2 + ((yy - cy) / h) ** 2)
    n = fbm(w, h, 5, 8, 0.6, seed)
    return np.clip(1 - d / reach, 0, 1) ** 1.8 * (0.5 + 0.7 * n)


def wormholes(w, h, seed, tunnels=3, holes=10, scale=1.0):
    """Bookworm damage: meandering channels and pin holes (alpha 0 where eaten)."""
    g = np.random.default_rng(seed)
    c = Canvas(w, h)
    for _ in range(tunnels):
        x, y = g.uniform(0, w), g.uniform(0, h)
        a = g.uniform(0, 2 * math.pi)
        pts = []
        for _ in range(int(g.uniform(20, 60))):
            a += g.normal(0, 0.45)
            x += 5 * scale * math.cos(a)
            y += 5 * scale * math.sin(a)
            pts.append((x, y))
        c.line(pts, g.uniform(4, 7) * scale)
    for _ in range(holes):
        x, y, r = g.uniform(0, w), g.uniform(0, h), g.uniform(1.8, 3.5) * scale
        c.ellipse(x, y, r, r)
    hole = c.mask()
    halo = np.clip(ndi.gaussian_filter(hole, 3 * scale) * 2.2 - hole, 0, 1)
    return hole, halo


def burn_edge(w, h, seed, side="right", depth=0.18, rough=0.6):
    """Alpha (0 = burnt away), a char band and a scorch halo along one side."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    if side == "right":
        d = (w - 1 - xx) / w
    elif side == "left":
        d = xx / w
    elif side == "bottom":
        d = (h - 1 - yy) / h
    else:
        d = yy / h
    n = fbm(w, h, 6, 4, 0.62, seed)
    front = d - depth * (0.35 + rough * n)
    alpha = np.clip(front * 220, 0, 1)
    char = np.clip(1 - front / 0.012, 0, 1) * alpha
    scorch = np.clip(1 - front / 0.06, 0, 1) * alpha
    return alpha, char, scorch


# ---------------------------------------------------------------- gilding & paint
def gilding(w, h, seed=0, burnish=0.6):
    """Gold leaf: colour, roughness and a slight relief, with crackle and loss."""
    n = fbm(w, h, 6, 8, 0.55, seed)
    streak = fbm(w, h, 3, 2, 0.5, seed + 1)
    img = np.array(GOLD, np.float32) * (0.86 + 0.22 * n[..., None]) + 30 * streak[..., None] ** 3
    crack = ridged(w, h, 26, seed + 2, 0.02)
    img = comp(img, (110, 76, 36), crack * 0.3)
    loss = np.clip((fbm(w, h, 5, 10, 0.55, seed + 3) - 0.88) / 0.05, 0, 1)
    loss *= np.clip((fbm(w, h, 3, 40, 0.6, seed + 4) - 0.45) / 0.1, 0, 1)
    img = comp(img, (146, 72, 48), loss * 0.9)                      # red bole under the leaf
    rough = np.clip(0.42 - 0.22 * burnish + 0.18 * (1 - n) + 0.4 * loss + 0.2 * crack, 0.12, 1)
    metal = np.clip(1 - loss * 1.1 - crack * 0.3, 0, 1)
    return img, rough, metal


def pigment(w, h, color, seed=0, grain=0.16):
    n = fbm(w, h, 6, max(8, w // 40), 0.6, seed)
    m = fbm(w, h, 3, 4, 0.5, seed + 1)
    return np.array(color, np.float32) * (1 - grain / 2 + grain * n[..., None]) * (0.94 + 0.1 * m[..., None])


def outline(mask, width=1.2):
    """A drawn contour (tahrir) around a filled shape."""
    inner = ndi.gaussian_filter(mask, width)
    return np.clip(np.abs(mask - inner) * 3.2, 0, 1)
