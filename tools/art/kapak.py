"""The itch.io cover and banner: one word through the game's three eras,
each band painted by its own school.

    python3 tools/art/kapak.py   ->  assets/art/style/kapak.png (1260 x 1000), kapak_630.png,
                                     banner.png (1920 x 480), banner_960.png

The word is bhāgos, "book", as the rules carry it: phāgos (I), phēgos (II), phēgo (III).
The same page is painted three times and cut into bands.
"""
import numpy as np
from PIL import Image, ImageDraw

import kagit
import masa
import motif as m
from motif import C, ROOT, text_path
from nakkas import G, el, place
import nakkas as nk

OUT = ROOT / "assets/art/style"
ERAS = {1: ("I", "phāgos"), 2: ("II", "phēgos"), 3: ("III", "phēgo")}
SEAM_DARK, SEAM_LIGHT = (42, 27, 20), (236, 220, 185)


def word(s, x, y, size, color, anchor="middle"):
    d, _ = text_path(s, x, y, size, anchor)
    return [el("path", "paint", fill=color, d=d)]


def paint(e, items, w, h, name, seed):
    st = m.ERAS[e]
    how = dict(st["how"])
    how["wobble"] = how.get("wobble", 1.0) * 0.55        # a steadier hand: the lettering must read small
    how["spill"] = how.get("spill", 0.0) * 0.45
    p = OUT / f"_{name}{e}.png"
    a = nk.paint_png(items, w, h, p, seed=seed, line=st["line"], age=0.8, **how)[..., :3]
    p.unlink()
    return a


def compose(shots, band, w, h):
    out = np.zeros((h, w, 3), np.float32)
    for e in (1, 2, 3):
        out[band == e - 1] = shots[e][band == e - 1]
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8))


def seam(d, a, b, gap=None):
    """A cut between two schools; `gap` (y0, y1) or (x0, x1) leaves the title whole."""
    for col, wd in ((SEAM_DARK, 6), (SEAM_LIGHT, 2)):
        d.line([a, b], fill=col, width=wd)


def cover():
    CW, CH, PW, PH, SC = 1260, 1000, 700, 560, 1.6
    OX, OY = (CW - PW * SC) / 2, (CH - PH * SC) / 2
    rows = {1: 222, 2: 352, 3: 482}                    # baselines of the three forms, page units
    shots = {}
    for e in (1, 2, 3):
        m.use_era(e)
        masa.W, masa.H, masa.X1, masa.Y1 = CW, CH, CW - 58, CH - 52
        page = kagit.document_page(PW, PH, True, 40 + e)
        num, form = ERAS[e]
        page += word("Vowel Shift", PW / 2, 81.5, 31, C["paper"])
        page += word(num, 150, rows[e] - 6, 34, C["red"])
        page += word(form, 395, rows[e], 84, C["ink"])
        shots[e] = paint(e, [masa.desk(3, 50 + e, ()), G("sayfa", page, place(OX, OY, 0, SC))], CW, CH, "kapak", 60 + e)
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
    cuts = [OY + 270 * SC, OY + 400 * SC]              # between the rows, tilted a little
    tilt = 0.04
    b1 = yy > cuts[0] + (xx - CW / 2) * tilt
    b2 = yy > cuts[1] - (xx - CW / 2) * tilt
    band = b1.astype(int) + b2.astype(int)
    img = compose(shots, band, CW, CH)
    d = ImageDraw.Draw(img)
    seam(d, (0, cuts[0] - CW / 2 * tilt), (CW, cuts[0] + CW / 2 * tilt))
    seam(d, (0, cuts[1] + CW / 2 * tilt), (CW, cuts[1] - CW / 2 * tilt))
    img.save(OUT / "kapak.png")
    img.resize((630, 500), Image.LANCZOS).save(OUT / "kapak_630.png")


def banner():
    BW, BH, PW, PH, SC = 1920, 480, 1200, 290, 1.4
    OX, OY = (BW - PW * SC) / 2, (BH - PH * SC) / 2
    shots = {}
    for e in (1, 2, 3):
        m.use_era(e)
        masa.W, masa.H, masa.X1, masa.Y1 = BW, BH, BW - 58, BH - 52
        page = kagit.document_page(PW, PH, False, 70 + e)
        page += word("Vowel Shift", PW / 2, 178, 84, C["ink"])
        page += word("a city's lie, in the hands of three scribes", PW / 2, 230, 24, C["red"])
        num, form = ERAS[e]
        x = {1: 175, 2: PW / 2, 3: PW - 205}[e]
        if e != 2:
            page += word(num, x, 140, 24, C["red"]) + word(form, x, 190, 42, C["ink"])
        else:
            page += word("II  ·  phēgos", PW / 2, 81, 27, C["paper"])
        shots[e] = paint(e, [masa.desk(2, 80 + e, ()), G("sayfa", page, place(OX, OY, 0, SC))], BW, BH, "banner", 90 + e)
    yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
    cuts = [OX + 350 * SC, OX + (PW - 350) * SC]
    tilt = 0.12
    b1 = xx > cuts[0] + (yy - BH / 2) * tilt
    b2 = xx > cuts[1] - (yy - BH / 2) * tilt
    img = compose(shots, b1.astype(int) + b2.astype(int), BW, BH)
    d = ImageDraw.Draw(img)
    seam(d, (cuts[0] - BH / 2 * tilt, 0), (cuts[0] + BH / 2 * tilt, BH))
    seam(d, (cuts[1] + BH / 2 * tilt, 0), (cuts[1] - BH / 2 * tilt, BH))
    img.save(OUT / "banner.png")
    img.resize((960, 240), Image.LANCZOS).save(OUT / "banner_960.png")


if __name__ == "__main__":
    import sys
    if "banner" not in sys.argv:
        cover()
    banner()
    print("ok")
