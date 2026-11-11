"""Document and desk-object textures for the four eras (no generated imagery).

python3 tools/art/tex_docs.py      ->  assets/art/tex/*.png
Each document writes an albedo and whichever of rough / height / alpha /
metal maps Blender needs. Texts are the real puzzle texts from data/.
"""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from tex_core import (INK, INK_BROWN, LAPIS, OUT, RED_INK, Canvas, apply_ink, blur, burn_edge, clay, comp, edge_distance,
                      fbm, font, foxing, gilding, outline, paper, parchment, pigment, ridged, rotated_text, save_gray,
                      save_rgb, save_rgba, stains, text_mask, thumb_grime, wormholes)
from tex_illum import arc_text, seal

COBALT = (32, 54, 140)


def save_maps(name, **maps):
    for k, v in maps.items():
        if k == "albedo":
            save_rgb(v, OUT / f"{name}_albedo.png")
        else:
            save_gray(np.clip(v, 0, 1), OUT / f"{name}_{k}.png")


def ruling(w, h, ys, x0, x1, width=1.2):
    c = Canvas(w, h)
    for y in ys:
        c.line([(x0, y), (x1, y)], width)
    return c.mask()


# ================================================================ era 1
def tablet(seed=11):
    """Foundation-stone tablet: clay, incised text, soil still in the grooves."""
    w, h = 1280, 900
    img, height = clay(w, h, seed)
    lines = ["Meiros deiwosyo ghewom dōneti.", "Meiros bhāgom ghrebheti.", "Mēros nākos."]
    ys = [250, 470, 690]
    guide = ruling(w, h, [y + 26 for y in ys], 90, w - 90, 2.0)
    tm = text_mask(w, h, lines, 68, (w / 2 - 10, ys[0]), 220, seed=seed, wobble=1.3)
    groove = blur(tm, 2.2)
    lip = np.clip(blur(tm, 7) - blur(tm, 2.2), 0, 1)
    cracks = ridged(w, h, 5, seed + 1, 0.006) * np.clip(1 - edge_distance(w, h, seed + 12, 0.1) / 160, 0, 1)
    height = height - 0.30 * groove + 0.06 * lip - 0.10 * blur(guide, 1.5) - 0.12 * cracks
    chip = np.clip(1 - np.hypot(np.arange(w)[None, :] - w, np.arange(h)[:, None] - 0) / 170, 0, 1) ** 0.6
    chip *= fbm(w, h, 4, 8, 0.6, seed + 3) > 0.35
    height = height - 0.25 * chip
    soil = np.clip(groove * 1.6, 0, 1) * 0.75 + np.clip((fbm(w, h, 6, 5, 0.6, seed + 4) - 0.62) / 0.2, 0, 1) * 0.55
    soil += np.clip(1 - edge_distance(w, h, seed + 5, 0.1) / 90, 0, 1) * 0.5
    img = comp(img, (64, 46, 32), np.clip(soil, 0, 0.9))
    img = comp(img, (70, 48, 32), cracks * 0.6)
    img = comp(img, (206, 176, 136), chip * 0.6)                    # fresh break is paler
    img = comp(img, (96, 70, 50), blur(guide, 1.0) * 0.5)
    rough = np.clip(0.86 + 0.1 * soil - 0.08 * fbm(w, h, 3, 4, 0.5, seed + 6), 0, 1)
    save_maps("era1_tablet", albedo=img, height=np.clip(height, 0, 1), rough=rough)


