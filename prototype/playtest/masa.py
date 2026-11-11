#!/usr/bin/env python3
"""MASA — kâğıt prototipin yöneticisi (oyuncu ajanlar için).

Kullanım:
  python3 masa.py <oyuncu> basla
  python3 masa.py <oyuncu> durum
  python3 masa.py <oyuncu> kural "<eski> -> <yeni>" <eskiKelime:yeniKelime> <eskiKelime:yeniKelime>
  python3 masa.py <oyuncu> kopyala "<kart sırası, örn. R1,R2>" "<kopya metni>"
  python3 masa.py <oyuncu> cevap "<cevabın>"
"""
import json, sys, re, unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
_argv = sys.argv; sys.argv = [sys.argv[0]]
import simulate as S  # noqa
sys.argv = _argv
R = {r["id"]: r for r in S.RULES}
LOGS = HERE / "logs"

DOCS = [
 {"no": 1, "era": 1, "rules": ["R1", "R2"], "title": "Temel taşı tableti", "old": "Meiros deiwosyo ghewom dōneti. Mēros nākos.",
  "who": "Rahibe, tapınaktan", "says": "Tapınağın temelini kazarken bu tablet çıktı. Bir *khewos* kaydı olmalı, ama hangi *dīwos*'a sunulmuş? Yeni yazıyla kopyala ki rafa koyabilelim.",
  "ask": "Adağı kim sundu? İkinci satır ne diyor?", "heard": []},
 {"no": 2, "era": 2, "rules": ["R3", "R4"], "title": "Kurucuların kaydı", "old": "Mīros Mērom ageti. Mēros nākos.",
  "who": "Saray görevlisi", "says": "*Rīgos* kurucuların kaydını istiyor. Eski defterlerde *grānos* yazıyor, biz artık *grēnos* diyoruz; kopyan bugünün diliyle olmalı. Acele et, *rīgos* beklemez.",
  "ask": "Kurucunun kardeşine ne oldu?", "heard": ["rīgos", "grēnos"]},
 {"no": 3, "era": 2, "rules": ["R3", "R4"], "title": "Bir borç senedi", "old": "Mātēros Mīrosyo grānom emeti.",
  "who": "Tüccar kadın", "says": "Bu senet annemden kaldı. Ben ona *mētīros* derdim, siz eski yazıda başka türlü yazıyorsunuz. Tahıl kimden kime geçmiş, bilmem lazım.",
  "ask": "Tahılı kim aldı, kimin tahılıydı?", "heard": ["mētīros"]},
]
CHAIN = {1: ["R1"] + ["R2"], 2: ["R1", "R2", "R3", "R4"]}


def nfc(x): return unicodedata.normalize("NFC", x.strip())


def apply(ids, w):
    cap = w[:1].isupper(); w = w.lower()
    for i in ids: w = S.apply_rule(w, R[i])
    return w


def real_words(era):
    ids = [r["id"] for r in S.RULES if r["era"] <= era]
    out = set()
    for wd in S.WORDS:
        for f in wd["forms"].values():
            out.add(apply(ids, f).lower())
    return out


def load(p):
    f = LOGS / f"{p}.json"
    return json.loads(f.read_text()) if f.exists() else None


def save(p, st): (LOGS / f"{p}.json").write_text(json.dumps(st, ensure_ascii=False, indent=1))


def show_doc(d):
    print(f"\n=== Belge {d['no']} · Çağ {d['era']} · {d['title']} ===")
    if d["no"] == 2:
        print("(Yüz yıl geçti. Artık Çağ 2'desin: materials/sozluk_cag2.md dosyasını aç. Eski kartların hâlâ geçerli ama bu belgedeki metin zaten Çağ 1 yazısıyla.)")
    print(f"{d['who']}: “{d['says']}”")
    print(f"\nMasadaki eski metin:\n    {d['old']}\n")
    print("Önce eski metni sözlükle eşleştir, ses değişimlerini bul (kural komutu), sonra kopyala.")


