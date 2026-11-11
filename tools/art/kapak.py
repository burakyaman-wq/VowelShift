"""The cover: one word in four eras, each quarter painted by its own school.

    python3 tools/art/kapak.py   ->  assets/art/style/kapak.png (1260 x 1000) and kapak_630.png

The word is bhāgos, "book", as the rule engine carries it through the eras:
phāgos, phēgos, phēgo, fēg. The same page is painted four times and
quartered, so the title, the frame and the medallion change hands at the seams.
"""
import numpy as np
from PIL import Image, ImageDraw

import kagit
import masa
import motif as m
import nakkas as nk
from motif import C, ROOT, lobed, text, text_path
from nakkas import G, el, fill, place, stroke

CW, CH = 1260, 1000
PW, PH, SC = 700, 540, 1.6                 # the page, in its own units, and how much it is enlarged
OX, OY = (CW - PW * SC) / 2, (CH - PH * SC) / 2
MX, MY = 350, 322                          # where the four quarters meet, in page units
FORMS = {1: ("I", "phāgos", (186, 240)), 2: ("II", "phēgos", (514, 240)), 3: ("III", "phēgo", (186, 432)), 4: ("IV", "fēg", (514, 432))}
OUT = ROOT / "assets/art/style"


def word(s, x, y, size, color):
    """Large writing, laid as body colour so the reed's breath does not bend its marks."""
    d, _ = text_path(s, x, y, size, "middle")
    return [el("path", "paint", fill=color, d=d)]


def plate(e):
    m.use_era(e)
    masa.W, masa.H, masa.X1, masa.Y1 = CW, CH, CW - 58, CH - 52
    page = kagit.document_page(PW, PH, True, 40 + e)
    page += text("Ses Kayması", PW / 2, 81.5, 31, C["paper"], "middle")
    num, form, (x, y) = FORMS[e]
    page += word(num, x, y - 74, 26, C["red"])
    page += word(form, x, y, 74, C["ink"])
    return [masa.desk(3, 50 + e, ()), G("sayfa", page, place(OX, OY, 0, SC))]


def medallion():
    """Where the quarters meet: the word they all came from, on bare paper."""
    m.use_era(2)
    r = 104
    items = fill(lobed(r, r, 96, 12, 0.09), C["paper"], 2.2) + stroke(lobed(r, r, 84, 12, 0.09), 1.2, C["red"], closed=True)
    items += word("bhāgos", r, r + 14, 46, C["ink"]) + word("ata dil", r, r + 46, 19, C["red"])
    nk.paint_png(items, 2 * r, 2 * r, OUT / "_madalyon.png", seed=77, wobble=0.6, age=0.4)
    im = Image.open(OUT / "_madalyon.png").convert("RGBA")
    (OUT / "_madalyon.png").unlink()
    return im


def main():
    shots = {}
    for e in (1, 2, 3, 4):
        st = m.ERAS[e]
        how = dict(st["how"])                 # a steadier hand than in the game: the lettering has to read small
        how["wobble"] = how.get("wobble", 1.0) * 0.55
        how["spill"] = how.get("spill", 0.0) * 0.45
        shots[e] = nk.paint_png(plate(e), CW, CH, OUT / f"_kapak{e}.png", seed=60 + e, line=st["line"], age=0.8, **how)[..., :3]
        (OUT / f"_kapak{e}.png").unlink()
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
    cx, cy = OX + MX * SC, OY + MY * SC
    right = xx > cx + (yy - cy) * 0.105
    below = yy > cy - (xx - cx) * 0.035
    quarter = right.astype(int) + 2 * below.astype(int)
    out = np.zeros((CH, CW, 3), np.float32)
    for e in (1, 2, 3, 4):
        out[quarter == e - 1] = shots[e][quarter == e - 1]
    img = Image.fromarray((out * 255 + 0.5).astype(np.uint8))
    d = ImageDraw.Draw(img)
    v = [(cx + (0 - cy) * 0.105, 0), (cx + (CH - cy) * 0.105, CH)]
    h = [(0, cy + cx * 0.035), (CW, cy - (CW - cx) * 0.035)]
    for seam in (v, h):
        d.line(seam, fill=(42, 27, 20), width=6)
    for seam in (v, h):
        d.line(seam, fill=(236, 220, 185), width=2)
    med = medallion()
    img.paste(med, (int(cx - med.width / 2), int(cy - med.height / 2)), med)
    img.save(OUT / "kapak.png")
    img.resize((630, 500), Image.LANCZOS).save(OUT / "kapak_630.png")
    print(OUT / "kapak.png")


if __name__ == "__main__":
    main()
