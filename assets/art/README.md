# Art

The game's pictures are drawn in code as miniatures in four historical schools. The rules are in
`STYLE.md`; the tools are in `tools/art/` (`nakkas.py`, `motif.py`, `masa.py`, `kagit.py`, `karo.py`,
`minyatur.py`).

| Folder | What |
|---|---|
| `sprites/` | What the game loads. Second-era sprites carry plain names, the others `_cagN`. |
| `style/` | Screens from the game for looking at (`cagN_masa.png`, `cagN_okuma.png`, `dort_cag.png`), contact sheets, and the layered SVG of every sprite in `sprites_src/`. Not imported by Godot. |
| `AI_LOG.md` | Every asset made with an image generator, for the disclosure. Empty so far. |
| `tex/`, `bible/`, `concept/` | Earlier directions (flat v1, the Blender look). Superseded; kept for the record. Their tools are `tex_*.py`, `desk_scene.py`, `bible_sheets.py`, `build_bible_web.py`. |

The scribe's hand is `assets/fonts/Katip-Regular.ttf`, built by `tools/art/katip_font.py`
from Aref Ruqaa's Latin glyphs (SIL OFL 1.1, see `assets/fonts/OFL.txt`).

## Rebuild

```
pip install --break-system-packages numpy scipy pillow fonttools     # and librsvg (rsvg-convert)
cd tools/art && python3 minyatur.py --sheet
```
