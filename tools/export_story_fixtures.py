"""Expected rumour/epilogue texts for two scripted playthroughs (from the prototype)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "prototype"))
import content as C  # noqa: E402

A = {"copy2": "Mīros Mīrom ageti. Mīros nēkos.", "answers": {"2": "Sürgün edildi", "4": C.DOC4_SUBJECT_FIRST},
     "notes": {"2": "sürgün, ölü değil", "4": "Sırayı anlam için değiştirdim."}, "copy4": "Mīro rīgo Mīro nēko şeneti."}
B = {"copy2": "Mīros Mīrom ageti. Mīros nīkos.", "answers": {"2": "Sürgün edildi", "4": "Yazıdan anlaşılmıyor"},
     "notes": {}, "copy4": "Mīro nēko Mīro rīgo şeneti."}
out = {}
for name, s in (("A", A), ("B", B)):
    out[name] = {"rumour": C.reaction_doc3(s["copy2"], s["answers"]["2"]).replace("*", "*"),
                 "epilogue": C.epilogue(s["copy2"], s["answers"], s["notes"], s["copy4"]), **s}
p = ROOT / "tests/fixtures/story_fixtures.json"
p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(out["B"]["rumour"]); print(out["A"]["epilogue"][:120])
