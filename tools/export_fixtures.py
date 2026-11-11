"""Export golden fixtures for the Godot rule engine tests.

Writes tests/fixtures/rule_fixtures.json: every lexicon form at every era
(canonical order), plus the order-swap cases the game relies on.
Usage: python3 tools/export_fixtures.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.argv = [sys.argv[0]]
sys.path.insert(0, str(ROOT / "tools"))
import simulate as S  # noqa: E402

R = {r["id"]: r for r in S.RULES}


def chain(ids, w):
    return S.apply_chain(w, [R[i] for i in ids])


forms = []
for w in S.WORDS:
    for tag, f in w["forms"].items():
        forms.append({"form": f, "eras": {str(e): S.apply_chain(f, S.rules_upto(e)) for e in S.ERAS}})

swaps = [
    {"word": "nākos", "order": ["R1", "R2", "R3", "R4"], "expect": "nēkos"},
    {"word": "nākos", "order": ["R1", "R2", "R4", "R3"], "expect": "nīkos"},
    {"word": "ghesros", "order": ["R1", "R6"], "expect": "şesros"},
    {"word": "ghesros", "order": ["R6", "R1"], "expect": "khesros"},
    {"word": "domos", "order": ["R5", "R8"], "expect": "dom"},
    {"word": "domos", "order": ["R8", "R5"], "expect": "domo"},
    {"word": "Kerdāgros", "order": [r["id"] for r in S.RULES], "expect": "Çerdēgro"},
]
for s in swaps:
    got = chain(s["order"], s["word"])
    assert got == s["expect"], (s, got)

out = ROOT / "tests/fixtures/rule_fixtures.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"forms": forms, "swaps": swaps}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"{len(forms)} forms, {len(swaps)} swap cases -> {out.relative_to(ROOT)}")