def parchment_copy(seed=12):
    """The scribe's copy of doc 1, half written, on ruled parchment with a flaw hole."""
    w, h = 1300, 1800
    img, height = parchment(w, h, seed, age=0.45)
    ys = [380 + 150 * i for i in range(9)]
    rule = ruling(w, h, ys, 150, w - 150, 1.4)
    height = height - 0.03 * blur(rule, 1.2)
    img = comp(img, (170, 140, 100), rule * 0.18)
    prick = Canvas(w, h)
    for y in ys:
        prick.ellipse(w - 70, y, 2.2, 2.2)
    flaw = Canvas(w, h)
    flaw.ellipse(930, 1460, 46, 20)
    fl = ndi.gaussian_filter(flaw.mask(), 1.0)
    rim = np.clip(ndi.gaussian_filter(fl, 9) * 2.4 - fl, 0, 1)
    img = comp(img, (186, 156, 112), rim * 0.6)
    height += 0.06 * rim
    lines = ["Mīros dīwosyo khewom dōneti.", "Mīros phāgom khrepheti.", "Mēros"]
    tm = text_mask(w, h, lines, 76, (165, ys[0] - 12), 300, align="left", seed=seed, wobble=0.9)
    img, ink_a = apply_ink(img, tm, INK, seed + 1, density=0.97)
    rough = np.clip(0.7 - 0.36 * ink_a + 0.06 * fbm(w, h, 4, 8, 0.5, seed + 2), 0, 1)
    img = comp(img, (140, 104, 66), thumb_grime(w, h, seed + 3, (1, 1), 0.25) * 0.3)
    alpha = np.clip(1 - prick.mask() * 1.5 - fl * 1.2, 0, 1)
    save_maps("era1_parchment", albedo=img, height=np.clip(height, 0, 1), rough=rough, alpha=alpha)


def notebook_spread(name, left, right, seed, burnt=False, note=None, tone=(232, 218, 184)):
    """An open notebook: two pages, dry-point ruled, entries in the scribe's hand."""
    w, h = 2000, 1400
    img = np.zeros((h, w, 3), np.float32)
    height = np.zeros((h, w), np.float32)
    for k in range(2):
        pi, ph = paper(1000, 1400, seed + k, tone=tone, age=0.7, laid=False)
        img[:, k * 1000:(k + 1) * 1000] = pi
        height[:, k * 1000:(k + 1) * 1000] = ph
    gutter = np.exp(-((np.arange(w) - 1000) / 60.0) ** 2)[None, :] * np.ones((h, 1))
    img = img * (1 - 0.35 * gutter[..., None])
    ys = [210 + 92 * i for i in range(13)]
    rule = np.maximum(ruling(w, h, ys, 90, 930, 1.0), ruling(w, h, ys, 1070, 1910, 1.0))
    img = comp(img, (160, 140, 110), rule * 0.25)
    tm = np.maximum(text_mask(w, h, left, 50, (110, ys[0] - 14), 92, align="left", seed=seed + 2, wobble=1.0),
                    text_mask(w, h, right, 50, (1090, ys[0] - 14), 92, align="left", seed=seed + 3, wobble=1.0))
    img, ink_a = apply_ink(img, tm, INK_BROWN, seed + 4, density=0.9)
    if note:
        nm = rotated_text(w, h, note, 46, (760, 1240), 18, seed + 5)
        img, na = apply_ink(img, nm, (110, 50, 34), seed + 6, density=0.85)
        ink_a = np.maximum(ink_a, na)
    img = comp(img, (130, 98, 64), foxing(w, h, seed + 7, 70) * 0.4)
    img = comp(img, (120, 90, 60), stains(w, h, seed + 8, 1, (0.08, 0.14)) * 0.35)
    alpha = np.ones((h, w), np.float32)
    if burnt:
        a, char, scorch = burn_edge(w, h, seed + 9, "right", depth=0.30, rough=0.9)
        img = comp(img, (120, 74, 36), scorch * 0.7)
        img = comp(img, (26, 20, 16), char)
        alpha = a
    rough = np.clip(0.7 - 0.2 * ink_a, 0, 1)
    save_maps(name, albedo=img, height=np.clip(height, 0, 1), rough=rough, alpha=alpha)


