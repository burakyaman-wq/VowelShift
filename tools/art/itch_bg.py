"""Page background for itch.io: the era I desk, wide. -> assets/art/style/itch_bg.jpg"""
import motif as m, masa, nakkas as nk
from PIL import Image
from motif import ROOT
OUT = ROOT / "assets/art/style"
W, H = 1920, 1080
m.use_era(1)
masa.W, masa.H, masa.X1, masa.Y1 = W, H, W - 58, H - 52
st = m.ERAS[1]
how = dict(st["how"]); how["wobble"] = how.get("wobble", 1.0) * 0.55; how["spill"] = how.get("spill", 0.0) * 0.45
p = OUT / "_bg.png"
nk.paint_png(masa.desk_plate(), W, H, p, seed=5, line=st["line"], age=0.8, **how)
Image.open(p).convert("RGB").save(OUT / "itch_bg.jpg", quality=86)
p.unlink()
print("ok")
