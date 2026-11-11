"""Derive every lexicon form through the eras and report what the rules do.

Usage: python3 tools/simulate.py [--markdown]

Prints, per word, its root form at the end of each era; then
  * order-sensitive rule pairs (swapping them changes some output),
  * forms of DIFFERENT words that merge in each era (puzzle risks),
  * case/number distinctions lost per era (intended erosion).
"""
import json
import re
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDS = json.loads((ROOT / "data/words/words.json").read_text(encoding="utf-8"))["words"]
RULESET = json.loads((ROOT / "data/rules/rules.json").read_text(encoding="utf-8"))


def compile_rules(ruleset):
    classes = ruleset["classes"]
    out = []
    for r in ruleset["rules"]:
        subs = []
        for pat, rep in r["subs"]:
            for name, cls in classes.items():
                pat = pat.replace("{" + name + "}", cls)
            subs.append((re.compile(pat), rep))
        out.append({**r, "compiled": subs})
    return out


RULES = compile_rules(RULESET)
ERAS = sorted({r["era"] for r in RULES})


def apply_rule(word, rule):
    # Subs inside one rule apply simultaneously (one pass each, no feeding).
    for rx, rep in rule["compiled"]:
        word = rx.sub(rep, word)
    return word


def apply_chain(word, rules):
    for r in rules:
        word = apply_rule(word, r)
    return word


def all_forms():
    for w in WORDS:
        for tag, form in w["forms"].items():
            yield w["root"], tag, form


def rules_upto(era, order=None):
    seq = order or RULES
    return [r for r in seq if r["era"] <= era]


def main():
    md = "--markdown" in sys.argv
    header = ["kök"] + [f"Çağ {e}" for e in ERAS]
    if md:
        print("| " + " | ".join(header) + " |")
        print("|" + "---|" * len(header))
    for w in WORDS:
        row = [w["root"]] + [apply_chain(w["root"], rules_upto(e)) for e in ERAS]
        print(("| " + " | ".join(row) + " |") if md else "  ".join(f"{c:<12}" for c in row))

    print("\n## Sıraya duyarlı kural çiftleri")
    forms = list(all_forms())
    for a, b in combinations(RULES, 2):
        diffs = []
        for root, tag, f in forms:
            ab = apply_rule(apply_rule(f, a), b)
            ba = apply_rule(apply_rule(f, b), a)
            if ab != ba:
                diffs.append(f"{f}: {a['id']}→{b['id']} = {ab}, {b['id']}→{a['id']} = {ba}")
        if diffs:
            print(f"- {a['id']} ({a['name_tr']}) × {b['id']} ({b['name_tr']}): {len(diffs)} form, ör. {diffs[0]}")

    for e in ERAS:
        chain = rules_upto(e)
        by_out = {}
        for root, tag, f in forms:
            by_out.setdefault(apply_chain(f, chain), []).append((root, tag))
        cross = {o: s for o, s in by_out.items() if len({r for r, _ in s}) > 1}
        lost = {o: s for o, s in by_out.items() if len(s) > 1 and len({r for r, _ in s}) == 1}
        print(f"\n## Çağ {e}: farklı kelimeler birleşiyor ({len(cross)})")
        for o, s in sorted(cross.items()):
            print(f"- {o}: " + ", ".join(f"{r}:{t}" for r, t in s))
        print(f"Çağ {e}: aynı kelimenin hâl/sayı ayrımı kayboldu: {len(lost)} biçim")


if __name__ == "__main__":
    main()