# ================================================================ era 2
def copy_era2(seed=21):
    """Doc 2 copy on burnished paper, with the player's diagonal margin note."""
    w, h = 1300, 1800
    img, height = paper(w, h, seed, tone=(238, 226, 196), age=0.3)
    ys = [420 + 170 * i for i in range(7)]
    mistar = ruling(w, h, ys, 200, w - 330, 1.0)
    height = height - 0.025 * blur(mistar, 1.0)
    tm = text_mask(w, h, ["Mīros Mīrom ageti.", "Mīros nēkos."], 84, ((200 + w - 330) / 2, ys[0] - 10), 170, seed=seed, wobble=0.6)
    img, ink_a = apply_ink(img, tm, INK, seed + 1)
    nm = rotated_text(w, h, "nēkos: sürgün mü, ölü mü?", 38, (1110, 820), 52, seed + 2)
    img, na = apply_ink(img, nm, (96, 46, 32), seed + 3, density=0.85)
    blot = Canvas(w, h)
    blot.ellipse(300, 1290, 9, 7)
    blot.ellipse(312, 1296, 4, 4)
    bm = ndi.gaussian_filter(blot.mask(), 1.0)
    img = comp(img, INK, bm * 0.9)
    rough = np.clip(0.58 - 0.24 * np.maximum(ink_a, na) - 0.3 * bm, 0, 1)
    save_maps("era2_copy", albedo=img, height=np.clip(height, 0, 1), rough=rough)


def deed_era2(seed=22):
    """Doc 3, the merchant's debt deed: narrow sheet, two seals, a fold line."""
    w, h = 900, 1500
    img, height = paper(w, h, seed, tone=(226, 210, 172), age=0.8)
    tm = text_mask(w, h, ["Mātēros Mīrosyo", "grānom emeti."], 70, (w / 2, 470), 150, seed=seed, wobble=1.1)
    img, ink_a = apply_ink(img, tm, INK_BROWN, seed + 1)
    for (cx, cy, r, txt) in [(300, 1060, 70, "Mātēros"), (610, 1110, 62, "Kerdāgros")]:
        sm = seal(w, h, cx, cy, r, txt, seed + cx)
        img = comp(img, (60, 34, 28), sm * 0.8)
    fold = np.exp(-((np.arange(h) - h * 0.5) / 4.0) ** 2)[:, None] * np.ones((1, w))
    img = comp(img, (150, 120, 84), fold * 0.35)
    height = height - 0.05 * fold
    img = comp(img, (140, 100, 60), stains(w, h, seed + 2, 2, (0.12, 0.2)) * 0.4)
    save_maps("era2_deed", albedo=img, height=np.clip(height, 0, 1), rough=np.clip(0.7 - 0.2 * ink_a, 0, 1))


def wax_seal(seed=23):
    """Red wax disc with an impressed palace seal (for the sealed scroll)."""
    w = h = 512
    base = pigment(w, h, (150, 26, 24), seed, 0.2)
    c = Canvas(w, h)
    pts = []
    g = np.random.default_rng(seed)
    for k in range(48):
        a = 2 * math.pi * k / 48
        r = 220 + g.normal(0, 7)
        pts.append((256 + r * math.cos(a), 256 + r * math.sin(a)))
    c.poly(pts)
    disc = ndi.gaussian_filter(c.mask(), 2)
    sm = seal(w, h, 256, 256, 150, "Kerdēgros", seed)
    height = 0.35 * disc + 0.25 * ndi.gaussian_filter(disc, 18) - 0.12 * blur(sm, 1.5)
    img = comp(base, (96, 14, 14), blur(sm, 1.0) * 0.6)
    rough = np.clip(0.3 + 0.2 * blur(sm, 2), 0, 1)
    save_maps("era2_wax", albedo=img, height=np.clip(height + 0.3, 0, 1), rough=rough, alpha=disc)


