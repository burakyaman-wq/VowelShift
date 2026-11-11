"""Build the paper prototype PDF (A4). Usage: python3 prototype/paper/build.py"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.argv = [sys.argv[0]]
sys.path.insert(0, str(ROOT / "tools"))
import simulate as s  # noqa: E402
from weasyprint import HTML  # noqa: E402

R = {r["id"]: r for r in s.RULES}


def chain(ids, text):
    out = []
    for tok in text.split():
        word, dot = tok.rstrip("."), tok.endswith(".")
        cap = word[:1].isupper()
        w = word.lower()
        for i in ids:
            w = s.apply_rule(w, R[i])
        out.append((w[:1].upper() + w[1:] if cap else w) + ("." if dot else ""))
    return " ".join(out)


DOCS = [
    {"no": 1, "era": 1, "title": "Temel taşı tableti", "old": "Meiros deiwosyo ghewom dōneti. Mēros nākos.",
     "who": "Rahibe, tapınaktan",
     "says": "Tapınağın temelini kazarken bu tablet çıktı. Bir <i>khewos</i> kaydı olmalı, ama hangi <i>dīwos</i>'a sunulmuş? Yeni yazıyla kopyala ki rafa koyabilelim.",
     "ask": "Adağı kim sundu? İkinci satır ne diyor?", "chain": ["R1", "R2"]},
    {"no": 2, "era": 2, "title": "Kurucuların kaydı", "old": "Mīros Mērom ageti. Mēros nākos.",
     "who": "Saray görevlisi",
     "says": "<i>Rīgos</i> kurucuların kaydını istiyor. Eski defterlerde <i>grānos</i> yazıyor, biz artık <i>grēnos</i> diyoruz; kopyan bugünün diliyle olmalı. Acele et, <i>rīgos</i> beklemez.",
     "ask": "Kurucunun kardeşine ne oldu?", "chain": ["R3", "R4"], "key": True},
    {"no": 3, "era": 2, "title": "Bir borç senedi", "old": "Mātēros Mīrosyo grānom emeti.",
     "who": "Tüccar kadın",
     "says": "Bu senet annemden kaldı. Ben ona <i>mētīros</i> derdim, siz eski yazıda başka türlü yazıyorsunuz. Tahıl kimden kime geçmiş, bilmem lazım.",
     "ask": "Tahılı kim aldı, kimin tahılıydı?", "chain": ["R3", "R4"]},
]
for d in DOCS:
    d["right"] = chain(d["chain"], d["old"])
    d["wrong"] = chain(list(reversed(d["chain"])), d["old"])

LEX1 = [("Mīros", "kurucu, büyük kardeş"), ("Mēros", "kurucu, küçük kardeş"), ("dīwos", "tanrı"),
        ("khewos", "adak, sunu"), ("dōneti", "verir"), ("emeti", "alır"), ("ageti", "kovar, sürer"),
        ("nākos", "sürgün"), ("nēkos", "ölü"), ("āgros", "tarla"), ("grānos", "tahıl"),
        ("rēgos", "bey, kral"), ("mātēros", "anne"), ("lōkos", "ışık, kandil"), ("thūmos", "duman"),
        ("phāgos", "kitap")]
LEX2_KNOWN = {"rīgos", "grēnos", "mētīros"}


def era2(w):
    return chain(["R3", "R4"], w)


CARDS = [("R1", "Aspiratlar sertleşir", "bh → ph · dh → th · gh → kh", "Belge 1"),
         ("R2", "Çift ünlüler kaynaşır", "ei → ī · eu → ō", "Belge 1"),
         ("R3", "Uzun ē yükselir", "ē → ī", "Belge 2"),
         ("R4", "Uzun ā öne kayar", "ā → ē", "Belge 2")]

CSS = """
@page { size: A4; margin: 16mm 16mm 14mm; @bottom-right { content: "Ses Kayması · kâğıt prototip · s. " counter(page); font: 8pt 'DejaVu Sans'; color: #888; } }
body { font-family: 'DejaVu Sans'; font-size: 10pt; color: #2a211a; line-height: 1.4; }
h1 { font-family: 'DejaVu Serif'; font-size: 20pt; margin: 0 0 2mm; }
h2 { font-family: 'DejaVu Serif'; font-size: 14pt; margin: 6mm 0 2mm; border-bottom: 1px solid #c9b48a; padding-bottom: 1mm; }
.page { page-break-after: always; }
.tag { display: inline-block; font-size: 8pt; letter-spacing: .08em; text-transform: uppercase; color: #8a6d3b; }
.ms { background: #f3e7c9; border: 1px solid #b89a5e; border-radius: 3mm; padding: 9mm 8mm; margin: 4mm 0;
      font-family: 'DejaVu Serif'; font-size: 22pt; letter-spacing: .04em; line-height: 1.7; text-align: center; }
.req { border-left: 3px solid #8a6d3b; padding: 2mm 4mm; margin: 4mm 0; background: #faf6ec; }
.lines div { border-bottom: 1px solid #999; height: 11mm; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 1px solid #c9b48a; padding: 1.2mm 2.5mm; vertical-align: top; }
th { background: #f3e7c9; text-align: left; font-size: 9pt; }
.pic { width: 16mm; height: 9mm; border: 1px dashed #b89a5e; font-size: 7pt; color: #8a6d3b; text-align: center; vertical-align: middle; }
.form { font-family: 'DejaVu Serif'; font-size: 13pt; }
.cards { font-size: 0; }
.card { display: inline-block; vertical-align: top; font-size: 10pt; width: 85mm; height: 52mm; border: 1px dashed #777; box-sizing: border-box; padding: 5mm; margin: 0 2mm 2mm 0; position: relative; }
.card .id { font-size: 8pt; color: #8a6d3b; } .card .name { font-family: 'DejaVu Serif'; font-size: 13pt; margin-top: 2mm; }
.card .rule { font-family: 'DejaVu Serif'; font-size: 20pt; margin-top: 5mm; text-align: center; }
.card .where { position: absolute; bottom: 4mm; right: 5mm; font-size: 7pt; color: #999; }
.tablet { margin-top: 4mm; font-size: 0; } .slot { display: inline-block; width: 85mm; margin-right: 3mm; box-sizing: border-box; font-size: 9pt; height: 52mm; border: 2px solid #8a6d3b; border-radius: 3mm; text-align: center; padding-top: 22mm; color: #b89a5e; font-size: 9pt; }
.small { font-size: 8.5pt; color: #555; } .warn { color: #8b2e1f; font-weight: bold; }
ol li, ul li { margin-bottom: 1.5mm; }
"""


def page(html):
    return f'<section class="page">{html}</section>'


pages = []

# 1 Facilitator guide
pages.append(page(f"""
<span class="tag">Yönetici için · oyuncuya gösterme</span>
<h1>Ses Kayması — kâğıt prototip</h1>
<p><b>Test edilen döngü:</b> Oku → Kopyala → Cevapla. Sen <b>masa</b>sın: eşleşmeleri onaylar, kural kartını verir, kopyadaki kelimelerin gerçek olup olmadığını söylersin. Süre: 20–30 dakika, tek oyuncu.</p>
<h2>Hazırlık</h2>
<ul><li>Kural kartlarını (s. 3) kes, ters çevir, oyuncuya gösterme. Boş kartları ve kural tabletini (s. 4) masaya koy.</li>
<li>Oyuncuya ver: Dilbilgisi kartı (s. 2), Çağ 1 sözlüğü (s. 5). Belgeleri sırayla ver.</li>
<li>Çağ 2 sözlüğünü (s. 7) Belge 2 başlarken ver.</li></ul>
<h2>Her belgede</h2>
<ol>
<li><b>Talep:</b> Talep sahibinin repliğini sesli oku. İtalik kelimeler bugünün dilinden; oyuncu bunları sözlükle karşılaştırabilir.</li>
<li><b>Oku:</b> Oyuncu eski metindeki kelimeleri sözlükle eşleştirir. Bir ses değişimini <b>iki örnek kelimeyle</b> söylerse (örn. “ghewom → khewom, dīwos”) kartı ver. Tek örnekle verme; tahmin değil, çıkarım istiyoruz.</li>
<li><b>Kopyala:</b> Oyuncu kartları tablete <b>istediği sırayla</b> dizer ve her kelimeye kartları soldan sağa uygulayarak kopyayı yazar.</li>
<li><b>Masa denetimi:</b> Her kopyalanan kelimeye bak. Cevap anahtarındaki (s. 10) “gerçek kelime” listesindeyse “masa kabul etti” de; değilse yalnızca “masa bu kelimeyi tanımıyor” de, nedenini söyleme.</li>
<li><b>Cevapla:</b> Soruyu sor; oyuncu cevabı kendi kopyasından vermeli.</li></ol>
<h2><span class="warn">Gizli kural: Belge 2</span></h2>
<p>Oyuncu R4'ü R3'ten önce dizerse <i>nākos</i> → <b>nīkos</b> olur. Bu gerçek bir kelimedir (“ölü”), <b>kabul et ve hiçbir şey söyleme.</b> Sırayı not et. Belge 3'te aynı yanlış sıra reddedilecek; oyuncunun Belge 2'ye geri dönüp dönmediğini gözle. Testten sonra açıkla.</p>
<h2>Gözlem formu (s. 11)</h2>
<p class="small">Sessiz kal, ipucu verme. Oyuncu takılırsa 2 dakika bekle, sonra yalnızca “sözlükteki hangi kelime buna benziyor?” diye sor.</p>
"""))

# 2 Grammar card
pages.append(page("""
<span class="tag">Oyuncu</span>
<h1>Dilbilgisi kartı</h1>
<p>Bu dil yüzyıllardır yazılıyor. Eklerinin anlamını biliyorsun; değişen, kelimelerin sesi.</p>
<table><tr><th>Ek</th><th>Görev</th><th>Örnek</th></tr>
<tr><td class="form">-os</td><td>özne (yapan)</td><td class="form">dīwos <span class="small">tanrı</span></td></tr>
<tr><td class="form">-om</td><td>nesne (-ı, -i)</td><td class="form">dīwom <span class="small">tanrıyı</span></td></tr>
<tr><td class="form">-osyo</td><td>iyelik (-ın, -in)</td><td class="form">dīwosyo <span class="small">tanrının</span></td></tr>
<tr><td class="form">o → e</td><td>çoğul</td><td class="form">dīwes <span class="small">tanrılar</span></td></tr>
<tr><td class="form">-eti</td><td>fiil: yapar</td><td class="form">dōneti <span class="small">verir</span></td></tr></table>
<h2>Cümle düzeni</h2>
<p>Özne — Nesne — Fiil, Türkçedeki gibi. Fiilsiz cümle “-dır” anlamı taşır: <span class="form">Mīros rēgos.</span> = Mīros beydir.</p>
<h2>Kâtip olarak işin</h2>
<ol><li><b>Oku:</b> Eski metnin kelimelerini sözlüğündeki bugünkü kelimelerle eşleştir. Sesin nasıl değiştiğini fark edince masaya söyle.</li>
<li><b>Kopyala:</b> Bulduğun kural kartlarını tablete diz. Her kelimeye kartları soldan sağa uygula ve yeni yazıyla kopyala.</li>
<li><b>Cevapla:</b> Talep sahibinin sorusunu kendi kopyandan cevapla.</li></ol>
"""))

# 3 Rule cards
cards = "".join(f'<div class="card"><div class="id">{c[0]}</div><div class="name">{c[1]}</div><div class="rule">{c[2]}</div><div class="where">{c[3]}</div></div>' for c in CARDS)
pages.append(page(f'<span class="tag">Yönetici · kes, ters çevir</span><h1>Kural kartları</h1><div class="cards">{cards}</div>'))

# 4 Blank cards + tablet
blank = "".join('<div class="card"><div class="id">Kendi kuralın</div><div class="rule" style="color:#ccc">… → …</div></div>' for _ in range(2))
pages.append(page(f'<span class="tag">Oyuncu</span><h1>Kural tableti</h1><p>Kartları sırayla diz. Her kelimeye soldan sağa uygulanır.</p><div class="tablet"><div class="slot">1</div><div class="slot">2</div></div><h2>Boş kartlar</h2><p class="small">Bir kuralı fark ettiğinde buraya yazabilirsin.</p><div class="cards">{blank}</div>'))


def lex_table(rows):
    body = "".join(f'<tr><td class="pic">{m}</td><td class="form">{f}</td><td>{m}</td></tr>' for f, m in rows)
    return f'<table><tr><th style="width:18mm">Resim</th><th>Kelime</th><th>Anlam</th></tr>{body}</table>'


# 5 Lexicon era 1
pages.append(page('<span class="tag">Oyuncu · Çağ 1</span><h1>Sözlük — senin çağın</h1><p class="small">Bugün böyle yazılıyor. Resimler oyunda çizimle gelecek.</p>' + lex_table(LEX1)))


def doc_page(d):
    return page(f"""
<span class="tag">Oyuncu · Çağ {d['era']} · Belge {d['no']}</span>
<h1>{d['title']}</h1>
<div class="req"><b>{d['who']}:</b> “{d['says']}”</div>
<p class="small">Masadaki eski metin:</p>
<div class="ms">{d['old']}</div>
<p><b>Kopyan (yeni yazıyla):</b></p>
<div class="lines"><div></div><div></div></div>
<p style="margin-top:6mm"><b>Soru:</b> {d['ask']}</p>
<div class="lines"><div></div></div>""")


pages.append(doc_page(DOCS[0]))

# 7 Lexicon era 2 (partial)
rows2 = []
for f, m in LEX1:
    new = era2(f)
    rows2.append((new if new in LEX2_KNOWN else "?", m))
pages.append(page('<span class="tag">Oyuncu · Çağ 2</span><h1>Sözlük — yeni çağ</h1><p>Yüz yıl geçti. Sözlüğün eskidi; bildiğin kelimelerin çoğunun bugün nasıl söylendiğini henüz bilmiyorsun. Duydukça doldur.</p>' + lex_table(rows2)))

pages.append(doc_page(DOCS[1]))
pages.append(doc_page(DOCS[2]))

# 10 Answer key
def keyrow(d):
    return f"<tr><td>Belge {d['no']}</td><td class='form'>{d['right']}</td><td class='form'>{d['wrong'] if d['wrong'] != d['right'] else '—'}</td></tr>"
real2 = sorted({era2(f) for f, _ in LEX1})
pages.append(page(f"""
<span class="tag">Yönetici · cevap anahtarı</span><h1>Cevap anahtarı</h1>
<table><tr><th>Belge</th><th>Doğru kopya</th><th>Ters sırayla</th></tr>{''.join(keyrow(d) for d in DOCS)}</table>
<p class="small">Belge 1'de sıra önemsiz (R1 ve R2 birbirini etkilemez). Belge 2 ve 3'te doğru sıra R3 → R4.</p>
<h2>Masanın kabul ettiği kelimeler</h2>
<p><b>Çağ 1:</b> <span class="form">{' · '.join(f for f, _ in LEX1)}</span></p>
<p><b>Çağ 2:</b> <span class="form">{' · '.join(real2)}</span></p>
<p class="small">Ekleri (-om, -osyo, çoğul) ve özel adları kökün çekimi olarak kabul et.</p>
<h2>Kontrol</h2>
<ul><li>Belge 2, ters sıra: <span class="form">nīkos</span> Çağ 2'de <b>nēkos (ölü)</b> kelimesinin biçimi → <span class="warn">kabul et, sessiz kal.</span></li>
<li>Belge 3, ters sıra: <span class="form">Mītīros, grīnom</span> gerçek değil → reddet.</li>
<li>Doğru cevaplar: (1) Mīros sundu; Mēros sürgündür. (2) Sürgün edildi (oyuncu nīkos yazdıysa “öldü” der). (3) Anne aldı; Mīros'un tahılıydı.</li></ul>
"""))

# 11 Observation form
qs = ["Oyuncu ilk kuralı kendi başına kaç dakikada buldu?", "İki örnek şartı can sıktı mı, yoksa “aha” anını güçlendirdi mi?",
      "Belge 2'de kartları hangi sırayla dizdi? nīkos yazdı mı?", "Belge 3'te reddedilince Belge 2'ye geri dönmek istedi mi?",
      "Sıralama anı keyifli miydi, angarya mıydı?", "Cevap adımı anlamlı geldi mi, yoksa fazlalık mı?",
      "Talep sahiplerinin repliklerindeki ipuçlarını fark etti mi?", "Oyuncunun kendi cümlesiyle: oyun neyle ilgili?"]
pages.append(page('<span class="tag">Yönetici</span><h1>Gözlem formu</h1><table>' + "".join(f'<tr><td style="width:55%">{q}</td><td style="height:16mm"></td></tr>' for q in qs) + '</table>'))

html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(pages)}</body></html>"
out = Path(__file__).with_name("ses_kaymasi_kagit_prototip.pdf")
HTML(string=html).write_pdf(out)
print(out)
for d in DOCS:
    print(d["no"], d["right"], "|", d["wrong"])
