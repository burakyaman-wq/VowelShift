# Art

Everything here is made in code, in Blender, or (later) cut from CC0 museum scans.
No generated imagery. The visual book (`bible/web/index.html`) explains the rules.

| Folder | What | Made by |
|---|---|---|
| `tex/` | Document, tile, cover, fabric and desk-wear textures (albedo / rough / height / alpha / metal) | `tools/art/tex_illum.py`, `tex_docs.py`, `tex_props.py` |
| `bible/` | Renders and sheets for the visual book (PNG renders are not committed) | `tools/art/desk_scene.py`, `bible_sheets.py` |
| `bible/web/` | The visual book page and its JPEGs | `tools/art/build_bible_web.py` |
| `concept/` | Earlier look-dev (v1 rejected, v2 superseded) | |

The scribe's hand is `assets/fonts/Katip-Regular.ttf`, built by `tools/art/katip_font.py`
from Aref Ruqaa's Latin glyphs (SIL OFL 1.1, see `assets/fonts/OFL.txt`).

## Rebuild

```
pip install --break-system-packages bpy==5.3.0 scikit-image fonttools
python3 tools/art/katip_font.py
cd tools/art && python3 tex_illum.py && python3 tex_docs.py && python3 tex_props.py
python3 desk_scene.py era2 --res 1600 900 --samples 40      # shots: menu era1-4 final read1-3 tray
python3 bible_sheets.py && python3 build_bible_web.py
```

Renders take about 3.5 minutes per shot on two CPU cores.