# ================================================================ era 3
def burnt_doc(seed=31):
    """Doc 4 from the mountain archive: older paper, burnt edge, patched, stitched."""
    w, h = 1400, 1900
    img, height = paper(w, h, seed, tone=(214, 192, 150), age=1.0, laid=False)
    img = comp(img, (120, 90, 60), stains(w, h, seed + 1, 3, (0.1, 0.25)) * 0.5)
    patch = Canvas(w, h)
    patch.poly([(120, 170), (300, 150), (552, 158), (572, 330), (560, 512), (360, 530), (128, 540), (140, 360)])
    pm = ndi.gaussian_filter(patch.mask(), 1.5) * np.clip(0.75 + 0.5 * fbm(w, h, 4, 30, 0.6, seed + 12), 0, 1)
    pm = np.clip(pm * 1.3, 0, 1)
    pimg, _ = paper(w, h, seed + 2, tone=(226, 212, 180), age=0.8, laid=False)
    img = comp(img, pimg, pm)
    edge = outline(pm, 1.5)
    img = comp(img, (120, 96, 70), edge * 0.6)
    height = height + 0.05 * pm
    tear = Canvas(w, h)
    tear.line([(560, 1180), (700, 1240), (820, 1220), (960, 1300)], 2)
    tm_ = tear.mask()
    img = comp(img, (90, 66, 46), tm_)
    stitch = Canvas(w, h)
    for t in np.linspace(0.05, 0.95, 9):
        x = 560 + 400 * t
        y = 1180 + 120 * t + 10 * math.sin(t * 9)
        stitch.line([(x - 4, y - 14), (x + 4, y + 14)], 3.4)
    sm_ = stitch.mask()
    img = comp(img, (120, 92, 60), sm_)
    img = comp(img, (60, 44, 30), outline(sm_, 0.8) * 0.6)
    height = height + 0.04 * sm_
    tm = text_mask(w, h, ["Mīrom nēkom Mīros", "rīgos kheneti."], 82, (w / 2 - 120, 760), 210, seed=seed + 3, wobble=1.2)
    img, ink_a = apply_ink(img, tm, INK_BROWN, seed + 4, density=0.88, rim=0.6)
    sq = Canvas(w, h)
    sq.line([(980, 1520), (1180, 1520), (1180, 1700), (980, 1700), (980, 1520)], 9)
    zig = [(1000 + 20 * k, 1650 - (40 if k % 2 else 0)) for k in range(9)]
    sq.line(zig, 6)
    stamp = sq.mask() + text_mask(w, h, ["Mīro"], 56, (1080, 1590), 0, seed=seed + 5)
    stamp *= np.clip(0.4 + fbm(w, h, 4, 30, 0.6, seed + 6), 0, 1)
    img = comp(img, (110, 40, 28), np.clip(stamp, 0, 1) * 0.75)
    a, char, scorch = burn_edge(w, h, seed + 7, "right", depth=0.16, rough=0.8)
    a2, char2, scorch2 = burn_edge(w, h, seed + 8, "bottom", depth=0.08, rough=1.0)
    alpha = a * a2
    img = comp(img, (128, 80, 40), np.maximum(scorch, scorch2) * 0.75)
    img = comp(img, (24, 18, 14), np.maximum(char, char2))
    soot = np.clip(1 - edge_distance(w, h, seed + 9, 0.2) / 160, 0, 1) * fbm(w, h, 4, 6, 0.6, seed + 10)
    img = comp(img, (60, 50, 42), soot * 0.35)
    hole, halo = wormholes(w, h, seed + 11, 1, 6, 1.0)
    img = comp(img, (110, 76, 44), halo * 0.6)
    alpha = alpha * np.clip(1 - hole * 1.2, 0, 1)
    rough = np.clip(0.78 - 0.18 * ink_a + 0.1 * np.maximum(char, char2), 0, 1)
    save_maps("era3_burnt", albedo=img, height=np.clip(height, 0, 1), rough=rough, alpha=alpha)


