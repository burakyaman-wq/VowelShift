"""Sheets for the visual book: type specimen, ornament vocabulary, material
swatches, rule tiles in their states, sleeve fabrics.

python3 tools/art/bible_sheets.py   ->  assets/art/bible/sheet_*.png
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tex_core import INK, KATIP, OUT as TEX, apply_ink, paper, save_rgb, text_mask

ROOT = TEX.parents[2]
BIBLE = ROOT / "assets/art/bible"
BG = (24, 19, 15)
FG = (233, 220, 194)
DIM = (160, 140, 112)
GOLD = (201, 164, 84)


def label_font(size):
    return ImageFont.truetype(str(KATIP), size)


def tex(name):
    return Image.open(TEX / name).convert("RGB")


def typography():
    w, h = 1800, 1320
    img, _ = paper(w, h, 5, tone=(234, 222, 192), age=0.35, laid=False)
    lines = [
        (150, "Mīros dīwosyo khewom dōneti.", 120),
        (360, "Mīrom nēkom Mīros rīgos kheneti.", 84),
        (540, "ā ē ī ō ū · Ā Ē Ī Ō Ū · ş ç ğ ı İ ö ü â î û", 64),
        (720, "bh → ph · ē → ī · -s → ∅", 64),
    ]
    cov = np.zeros((h, w), np.float32)
    for y, t, s in lines:
        cov = np.maximum(cov, text_mask(w, h, [t], s, (110, y), 0, align="left", seed=y, wobble=0.7))
    img, _ = apply_ink(img, cov, INK, 3)
    note = text_mask(w, h, ["Önce gelen yapandır."], 44, (110, 880), 0, align="left", seed=9, wobble=1.0)
    img, _ = apply_ink(img, note, (110, 50, 34), 4, density=0.85)
    # the red-vowel reading aid: long vowels rubricated
    word = "Mīros nēkos."
    f = ImageFont.truetype(str(KATIP), 84)
    x = 110
    red = np.zeros((h, w), np.float32)
    blk = np.zeros((h, w), np.float32)
    for i, ch in enumerate(word):
        m = text_mask(w, h, [ch], 84, (110 + f.getlength(word[:i]), 1090), 0, align="left", seed=7, wobble=0.0)
        if ch in "āēīōū":
            red = np.maximum(red, m)
        else:
            blk = np.maximum(blk, m)
    img, _ = apply_ink(img, blk, INK, 5)
    img, _ = apply_ink(img, red, (156, 44, 30), 6)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(out)
    small = ImageFont.truetype("/tmp/ttf/ebg_it.ttf", 30)
    for y, t in ((205, "belge metni · 120"), (395, "belge metni · 84"), (570, "uzun ünlüler ve Türkçe harfler"),
                 (750, "kural karosu işaretleri"), (905, "oyuncunun kenar notu (kahverengi mürekkep)"),
                 (1120, "erişilebilirlik seçeneği: uzun ünlüler kırmızı mürekkeple")):
        d.text((112, y), t, font=small, fill=(120, 96, 70))
    out.save(BIBLE / "sheet_typography.png")


def crop(img, box, size):
    return img.crop(box).resize(size, Image.LANCZOS)


def ornament():
    page = tex("era2_illum_albedo.png")
    cover = tex("menu_cover_albedo.png")
    items = [
        ("Bulut kartuş ve başlık", crop(page, (560, 600, 1240, 840), (520, 184))),
        ("Helezon zemin", crop(page, (430, 590, 600, 647), (520, 174))),
        ("Bulut içinde satır", crop(page, (400, 1010, 1100, 1230), (520, 164))),
        ("Ogee madalyon", crop(page, (270, 880, 400, 1620), (130, 740)).rotate(90, expand=True).resize((520, 92))),
        ("Zencerek ve tığ", crop(page, (190, 470, 760, 600), (520, 118))),
        ("Durak gülü", crop(page, (1232, 1078, 1328, 1142), (270, 180))),
        ("Saray mührü", crop(page, (1270, 2140, 1490, 2360), (220, 220))),
        ("Cilt şemsesi", crop(cover, (360, 380, 1040, 1620), (230, 420))),
    ]
    w, h = 1700, 1080
    out = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(out)
    f = label_font(34)
    pos = [(40, 40), (40, 300), (40, 540), (40, 770), (600, 40), (600, 260), (900, 260), (1200, 40)]
    for (name, im), (x, y) in zip(items, pos):
        out.paste(im, (x, y + 44))
        d.text((x, y), name, font=f, fill=GOLD)
    out.save(BIBLE / "sheet_ornament.png")


def materials():
    sw = [
        ("Kil tablet", "era1_tablet_albedo.png", (300, 300, 560, 560)),
        ("Parşömen", "era1_parchment_albedo.png", (100, 1300, 360, 1560)),
        ("Aharlı kâğıt", "era2_copy_albedo.png", (60, 1300, 320, 1560)),
        ("Varak altın", "era2_illum_albedo.png", (700, 1300, 960, 1560)),
        ("Lapis", "era2_illum_albedo.png", (720, 650, 830, 760)),
        ("Firuze", "era2_illum_albedo.png", (285, 1180, 395, 1290)),
        ("Yanık kenar", "era3_burnt_albedo.png", (1080, 1500, 1340, 1760)),
        ("Çini sır", "tile_R3_blank_albedo.png", (90, 420, 350, 680)),
        ("Cilt derisi", "menu_cover_albedo.png", (180, 820, 350, 990)),
        ("Ebru", "era4_ebru_albedo.png", (0, 0, 400, 400)),
        ("Keten", "sleeve_linen_albedo.png", (0, 0, 400, 400)),
        ("Kemha", "sleeve_kemha_albedo.png", (0, 0, 400, 400)),
        ("Keçe", "sleeve_felt_albedo.png", (0, 0, 400, 400)),
        ("Mühür mumu", "era2_wax_albedo.png", (120, 120, 392, 392)),
    ]
    cols, cell = 7, 236
    w, h = cols * cell + 20, 2 * (cell + 60) + 20
    out = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(out)
    f = label_font(28)
    for i, (name, fn, box) in enumerate(sw):
        x, y = 10 + (i % cols) * cell, 10 + (i // cols) * (cell + 60)
        out.paste(crop(tex(fn), box, (cell - 16, cell - 16)), (x + 8, y + 8))
        d.text((x + 10, y + cell + 2), name, font=f, fill=FG)
    out.save(BIBLE / "sheet_materials.png")


def tiles():
    states = [("tile_R3_blank", "boş: henüz kanıt yok"), ("tile_R1_partial", "kısmi: bir eşleşme kanıtlandı"),
              ("tile_R1", "tam"), ("tile_R2_worn", "miras: önceki çağdan"), ("tile_R6_scorched", "yangından kalan")]
    cw = 300
    out = Image.new("RGB", (len(states) * cw + 20, 520), BG)
    d = ImageDraw.Draw(out)
    f = ImageFont.truetype("/tmp/ttf/ebg_it.ttf", 24)
    for i, (fn, lab) in enumerate(states):
        im = tex(f"{fn}_albedo.png").resize((270, 360), Image.LANCZOS)
        out.paste(im, (10 + i * cw + 15, 20))
        d.text((10 + i * cw + 15, 400), lab, font=f, fill=FG)
    out.save(BIBLE / "sheet_tiles.png")


def fabrics():
    items = [("Rahibe · keten, dokuma kenar", "sleeve_linen_albedo.png"), ("Saray görevlisi · kemha, çintemani", "sleeve_kemha_albedo.png"),
             ("Dağlı elçi · keçe, işlemeli kenar", "sleeve_felt_albedo.png")]
    out = Image.new("RGB", (3 * 420 + 20, 470), BG)
    d = ImageDraw.Draw(out)
    f = ImageFont.truetype("/tmp/ttf/ebg_it.ttf", 24)
    for i, (lab, fn) in enumerate(items):
        out.paste(tex(fn).crop((0, 0, 700, 700)).resize((400, 400), Image.LANCZOS), (10 + i * 420, 10))
        d.text((12 + i * 420, 420), lab, font=f, fill=FG)
    out.save(BIBLE / "sheet_fabrics.png")


if __name__ == "__main__":
    BIBLE.mkdir(parents=True, exist_ok=True)
    typography()
    ornament()
    materials()
    tiles()
    fabrics()
    print("sheets done")
