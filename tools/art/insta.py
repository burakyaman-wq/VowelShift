"""Instagram post, 1080 x 1350 (painted at 2x): the cover idea, portrait, with a call to play.
    python3 tools/art/insta.py -> assets/art/style/insta_post.png"""
import numpy as np
from PIL import Image, ImageDraw
import kagit, masa, motif as m
from motif import C, ROOT
from nakkas import G, place
from kapak import word, paint, compose, seam, ERAS

OUT = ROOT / "assets/art/style"
CW, CH, PW, PH, SC = 1080, 1350, 640, 840, 1.5
OX, OY = (CW - PW * SC) / 2, (CH - PH * SC) / 2
rows = {1: 300, 2: 455, 3: 610}
shots = {}
for e in (1, 2, 3):
    m.use_era(e)
    masa.W, masa.H, masa.X1, masa.Y1 = CW, CH, CW - 40, CH - 40
    page = kagit.document_page(PW, PH, True, 140 + e)
    num, form = ERAS[e]
    page += word("Vowel Shift", PW / 2, 81.5, 31, C["paper"])
    page += word("one word, three eras", PW / 2, 175, 26, C["red"])
    page += word(num, 120, rows[e] - 6, 34, C["red"])
    page += word(form, 365, rows[e], 88, C["ink"])
    page += word("Game Off 2026 · play free in your browser", PW / 2, 712, 22, C["ink"])
    page += word("itch.io · Yoru Creative Studio", PW / 2, 748, 20, C["red"])
    shots[e] = paint(e, [masa.desk(4, 150 + e, ()), G("sayfa", page, place(OX, OY, 0, SC))], CW, CH, "insta", 160 + e)
yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
cuts = [OY + 378 * SC, OY + 533 * SC]
tilt = 0.04
b1 = yy > cuts[0] + (xx - CW / 2) * tilt
b2 = yy > cuts[1] - (xx - CW / 2) * tilt
img = compose(shots, b1.astype(int) + b2.astype(int), CW, CH)
d = ImageDraw.Draw(img)
seam(d, (0, cuts[0] - CW / 2 * tilt), (CW, cuts[0] + CW / 2 * tilt))
seam(d, (0, cuts[1] + CW / 2 * tilt), (CW, cuts[1] - CW / 2 * tilt))
img.save(OUT / "insta_post.png")
print("ok")
