#!/usr/bin/env python3
"""MASA — kâğıt prototipin yöneticisi (oyuncu ajanlar için), sürüm 2.

Kullanım:
  python3 masa.py <oyuncu> basla
  python3 masa.py <oyuncu> durum
  python3 masa.py <oyuncu> kural "<eski> -> <yeni>" <eskiKelime:yeniKelime> <eskiKelime:yeniKelime>
  python3 masa.py <oyuncu> kopyala "<kart adları, sırayla, örn. sert,teklesme>"
  python3 masa.py <oyuncu> cevap <seçenek numarası>

Uzun ünlüleri yazamıyorsan çift harf kullanabilirsin: aa=ā, ee=ē, ii=ī, oo=ō, uu=ū.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import content as C  # noqa: E402

LOGS = HERE / "logs"
LOGS.mkdir(exist_ok=True)
LONG = {"aa": "ā", "ee": "ē", "ii": "ī", "oo": "ō", "uu": "ū"}


def norm(x):
    x = unicodedata.normalize("NFC", x.strip())
    for k, v in LONG.items():
        x = x.replace(k, v)
    return x


def strip_macrons(x):
    return "".join(ch for ch in unicodedata.normalize("NFD", x) if unicodedata.category(ch) != "Mn")


def words_of(text):
    return [w.strip(".,").lower() for w in text.split() if w.strip(".,")]


def load(p):
    f = LOGS / f"{p}.json"
    return json.loads(f.read_text()) if f.exists() else None


def save(p, st):
    (LOGS / f"{p}.json").write_text(json.dumps(st, ensure_ascii=False, indent=1))


def visible_old(st, d):
    """Old forms the player can actually see: this document, plus the previous era's dictionary."""
    s = set(words_of(d["old"]))
    if d["era"] >= 2:
        for f, _ in C.LEX1:
            s |= C.inflections(f)
    return s


def visible_new(st, d):
    """Current-era forms the player has actually seen or heard."""
    s = set()
    if d["era"] == 1:
        for f, _ in C.LEX1:
            s |= C.inflections(f)
    for doc in C.DOCS:
        if doc["era"] == d["era"] and doc["no"] <= d["no"]:
            for h in doc["heard"]:
                s |= C.inflections(h)
    return s