def main():
    if len(sys.argv) < 3: print(__doc__); return
    p, cmd, args = sys.argv[1], sys.argv[2], sys.argv[3:]
    st = load(p)
    if cmd == "basla":
        st = {"doc": 1, "cards": [], "log": [], "phase": "oku"}
        save(p, st); show_doc(DOCS[0]); return
    if not st: print("Önce: basla"); return
    d = DOCS[st["doc"] - 1] if st["doc"] <= 3 else None
    def log(**k): st["log"].append({"doc": st["doc"], **k})
    if cmd == "durum":
        print(f"Belge {st['doc']}, kartların: {st['cards'] or 'yok'}, aşama: {st['phase']}")
        if d: show_doc(d)
        return
    if d is None: print("Test bitti. Teşekkürler."); return
    if cmd == "kural":
        if len(args) < 3: print("Kural için değişimi ve İKİ örnek çifti ver: kural \"gh -> kh\" eski:yeni eski:yeni"); return
        m = re.match(r"\s*(\S+)\s*->\s*(\S+)\s*", nfc(args[0]))
        if not m: print("Biçim: \"x -> y\""); return
        frm, to = m.group(1), m.group(2)
        pairs = [tuple(nfc(a).split(":", 1)) for a in args[1:3] if ":" in a]
        hit = None
        for rid in d["rules"]:
            for pat, rep in R[rid]["subs"]:
                if pat == frm and rep == to: hit = rid
        prev_ids = [r["id"] for r in S.RULES if r["era"] < d["era"]]
        cur_ids = [r["id"] for r in S.RULES if r["era"] <= d["era"]]
        ok_pairs = 0
        for old, new in pairs:
            o = old.lower().strip(".,"); n = new.lower().strip(".,")
            if frm in o and n == apply(cur_ids[len(prev_ids):], o) and o != n: ok_pairs += 1
        if hit and ok_pairs >= 2 and len({a for a, _ in pairs}) >= 2:
            if hit not in st["cards"]: st["cards"].append(hit)
            card = R[hit]
            print(f"Masa kartı verdi: {hit} — {card['name_tr']} ({card['note_tr']})")
            log(action="kural", rule=args[0], pairs=args[1:3], result="kart", card=hit)
        else:
            reason = "Masa bu kuralı onaylamadı." if not hit else "Kural doğru olabilir ama iki örnek çiftin ikisi de bunu göstermeli."
            print(reason); log(action="kural", rule=args[0], pairs=args[1:3], result="red")
        save(p, st); return
    if cmd == "kopyala":
        if len(args) < 2: print("kopyala \"R1,R2\" \"metin\""); return
        order = [x.strip() for x in args[0].split(",") if x.strip()]
        missing = [x for x in order if x not in st["cards"]]
        if missing: print(f"Bu kartlar sende yok: {missing}"); return
        real = real_words(d["era"])
        words = [w.strip(".,").lower() for w in nfc(args[1]).split() if w.strip(".,")]
        res = [(w, w in real) for w in words]
        for w, ok in res: print(f"  {w}: {'masa kabul etti' if ok else 'masa bu kelimeyi tanımıyor'}")
        old_words = [w.strip(".,") for w in d["old"].split()]
        allok = all(ok for _, ok in res) and len(words) == len(old_words)
        log(action="kopyala", order=order, text=args[1], accepted=allok, rejected=[w for w, ok in res if not ok])
        if allok:
            st["phase"] = "cevap"; st.setdefault("copies", {})[str(d["no"])] = args[1]
            print(f"\nKopya rafa kondu. Soru: {d['ask']}  →  cevap \"...\"")
        elif len(words) != len(old_words):
            print(f"Eski metinde {len(old_words)} kelime var, kopyanda {len(words)}.")
        save(p, st); return
    if cmd == "cevap":
        if st["phase"] != "cevap": print("Önce belgeyi kopyala."); return
        log(action="cevap", text=" ".join(args))
        st["doc"] += 1; st["phase"] = "oku"; save(p, st)
        print("Talep sahibi teşekkür edip ayrıldı.")
        if st["doc"] <= 3: show_doc(DOCS[st["doc"] - 1])
        else: print("\n=== Test bitti. ===")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
