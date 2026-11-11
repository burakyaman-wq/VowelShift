"""Collect the book's images into assets/art/bible/web/img as JPEG, crop the
sleeve details, and write each <img>'s real width/height into index.html.

python3 tools/art/build_bible_web.py
"""
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BIBLE = ROOT / "assets/art/bible"
WEB = BIBLE / "web"
IMG = WEB / "img"

RENDERS = ["menu", "era1", "era2", "era3", "era4", "final", "read1", "read2", "read3", "tray"]
SHEETS = ["sheet_materials", "sheet_ornament", "sheet_typography", "sheet_tiles", "sheet_fabrics"]


def save_jpg(im, name, max_w=1600):
    im = im.convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(IMG / f"{name}.jpg", quality=86, optimize=True, progressive=True)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    for n in RENDERS:
        p = BIBLE / f"{n}.png"
        if p.exists():
            save_jpg(Image.open(p), n)
    for n in SHEETS:
        save_jpg(Image.open(BIBLE / f"{n}.png"), n, 1800)
    for k, era in enumerate(("era1", "era2", "era3"), start=1):
        p = BIBLE / f"{era}.png"
        if p.exists():
            im = Image.open(p)
            w, h = im.size
            crop = im.crop((int(w * 0.52), int(h * 0.10), w, int(h * 0.10) + int(w * 0.48 / 1.6)))
            save_jpg(crop.resize((800, 500), Image.LANCZOS), f"sleeve{k}")
    html = (WEB / "index.html").read_text()

    def fix(m):
        src = m.group(2)
        p = WEB / src
        if not p.exists():
            return m.group(0)
        w, h = Image.open(p).size
        tag = re.sub(r'\swidth="\d+"', "", m.group(0))
        tag = re.sub(r'\sheight="\d+"', "", tag)
        return tag.replace(f'src="{src}"', f'src="{src}" width="{w}" height="{h}"')

    html = re.sub(r'<img([^>]*?)src="(img/[^"]+)"([^>]*)>', fix, html)
    (WEB / "index.html").write_text(html)
    total = sum(f.stat().st_size for f in WEB.rglob("*") if f.is_file())
    print(f"web folder {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