# ================================================================ era 4
def ebru(seed=41, size=1024, palette=None):
    """Battal ebru (stone marbling) for the archive box covers."""
    g = np.random.default_rng(seed)
    palette = palette or [(52, 62, 98), (166, 130, 78), (138, 70, 64), (206, 190, 156), (62, 72, 66)]
    w = h = size
    npts = 70
    pts = g.random((npts, 2)) * size
    cols = np.array([palette[int(i)] for i in g.integers(len(palette), size=npts)], np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    wx = xx + (fbm(w, h, 5, 4, 0.6, seed) - 0.5) * 90
    wy = yy + (fbm(w, h, 5, 4, 0.6, seed + 1) - 0.5) * 90
    best = np.full((h, w), 1e9, np.float32)
    second = np.full((h, w), 1e9, np.float32)
    idx = np.zeros((h, w), np.int32)
    for i, (px, py) in enumerate(pts):
        dx = np.minimum(np.abs(wx - px), size - np.abs(wx - px))
        dy = np.minimum(np.abs(wy - py), size - np.abs(wy - py))
        d = dx * dx + dy * dy
        upd = d < best
        second = np.where(upd, best, np.minimum(second, d))
        idx = np.where(upd, i, idx)
        best = np.where(upd, d, best)
    img = cols[idx]
    gap = np.sqrt(second) - np.sqrt(best)
    rim = np.clip(1 - gap / 22.0, 0, 1) ** 1.5
    img = comp(img, img * 0.55 + 120, rim * 0.55)                    # paint thins at the edge
    vein = np.clip(1 - gap / 3.0, 0, 1)
    img = comp(img, (36, 30, 34), vein * 0.8)
    streak = fbm(w, h, 5, 30, 0.6, seed + 2)
    img = img * (0.86 + 0.2 * streak[..., None])
    speck = (g.random((h, w)) > 0.996).astype(np.float32)
    img = comp(img, (30, 26, 28), ndi.gaussian_filter(speck, 0.8) * 0.8)
    save_rgb(img, OUT / "era4_ebru_albedo.png")


def label(text_lines, name, seed, w=640, h=360):
    img, _ = paper(w, h, seed, tone=(236, 226, 200), age=0.5, laid=False)
    frame = Canvas(w, h)
    frame.line([(22, 22), (w - 22, 22), (w - 22, h - 22), (22, h - 22), (22, 22)], 3)
    frame.line([(32, 32), (w - 32, 32), (w - 32, h - 32), (32, h - 32), (32, 32)], 1.2)
    img = comp(img, (70, 60, 110), frame.mask() * 0.8)
    tm = text_mask(w, h, text_lines, 66, (w / 2, 150), 110, seed=seed, wobble=0.7)
    img, _ = apply_ink(img, tm, INK, seed + 1)
    save_rgb(img, OUT / f"{name}_albedo.png")


def catalog_card(seed=43):
    """Melno's catalogue card: the epilogue, read in the final archive."""
    w, h = 1500, 960
    img, height = paper(w, h, seed, tone=(232, 222, 196), age=0.45, laid=False)
    top = ruling(w, h, [150], 60, w - 60, 3.0)
    lines = ruling(w, h, [250 + 112 * i for i in range(6)], 60, w - 60, 1.2)
    img = comp(img, (170, 60, 50), top * 0.7)
    img = comp(img, (110, 130, 170), lines * 0.45)
    head = text_mask(w, h, ["Fēg · Çerdēgro · II"], 62, (80, 122), 0, align="left", seed=seed, wobble=0.5)
    body = text_mask(w, h, ["Kopyacı: adı bilinmiyor.",
                            "Belge 2: «Mīros nēkos.» Kenarda tek satır not var.",
                            "Belge 4: sıra değiştirilmiş; notu okudum.",
                            "Sahtecilik değil: çeviri.",
                            "Melno"], 50, (80, 235), 112, align="left", seed=seed + 1, wobble=0.8)
    img, a1 = apply_ink(img, head, INK, seed + 2)
    img, a2 = apply_ink(img, body, INK_BROWN, seed + 3)
    st = Canvas(w, h)
    st.ellipse(1330, 820, 86, 58)
    st2 = Canvas(w, h)
    st2.ellipse(1330, 820, 78, 50)
    ring = np.clip(st.mask() - st2.mask(), 0, 1)
    pw = text_mask(w, h, ["PW·8012"], 34, (1330, 832), 0, seed=seed + 4, wobble=0.2)
    stamp = np.clip(ring + pw, 0, 1) * np.clip(0.25 + 0.7 * fbm(w, h, 3, 20, 0.6, seed + 5), 0, 1)
    img = comp(img, (80, 96, 140), stamp * 0.55)
    img = comp(img, (140, 110, 80), foxing(w, h, seed + 6, 30) * 0.35)
    save_maps("era4_card", albedo=img, height=np.clip(height, 0, 1), rough=np.clip(0.68 - 0.2 * (a1 + a2), 0, 1))


# ================================================================ desk wear per era
def desk_wear(seed=51):
    """Grey masks the desk shader reads: ink stains and oil spots accumulate
    era by era, the third era adds scorch. R = ink, G = scratches, B = scorch."""
    w, h = 2048, 1200
    g = np.random.default_rng(seed)
    ink = np.zeros((h, w), np.float32)
    scratch = np.zeros((h, w), np.float32)
    for era in range(1, 5):
        c = Canvas(w, h, 1)
        for _ in range(6 + 6 * era):
            x, y, r = g.uniform(200, w - 200), g.uniform(150, h - 100), g.uniform(4, 26)
            c.ellipse(x, y, r, r * g.uniform(0.6, 1.1), fill=int(g.uniform(120, 255)))
            for _ in range(int(g.uniform(0, 4))):
                c.ellipse(x + g.normal(0, r * 2), y + g.normal(0, r * 2), r * 0.25, r * 0.25, fill=200)
        ring = ndi.gaussian_filter(c.mask(), 1.2)
        ink = np.maximum(ink, ring)
        s = Canvas(w, h, 1)
        for _ in range(40 * era):
            x, y = g.uniform(0, w), g.uniform(0, h)
            a, L = g.normal(0.05, 0.5), g.uniform(30, 240)
            s.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], 1, fill=int(g.uniform(60, 200)))
        scratch = np.maximum(scratch, s.mask())
        sc = np.zeros((h, w), np.float32)
        if era >= 3:
            sc = np.clip((fbm(w, h, 6, 4, 0.62, seed + 3) - 0.58) / 0.25, 0, 1)
            sc *= np.clip(1 - np.arange(w)[None, :] / (w * 0.45), 0, 1)
        rgb = np.dstack([ink, scratch, sc]) * 255
        Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(OUT / f"desk_wear_era{era}.png")


