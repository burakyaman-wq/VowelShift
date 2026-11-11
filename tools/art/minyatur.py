"""The game's look: the scribe's desk as a miniature, seen straight from
above, in the manner of four schools. Rules: assets/art/STYLE.md.

    python3 tools/art/minyatur.py              every sprite of every era
    python3 tools/art/minyatur.py 2            the second era only
    python3 tools/art/minyatur.py 1 masa karo  named sprites of the first
    python3 tools/art/minyatur.py --sheet      contact sheets for looking at

Second-era sprites keep the plain names the game started with; the others
carry `_cagN`. The game asks for the era it needs and falls back on the plain
name (scripts/ui/art.gd). Each sprite also leaves a layered SVG in
assets/art/style/sprites_src for touching up in Illustrator.

  nakkas.py  the kernel: display list, paint and ink layers, the pigment pass
  motif.py   palette, eras, ornament
  masa.py    the desk plate of each era
  kagit.py   documents, copy sheet, slip, notebook
  karo.py    rule tiles, pictograms, tray, stop mark, seal
"""
import sys

import numpy as np
from PIL import Image

import kagit
import karo
import masa
import motif as m
import nakkas as nk
from motif import C, H, ROOT, W
from nakkas import G, place

SPR = ROOT / "assets/art/sprites"
SRC = ROOT / "assets/art/style/sprites_src"


def fname(name):
    e = m.era()
    if name == "masa":
        return f"masa_cag{e}"
    return name if e == 2 else f"{name}_cag{e}"


def sprite(name, items, w, h, pad=8, seed=1, wobble=1.0, **kw):
    """Paint one sprite in the hand of the era in use."""
    st = m.ERAS[m.era()]
    how = dict(st["how"])
    how["wobble"] = how.get("wobble", 1.0) * wobble
    how.update(kw)
    nk.paint_png(items, w, h, SPR / f"{fname(name)}.png", pad=pad, seed=seed, src=SRC / f"{fname(name)}.svg", line=st["line"], **how)
    print("  ", fname(name))


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
    mm = np.clip(0.982 + fib + blot + burn - age, 0, 1)
    rgb = np.stack([mm ** 0.9, mm, mm ** 1.2], -1)
    Image.fromarray((rgb * 255 + 0.5).astype(np.uint8)).save(SPR / "sayfa_doku.png")
    print("   sayfa_doku")


def painters():
    """name -> a function that paints it, for the era in use."""
    e = m.era()
    tr, tw, th = karo.tray()
    age = {1: 1.3, 2: 1.0, 3: 1.5, 4: 0.5}[e]
    pen = masa.tuy(250) if e == 4 else masa.pen(250)
    todo = {
        "masa": lambda: sprite("masa", masa.desk_plate(), W, H, 0, seed=7 + e, post=masa.isik if e == 4 else None),
        "belge_kagit": lambda: sprite("belge_kagit", kagit.document_page(680, 440), 680, 440, seed=11, age=age),
        "belge_okuma": lambda: sprite("belge_okuma", kagit.document_page(1520, 760, True), 1520, 760, seed=12, age=age),
        "kopya_kagit": lambda: sprite("kopya_kagit", kagit.copy_sheet(), 420, 500, seed=13, age=0.25 * age),
        "pusula": lambda: sprite("pusula", kagit.slip(), 360, 250, seed=14, age=0.7 * age),
        "defter": lambda: sprite("defter", kagit.notebook(), 520, 420, 20, seed=15),
        "tepsi": lambda: sprite("tepsi", tr, tw, th, seed=16),
        "karo_cerceve": lambda: sprite("karo_cerceve", karo.tile_frame(), 150, 200, seed=17, wobble=0.7),
        "durak": lambda: sprite("durak", karo.durak(), 28, 28, 2, seed=18, wobble=0.4),
        "muhur": lambda: sprite("muhur", karo.seal(), 80, 80, seed=19, wobble=0.6, stamp=0.75),
        "kalem": lambda: sprite("kalem", [G("kalem", pen, place(0, 9))], 250, 18, seed=20, wobble=0.6),
        "kelime_fisi": lambda: sprite("kelime_fisi", kagit.word_slip(), 120, 44, 6, seed=21, wobble=0.5, age=0.4 * age),
    }
    return todo


def pictos(only=None):
    """Every rule's pictogram, each in the hand of the era that found the rule.
    These are not per-era files: a tile keeps the look it was born with."""
    for rule, e in karo.RULE_ERA.items():
        if only and e not in only:
            continue
        m.use_era(e)
        st = m.ERAS[e]
        how = dict(st["how"])
        how["wobble"] = how.get("wobble", 1.0) * 0.6
        nk.paint_png(karo.picto(rule), 150, 200, SPR / f"picto_{rule}.png", pad=8, seed=30 + int(rule[1]), src=SRC / f"picto_{rule}.svg", line=st["line"], **how)
        print("  ", f"picto_{rule}")


def contact_sheet(e):
    """Every loose sprite of an era on its own wooden ground, for looking at."""
    m.use_era(e)
    names = ["belge_kagit", "kopya_kagit", "pusula", "defter", "tepsi", "karo_cerceve", "durak", "muhur", "kalem"]
    bg = Image.new("RGBA", (1920, 1080), C["wood"])
    x = y = 20
    row = 0
    for n in names:
        im = Image.open(SPR / f"{fname(n)}.png").convert("RGBA")
        if x + im.width > 1900:
            x, y, row = 20, y + row + 20, 0
        bg.alpha_composite(im, (x, y))
        x += im.width + 20
        row = max(row, im.height)
    tile = Image.open(SPR / f"{fname('karo_cerceve')}.png").convert("RGBA")
    for rule, re in karo.RULE_ERA.items():
        if re != e:
            continue
        t = tile.copy()
        t.alpha_composite(Image.open(SPR / f"picto_{rule}.png").convert("RGBA"))
        bg.alpha_composite(t, (x, y))
        x += t.width + 20
    out = ROOT / f"assets/art/style/sayfa_cag{e}.png"
    bg.convert("RGB").save(out)
    return out


if __name__ == "__main__":
    SPR.mkdir(parents=True, exist_ok=True)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    eras = [int(a) for a in args if a.isdigit()] or [1, 2, 3, 4]
    names = [a for a in args if not a.isdigit()]
    for e in eras:
        m.use_era(e)
        print(f"{e}. çağ: {m.ERAS[e]['name']}")
        for name, fn in painters().items():
            if not names or any(name.startswith(a) for a in names):
                fn()
    if not names or any(a.startswith("picto") for a in names):
        pictos(eras)
    if not names or "sayfa_doku" in names:
        page_grain()
    if "--sheet" in sys.argv:
        for e in eras:
            print(contact_sheet(e))
