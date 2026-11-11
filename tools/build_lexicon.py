"""Build data/words/words.json from data/words/lexicon.csv and report clashes.

Usage: python3 tools/build_lexicon.py [lexicon.csv] [words.json]

Nouns: root ends in -os. Paradigm: o-vowel = singular, e-vowel = plural.
Verbs: root ends in -eti (3sg). Imperative = stem + e.
"""
import csv
import json
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/words/lexicon.csv"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data/words/words.json"

NOUN_ENDINGS = {
    "nom_sg": "os", "acc_sg": "om", "gen_sg": "osyo",
    "nom_pl": "es", "acc_pl": "em", "gen_pl": "esyo",
}
VERB_ENDINGS = {"3sg": "eti", "imp": "e"}

# Digraphs count as one sound so distances reflect what the player hears.
DIGRAPHS = ["bh", "dh", "gh", "kw"]


def segments(word):
    out, i = [], 0
    while i < len(word):
        pair = word[i:i + 2]
        if pair in DIGRAPHS:
            out.append(pair)
            i += 2
        else:
            out.append(word[i])
            i += 1
    return out


def distance(a, b):
    a, b = segments(a), segments(b)
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def paradigm(root, pos):
    if pos == "noun":
        if not root.endswith("os"):
            raise ValueError(f"noun '{root}' must end in -os")
        stem = root[:-2]
        return stem, {k: stem + v for k, v in NOUN_ENDINGS.items()}
    if pos == "verb":
        if not root.endswith("eti"):
            raise ValueError(f"verb '{root}' must end in -eti")
        stem = root[:-3]
        return stem, {k: stem + v for k, v in VERB_ENDINGS.items()}
    raise ValueError(f"unknown pos '{pos}' for '{root}'")


def main():
    with SRC.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    words, forms = [], {}
    for r in rows:
        stem, para = paradigm(r["root"], r["pos"])
        words.append({
            "id": int(r["id"]), "root": r["root"], "stem": stem,
            "meaning_tr": r["meaning"], "pos": r["pos"], "domain": r["domain"],
            "etymon": r["etymon"], "forms": para,
        })
        for tag, form in para.items():
            forms.setdefault(form, []).append(f"{r['root']}:{tag}")

    OUT.write_text(json.dumps({"version": 1, "words": words}, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"{len(words)} words -> {OUT.relative_to(ROOT)}")

    homophones = {f: t for f, t in forms.items() if len(t) > 1}
    print(f"\nIdentical forms already in era 0: {len(homophones)}")
    for f, t in sorted(homophones.items()):
        print(f"  {f}: {', '.join(t)}")

    print("\nStems one sound apart (likely to merge after a shift):")
    stems = [(w["root"], w["stem"]) for w in words]
    near = [(a, b, distance(sa, sb)) for (a, sa), (b, sb) in combinations(stems, 2)]
    for a, b, d in sorted(near, key=lambda x: x[2]):
        if d <= 1:
            print(f"  {a} ~ {b}")

    inventory = sorted({s for w in words for f in w["forms"].values() for s in segments(f)})
    print(f"\nSound inventory ({len(inventory)}): {' '.join(inventory)}")


if __name__ == "__main__":
    main()