def show_doc(st, d):
    print(f"\n=== Belge {d['no']} · Çağ {d['era']} · {d['title']} ===")
    if d["no"] == 2:
        print("(Yüz yıl geçti. Artık Çağ 2'desin: materials/sozluk_cag2.md dosyasını aç. Bu belgedeki metin Çağ 1 yazısıyla.)")
    if d["no"] == 3:
        print("Kapıda bir söylenti: " + C.reaction_doc3(st.get("copies", {}).get("2", ""), st.get("answers", {}).get("2")).replace("*", ""))
    print(f"{d['who']}: “{d['says']}”")
    print(f"\nMasadaki eski metin:\n    {d['old']}\n")
    print("Eski metni sözlükle eşleştir, ses değişimlerini kanıtla (kural), sonra kart sırasını ver (kopyala). Kopyayı masa yazar.")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    p, cmd, args = sys.argv[1], sys.argv[2], sys.argv[3:]
    st = load(p)
    if cmd == "basla":
        st = {"doc": 1, "cards": [], "log": [], "phase": "oku", "copies": {}, "answers": {}}
        save(p, st)
        show_doc(st, C.DOCS[0])
        return
    if not st:
        print("Önce: basla")
        return
    done = st["doc"] > len(C.DOCS)
    d = None if done else C.DOCS[st["doc"] - 1]

    def log(**k):
        st["log"].append({"doc": st["doc"], **k})

    if cmd == "durum":
        if done:
            print("Test bitti.")
            return
        names = [C.CARDS[c]["key"] for c in st["cards"]]
        print(f"Belge {st['doc']}, kartların: {', '.join(names) or 'yok'}, aşama: {st['phase']}")
        show_doc(st, d)
        return
    if done:
        print("Test bitti. Teşekkürler.")
        return

    if cmd == "kural":
        if len(args) < 3:
            print("Kural için değişimi ve İKİ örnek çifti ver: kural \"gh -> kh\" eski:yeni eski:yeni")
            return
        m = re.match(r"\s*(\S+)\s*->\s*(\S+)\s*", norm(args[0]))
        if not m:
            print("Biçim: \"x -> y\"")
            return
        frm, to = m.group(1), m.group(2)
        pairs = [tuple(norm(a).lower().strip(".,").split(":", 1)) for a in args[1:3] if ":" in a]
        cur = C.era_ids(d["era"])
        new_ids = cur[len(C.era_ids(d["era"] - 1)):]
        hit = near = None
        for rid in new_ids:
            for pat, rep in C.R[rid]["subs"]:
                if pat == frm and rep == to:
                    hit = rid
                elif strip_macrons(pat) == strip_macrons(frm) and strip_macrons(rep) == strip_macrons(to):
                    near = rid
        vo, vn = visible_old(st, d), visible_new(st, d)
        problems = []
        if len(pairs) < 2 or len({a for a, _ in pairs}) < 2:
            problems.append("iki farklı örnek gerekiyor")
        for old, new in pairs:
            if old not in vo:
                problems.append(f"'{old}' masada görünen eski bir kelime değil")
            elif new not in vn:
                problems.append(f"'{new}' henüz bu çağda duyduğun ya da sözlüğünde olan bir kelime değil")
            elif frm not in old or C.apply(new_ids, old) != new:
                problems.append(f"'{old} → {new}' bu değişimi göstermiyor")
        if hit and not problems:
            if hit not in st["cards"]:
                st["cards"].append(hit)
            c = C.CARDS[hit]
            print(f"Masa kartı verdi: «{c['name']}» ({c['rule']}). Kart adı: {c['key']}")
            log(action="kural", rule=args[0], pairs=args[1:3], result="kart", card=hit)
        else:
            if not hit and near:
                print("Neredeyse: uzun ünlü işaretlerine (ā ē ī ō ū) dikkat et.")
            elif not hit:
                print("Masa bu ses değişimini onaylamadı.")
            for pr in problems:
                print(f"  - {pr}")
            log(action="kural", rule=args[0], pairs=args[1:3], result="red", problems=problems)
        save(p, st)
        return

    if cmd == "kopyala":
        if st["phase"] != "oku":
            print("Bu belge zaten kopyalandı; cevap ver.")
            return
        keys = [k.strip() for k in norm(args[0]).split(",") if k.strip()] if args else []
        unknown = [k for k in keys if k not in C.KEY2ID or C.KEY2ID[k] not in st["cards"]]
        if unknown:
            print(f"Bu kartlar sende yok: {unknown}")
            return
        order = [C.KEY2ID[k] for k in keys]
        copy = C.apply_text(order, d["old"])
        real = C.real_words(d["era"])
        res = [(w, w in real) for w in words_of(copy)]
        print(f"Masa yazdı:  {copy}")
        bad = [w for w, ok in res if not ok]
        log(action="kopyala", order=keys, copy=copy, accepted=not bad, rejected=bad)
        if bad:
            print(f"Masa bu kelimeleri bu çağın dilinde tanımıyor: {', '.join(bad)}. Kopya rafa konmadı.")
        else:
            st["phase"] = "cevap"
            st["copies"][str(d["no"])] = copy
            print(f"\nKopya rafa kondu. {d['who']} soruyor: {d['ask']}")
            for i, o in enumerate(d["options"], 1):
                print(f"  {i}. {o}")
            print("Cevap: cevap <numara>")
        save(p, st)
        return

    if cmd == "cevap":
        if st["phase"] != "cevap":
            print("Önce belgeyi kopyala.")
            return
        try:
            choice = d["options"][int(args[0]) - 1]
        except (IndexError, ValueError):
            print(f"1 ile {len(d['options'])} arasında bir numara ver.")
            return
        st["answers"][str(d["no"])] = choice
        log(action="cevap", choice=choice)
        print(f"{d['who']} cevabını not etti: “{choice}”.")
        st["doc"] += 1
        st["phase"] = "oku"
        save(p, st)
        if st["doc"] <= len(C.DOCS):
            show_doc(st, C.DOCS[st["doc"] - 1])
        else:
            print("\n=== Son ===")
            print(C.epilogue(st["copies"].get("2", "")))
            print("\n=== Test bitti. ===")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
