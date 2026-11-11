"""Shared prototype content: used by paper/build.py and playtest/masa.py.

Forms are derived from the real rules (tools/simulate.py), so the
prototype can never drift from the simulator.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
_argv = sys.argv
sys.argv = [sys.argv[0]]
import simulate as S  # noqa: E402
sys.argv = _argv

R = {r["id"]: r for r in S.RULES}


def apply(ids, word):
    cap = word[:1].isupper()
    w = word.lower()
    for i in ids:
        w = S.apply_rule(w, R[i])
    return w[:1].upper() + w[1:] if cap else w


def apply_text(ids, text):
    out = []
    for tok in text.split():
        core, dot = tok.rstrip("."), tok.endswith(".")
        out.append(apply(ids, core) + ("." if dot else ""))
    return " ".join(out)


def era_ids(era):
    return [r["id"] for r in S.RULES if r["era"] <= era]


def real_words(era):
    """Every inflected form of every lexicon word, as written in that era."""
    ids = era_ids(era)
    return {apply(ids, f).lower() for w in S.WORDS for f in w["forms"].values()}


def inflections(form):
    """Forms the player can build from a known base with the grammar card."""
    f = form.lower()
    if f.endswith("os"):
        st = f[:-2]
        return {st + e for e in ("os", "om", "osyo", "es", "em", "esyo")}
    if f.endswith("eti"):
        return {f, f[:-3] + "e"}
    return {f}


# Cards: plain names, no numbers (numbers leaked the hidden order).
CARDS = {
    "R1": {"key": "sert", "name": "Sert ünsüzler", "rule": "bh → ph · dh → th · gh → kh"},
    "R2": {"key": "teklesme", "name": "Çift ünlüler tekleşir", "rule": "ei → ī · eu → ū"},
    "R3": {"key": "yukselme", "name": "ē yükselir", "rule": "ē → ī"},
    "R4": {"key": "kayma", "name": "ā kayar", "rule": "ā → ē"},
}
KEY2ID = {c["key"]: rid for rid, c in CARDS.items()}

# Era-1 dictionary (the player's own era). Era-0 roots → era-1 forms.
LEX_ROOTS = [
    ("Meiros", "kurucu, büyük kardeş"), ("Mēros", "kurucu, küçük kardeş"), ("deiwos", "tanrı"),
    ("ghewos", "adak, sunu"), ("dōneti", "verir"), ("emeti", "alır"), ("ageti", "kovar, sürer"),
    ("ghrebheti", "yazar"), ("nākos", "sürgün"), ("nēkos", "ölü"), ("āgros", "tarla"),
    ("grānos", "tahıl"), ("rēgos", "bey, kral"), ("dhētos", "borç"), ("mātēros", "anne"),
    ("leukos", "ışık, kandil"), ("dhūmos", "duman"), ("bhāgos", "kitap"),
]
LEX1 = [(apply(era_ids(1), r), m) for r, m in LEX_ROOTS]

DOCS = [
    {"no": 1, "era": 1, "title": "Temel taşı tableti",
     "old": "Meiros deiwosyo ghewom dōneti. Meiros bhāgom ghrebheti. Mēros nākos.",
     "who": "Rahibe, tapınaktan",
     "says": "Tapınağın temelini kazarken bu tablet çıktı. Bir *khewos* kaydı olmalı, kurucunun *phāgos*'undan da söz ediyor sanırım. Yeni yazıyla kopyala ki rafa koyabilelim.",
     "heard": ["khewos", "phāgos"],
     "ask": "Adağı kim sundu?",
     "options": ["Büyük kardeş Mīros", "Küçük kardeş Mēros", "Tanrının kendisi", "Rahibe"]},
    {"no": 2, "era": 2, "title": "Kurucuların kaydı",
     "old": "Mīros Mērom ageti. Mēros nākos.",
     "who": "Saray görevlisi",
     "says": "*Rīgos* kurucuların kaydını istiyor. Eski defterlerde *grānos* yazıyor, biz artık *grēnos* diyoruz; tarlalara da *ēgros* diyoruz, ambarın *thītos*'u kabardı. Kopyan bugünün diliyle olmalı. Acele et, *rīgos* beklemez.",
     "heard": ["rīgos", "grēnos", "ēgros", "thītos"],
     "ask": "Kurucunun kardeşine ne oldu?",
     "options": ["Sürgün edildi", "Öldü", "Kral oldu", "Tahılını verdi"]},
    {"no": 3, "era": 2, "title": "Bir borç senedi",
     "old": "Mātēros Mīrosyo grānom emeti.",
     "who": "Tüccar kadın",
     "says": "Bu senet annemden kaldı. Ben ona *mētīros* derdim, siz eski yazıda başka türlü yazıyorsunuz. Tahıl kimden kime geçmiş, bilmem lazım.",
     "heard": ["mētīros"],
     "ask": "Tahılı kim aldı?",
     "options": ["Annem aldı", "Mīros aldı", "Tüccar aldı", "Tanrıya adandı"]},
]
for _d in DOCS:
    _prev = era_ids(_d["era"] - 1)
    _cur = era_ids(_d["era"])
    _new = _cur[len(_prev):]
    _d["right"] = apply_text(_new, _d["old"])
    _d["wrong"] = apply_text(list(reversed(_new)), _d["old"])

KEY_WORD_RIGHT = "nēkos"  # doc 2, R3 → R4: sürgün
KEY_WORD_WRONG = "nīkos"  # doc 2, R4 → R3: reads as era-2 'ölü'


def reaction_doc3(copy2, answer2):
    """What the doc-3 requester has heard about the player's doc-2 copy."""
    says_dead = KEY_WORD_WRONG in copy2
    line = ("Sarayda senin kopyanı okudular: kurucunun kardeşi ölmüş. Mezarını arıyorlar."
            if says_dead else
            "Sarayda senin kopyanı okudular: kardeş sürgün edilmiş. Ama yaşlılar eski dille okuyor; onlara göre *nēkos* 'ölü' demek. Çarşıda kardeşin öldürüldüğü konuşuluyor.")
    if answer2 and ((says_dead and answer2.startswith("Sürgün")) or (not says_dead and answer2 == "Öldü")):
        line += " Görevliye başka, kâğıda başka yazmışsın; hangisine inanacaklarını bilmiyorlar."
    return line


def epilogue(copy2):
    if KEY_WORD_WRONG in copy2:
        return ("Yüz yıl sonra. Okullarda kurucunun kardeşinin öldüğü öğretiliyor; dayanak, senin rafa koyduğun kopya: "
                "'Mīros nīkos.' Temel taşındaki eski tablette ise 'Mēros nākos' yazıyordu: Mēros sürgündür. "
                "Kâğıt üstünde bir kardeşi sen öldürdün.")
    return ("Yüz yıl sonra. Saray kayıtları kardeşin sürgün edildiğini söylüyor; senin kopyan doğruydu: 'Mīros nēkos.' "
            "Ama eski dili bilenler aynı kelimeyi 'ölü' diye okudu ve söylenti kayıttan güçlü çıktı. "
            "Bugün herkes kardeşin öldürüldüğünü biliyor.")