def build_all():
    OUT.mkdir(parents=True, exist_ok=True)
    tablet()
    parchment_copy()
    notebook_spread("era1_notebook",
                    ["Sözlük", "khewos — adak, sunu", "phāgos — kitap", "dīwos — tanrı", "dōneti — verir",
                     "khrepheti — yazar", "Mīros — büyük kardeş", "Mēros — küçük kardeş", "nākos — sürgün", "nēkos — ölü"],
                    ["Duyduklarım", "khewos (rahibe)", "phāgos (rahibe)", "", "bh → ph ?  dh → th ?"], 13)
    copy_era2()
    deed_era2()
    wax_seal()
    burnt_doc()
    notebook_spread("era3_notebook_argos",
                    ["Argos'un defteri", "Damaklaşma:", "  kh → ş · k → ç · g → c", "rīgo — bey", "nēko — sürgün",
                     "ēgro — tarla", "grēno — tahıl", "Mīro — kurucu"],
                    ["Kelime sonları düşmeye başladı;", "halk kimin yaptığını eklerden", "değil sıradan anlıyor."],
                    33, burnt=True, note="Önce gelen yapandır.", tone=(222, 204, 166))
    ebru()
    for i, n in enumerate(["I", "II", "III"]):
        label(["Fēg · Çerdēgro", n], f"era4_label_{i + 1}", 44 + i)
    catalog_card()
    desk_wear()


if __name__ == "__main__":
    import time
    t = time.time()
    build_all()
    print("docs", round(time.time() - t, 1), "s")
