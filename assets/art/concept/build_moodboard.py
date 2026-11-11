"""Render the visual-direction moodboard: python3 assets/art/concept/build_moodboard.py"""
import math
import subprocess
from pathlib import Path
from weasyprint import HTML

HERE = Path(__file__).resolve().parent
F = Path("/tmp/fonts/node_modules/@fontsource")


def face(fam, path, weight=400, style="normal"):
    return f"@font-face{{font-family:'{fam}';src:url('file://{path}');font-weight:{weight};font-style:{style}}}"


fonts = "".join([
    face("EBG", F / "eb-garamond/files/eb-garamond-latin-400-normal.woff2"),
    face("EBG", F / "eb-garamond/files/eb-garamond-latin-500-normal.woff2", 500),
    face("EBG", F / "eb-garamond/files/eb-garamond-latin-400-italic.woff2", 400, "italic"),
    face("EBGX", F / "eb-garamond/files/eb-garamond-latin-ext-400-normal.woff2"),
    face("EBGX", F / "eb-garamond/files/eb-garamond-latin-ext-500-normal.woff2", 500),
    face("EBGX", F / "eb-garamond/files/eb-garamond-latin-ext-400-italic.woff2", 400, "italic"),
    face("COR", F / "cormorant-garamond/files/cormorant-garamond-latin-600-normal.woff2", 600),
    face("CORX", F / "cormorant-garamond/files/cormorant-garamond-latin-ext-600-normal.woff2", 600),
    face("FELL", F / "im-fell-english/files/im-fell-english-latin-400-italic.woff2", 400, "italic"),
])


def star(cx, cy, r, fill, stroke, sw=2):
    pts = []
    for i in range(16):
        a = math.pi / 8 * i
        rr = r if i % 2 == 0 else r * 0.72
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def star_tile(w, h, step, c1, c2, bg):
    s = [f'<rect width="{w}" height="{h}" fill="{bg}"/>']
    for y in range(0, h + step, step):
        for x in range(0, w + step, step):
            s.append(star(x, y, step * 0.42, c1, c2, 2))
            s.append(f'<circle cx="{x + step / 2}" cy="{y + step / 2}" r="{step * 0.12}" fill="{c2}"/>')
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(s)}</svg>'


def corner(x, y):
    return f'<svg style="position:absolute;left:{x}px;top:{y}px" width="70" height="70" viewBox="0 0 70 70">{star(35, 35, 28, "#c9a24a", "#1f3a6b", 3)}<circle cx="35" cy="35" r="9" fill="#1f3a6b"/></svg>'


ICONS = {
    "tarla": '<path d="M6 30 L34 30 M8 24 L32 24 M12 18 L28 18" stroke="#3b2a1c" stroke-width="2.5" fill="none"/><path d="M20 6 L20 16" stroke="#3b2a1c" stroke-width="2.5"/>',
    "tahıl": '<path d="M20 34 L20 8" stroke="#3b2a1c" stroke-width="2.5"/><ellipse cx="15" cy="14" rx="4" ry="7" fill="none" stroke="#3b2a1c" stroke-width="2"/><ellipse cx="25" cy="18" rx="4" ry="7" fill="none" stroke="#3b2a1c" stroke-width="2"/><ellipse cx="15" cy="25" rx="4" ry="6" fill="none" stroke="#3b2a1c" stroke-width="2"/>',
    "bey": '<path d="M8 28 L8 14 L14 20 L20 8 L26 20 L32 14 L32 28 Z" fill="none" stroke="#3b2a1c" stroke-width="2.5"/>',
    "borç": '<circle cx="20" cy="20" r="11" fill="none" stroke="#3b2a1c" stroke-width="2.5"/><path d="M20 13 L20 27 M15 17 L25 17" stroke="#3b2a1c" stroke-width="2"/>',
    "sürgün": '<path d="M6 30 L34 30" stroke="#3b2a1c" stroke-width="2"/><path d="M12 30 L18 14 L24 30" fill="none" stroke="#3b2a1c" stroke-width="2.5"/><path d="M26 12 L34 12 M30 8 L34 12 L30 16" fill="none" stroke="#3b2a1c" stroke-width="2"/>',
    "ölü": '<path d="M12 32 L12 14 Q20 4 28 14 L28 32 Z" fill="none" stroke="#3b2a1c" stroke-width="2.5"/><path d="M20 16 L20 26 M16 20 L24 20" stroke="#3b2a1c" stroke-width="2"/>',
}


def icon(k):
    return f'<svg width="40" height="40" viewBox="0 0 40 40">{ICONS[k]}</svg>'


lex = [("ēgros", "tarla", "tarla"), ("grēnos", "tahıl", "tahıl"), ("rīgos", "bey", "bey"),
       ("thītos", "borç", "borç"), ("?", "sürgün", "sürgün"), ("?", "ölü", "ölü")]
lex_html = "".join(f'<div class="lexrow">{icon(k)}<span class="lw">{w}</span><span class="lm">{m}</span></div>' for w, m, k in lex)

eras = [
    ("Çağ I · Tapınak", "lapis, altın, kandil", ["#1f3a6b", "#c9a24a", "#ead9b0", "#a6512f", "#2b1d14"]),
    ("Çağ II · Saray", "lal kırmızısı, aşı boyası, firuze", ["#7a1f24", "#c48a2c", "#e6d2a6", "#2f7f7a", "#2b1d14"]),
    ("Çağ III · Savaş", "is, kül, kor", ["#3a3633", "#8d877d", "#cfc3a8", "#b4532a", "#1d1a18"]),
    ("Çağ IV · Yeni düzen", "çivit, arduvaz, soğuk kâğıt", ["#22304a", "#5b6b7a", "#e4e1d6", "#4f8f7f", "#151515"]),
]
era_html = "".join(
    f'<div class="era"><div class="en">{n}<span>{d}</span></div><div class="sw">' +
    "".join(f'<i style="background:{c}"></i>' for c in cs) + "</div></div>" for n, d, cs in eras)


def card(x, y, rot, rule, name, active=True):
    op = "1" if active else ".9"
    return f'''<div class="card" style="left:{x}px;top:{y}px;transform:rotate({rot}deg);opacity:{op}">
<div class="cardin"><div class="cr">{rule}</div><div class="cn">{name}</div></div></div>'''


html = f"""<html><head><meta charset="utf-8"><style>
{fonts}
@page {{ size: 2400px 1500px; margin: 0 }}
body {{ margin:0; width:2400px; height:1500px; position:relative; font-family:'EBG','EBGX',serif; overflow:hidden }}
.desk {{ position:absolute; left:0; top:0; width:1600px; height:1500px;
  background: radial-gradient(ellipse 900px 700px at 800px 330px, rgba(255,196,110,.55), rgba(255,170,80,.12) 55%, rgba(0,0,0,0) 75%),
              repeating-linear-gradient(92deg, #3a2618 0px, #3a2618 14px, #34221a 15px, #3d2a1b 36px, #33211a 37px),
              #2e1f15; }}
.vign {{ position:absolute; left:0; top:0; width:1600px; height:1500px; background: radial-gradient(ellipse 1100px 900px at 800px 650px, rgba(0,0,0,0) 55%, rgba(8,4,2,.75) 100%) }}
.label {{ position:absolute; left:60px; top:48px; color:#e3c27a; font-family:'COR','CORX'; font-size:30px; letter-spacing:.18em }}
.label span {{ color:#b99a63; font-size:22px; letter-spacing:.08em; margin-left:18px; font-family:'EBG','EBGX'; font-style:italic }}
.ms {{ position:absolute; left:470px; top:190px; width:660px; height:900px; background: radial-gradient(ellipse 420px 520px at 330px 420px, #f1e3c2, #e2cc9e 70%, #c9ac74 100%);
  box-shadow: 0 30px 60px rgba(0,0,0,.6); }}
.ms .frame {{ position:absolute; left:26px; top:26px; right:26px; bottom:26px; border:3px solid #b8913f; }}
.ms .frame2 {{ position:absolute; left:38px; top:38px; right:38px; bottom:38px; border:1.5px solid #1f3a6b; }}
.ms .t {{ position:absolute; left:0; right:0; top:92px; text-align:center; font-family:'COR','CORX'; font-size:34px; color:#7a1f24; letter-spacing:.12em }}
.ms .old {{ position:absolute; left:70px; right:70px; top:190px; text-align:center; font-size:58px; line-height:1.5; color:#2b1d14 }}
.ms .rule {{ position:absolute; left:120px; right:120px; top:470px; height:30px; text-align:center; color:#b8913f; font-size:26px; letter-spacing:.6em }}
.ms .lab {{ position:absolute; left:0; right:0; top:540px; text-align:center; font-style:italic; color:#6d5638; font-size:24px }}
.ms .copy {{ position:absolute; left:70px; right:70px; top:590px; text-align:center; font-size:46px; line-height:1.5; color:#1f3a6b }}
.ms .copy b {{ font-weight:500; color:#a6512f; border-bottom:2px solid #a6512f }}
.note {{ position:absolute; left:820px; top:965px; width:230px; transform:rotate(-4deg); font-family:'FELL','EBGX'; font-style:italic; color:#5a3a1e; font-size:30px; line-height:1.2 }}
.note:before {{ content:''; position:absolute; left:-30px; top:16px; width:22px; height:2px; background:#5a3a1e }}
.lexbook {{ position:absolute; left:58px; top:250px; width:380px; height:760px; background: repeating-linear-gradient(180deg, #efe2c4 0, #efe2c4 49px, #d9c69e 50px); transform:rotate(-2.5deg);
  box-shadow: 0 20px 40px rgba(0,0,0,.55); border-left:14px solid #6b2a20 }}
.lexbook h3 {{ margin:0; padding:26px 0 10px 30px; font-family:'COR','CORX'; color:#6b2a20; font-size:30px; letter-spacing:.1em; font-weight:600 }}
.lexrow {{ height:50px; display:block; padding-left:24px; position:relative }}
.lexrow svg {{ position:absolute; left:24px; top:4px }}
.lw {{ position:absolute; left:80px; top:6px; font-size:30px; color:#2b1d14 }}
.lm {{ position:absolute; left:220px; top:10px; font-size:22px; font-style:italic; color:#6d5638 }}
.door {{ position:absolute; left:1190px; top:170px; width:330px; height:560px }}
.speech {{ position:absolute; left:1170px; top:700px; width:370px; background:#ead9b0; padding:22px 26px; font-size:24px; line-height:1.4; color:#2b1d14; box-shadow:0 16px 30px rgba(0,0,0,.5); border-top:6px solid #7a1f24 }}
.speech i {{ color:#7a1f24 }}
.speech .who {{ font-family:'COR','CORX'; font-size:22px; letter-spacing:.14em; color:#7a1f24; margin-bottom:8px }}
.tray {{ position:absolute; left:450px; top:1150px; width:700px; height:300px; background: linear-gradient(180deg,#5a3a22,#3f2816); border-radius:10px; box-shadow: inset 0 6px 18px rgba(0,0,0,.6), 0 16px 30px rgba(0,0,0,.5) }}
.tray .tl {{ position:absolute; left:24px; top:14px; font-family:'COR','CORX'; color:#d9b66a; letter-spacing:.2em; font-size:22px }}
.arrow {{ position:absolute; left:780px; top:1270px; color:#e3c27a; font-size:60px }}
.card {{ position:absolute; width:210px; height:250px; background:#f0e4c8; border-radius:8px; box-shadow:0 12px 24px rgba(0,0,0,.55) }}
.cardin {{ position:absolute; left:12px; top:12px; right:12px; bottom:12px; border:6px solid #2f6f8f; border-radius:4px; background: radial-gradient(circle at 50% 40%, #f7eedb, #e8d6ae) }}
.cr {{ position:absolute; left:0; right:0; top:62px; text-align:center; font-size:56px; color:#1f3a6b }}
.cn {{ position:absolute; left:0; right:0; bottom:22px; text-align:center; font-size:22px; font-style:italic; color:#6d5638 }}
.panel {{ position:absolute; left:1600px; top:0; width:800px; height:1500px; background:#f1e6cf; color:#2b1d14 }}
.panel h1 {{ margin:0; position:absolute; left:64px; top:56px; font-family:'COR','CORX'; font-size:62px; font-weight:600; color:#2b1d14 }}
.panel .sub {{ position:absolute; left:66px; top:138px; font-style:italic; font-size:26px; color:#6d5638 }}
.panel .p {{ position:absolute; left:64px; width:680px }}
.panel h2 {{ margin:0 0 14px; font-family:'COR','CORX'; font-size:30px; letter-spacing:.14em; color:#7a1f24; font-weight:600 }}
.panel li {{ font-size:23px; line-height:1.35; margin-bottom:8px }}
.panel ul {{ margin:0; padding-left:24px }}
.era {{ height:62px; position:relative; margin-bottom:6px }}
.en {{ position:absolute; left:0; top:4px; font-size:24px; width:330px }}
.en span {{ display:block; font-size:18px; font-style:italic; color:#6d5638 }}
.sw {{ position:absolute; left:340px; top:2px }}
.sw i {{ display:inline-block; width:62px; height:52px; margin-right:6px; border-radius:3px }}
.ty div {{ margin-bottom:12px; font-size:22px }}
.ty .a {{ font-size:40px }} .ty .b {{ font-family:'COR','CORX'; font-size:40px; font-weight:600 }} .ty .c {{ font-family:'FELL','EBGX'; font-style:italic; font-size:36px; color:#5a3a1e }}
.ty span {{ font-size:18px; color:#6d5638; font-style:italic; font-family:'EBG','EBGX'; margin-left:14px }}
</style></head><body>
<div class="desk"></div><div class="vign"></div>
<div class="label">ÇAĞ II<span>Kerdēgros · saray yazıhanesi</span></div>
<div class="lexbook"><h3>SÖZLÜK</h3>{lex_html}</div>
<div class="ms"><div class="frame"></div><div class="frame2"></div>
{corner(10, 10)}{corner(580, 10)}{corner(10, 820)}{corner(580, 820)}
<div class="t">KURUCULARIN KAYDI</div>
<div class="old">Mīros Mērom ageti.<br>Mēros nākos.</div>
<div class="rule">✦ ✦ ✦</div>
<div class="lab">masanın kopyası</div>
<div class="copy">Mīros M<b>ī</b>rom ageti.<br>M<b>ī</b>ros n<b>ē</b>kos.</div>
</div>
<div class="note">sürgün, ölü değil.</div>
<svg class="door" viewBox="0 0 330 560"><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#120b07"/><stop offset="1" stop-color="#2a1a10"/></linearGradient></defs>
<path d="M20 560 L20 230 Q20 90 165 20 Q310 90 310 230 L310 560 Z" fill="#c9a24a"/>
<path d="M44 560 L44 236 Q44 116 165 50 Q286 116 286 236 L286 560 Z" fill="url(#g)"/>
<path d="M44 236 Q44 116 165 50 Q286 116 286 236" fill="none" stroke="#2f7f7a" stroke-width="5"/>
<path d="M165 200 Q128 205 124 255 Q122 290 132 312 Q100 330 92 380 L80 560 L250 560 L238 380 Q230 330 198 312 Q208 290 206 255 Q202 205 165 200 Z" fill="#0a0604"/><path d="M165 222 Q146 228 145 258 Q146 282 165 290 Q184 282 185 258 Q184 228 165 222 Z" fill="#1c120c"/></svg>
<div class="speech"><div class="who">SARAY GÖREVLİSİ</div>“<i>Rīgos</i> kurucuların kaydını istiyor. Eski defterlerde <i>grānos</i> yazıyor, biz artık <i>grēnos</i> diyoruz…”</div>
<div class="tray"><div class="tl">KURAL TABLETİ</div></div>
{card(500, 1190, -1.5, "ē → ī", "ē yükselir")}
<div class="arrow">→</div>
{card(880, 1190, 1.2, "ā → ē", "ā kayar")}
{card(1230, 1225, 8, "kh → ş", "damaklaşma", False)}
<div class="panel">
<h1>Ses Kayması</h1><div class="sub">görsel yön taslağı · bir yazıhane masası, dört çağ</div>
<div class="p" style="top:210px"><h2>İLKELER</h2><ul>
<li><b>Mum ışığında tek masa.</b> Bütün oyun aynı masada geçer; çağ değişince masa değil ışık, renk ve kâğıt değişir.</li>
<li><b>Geometri çerçeve olur.</b> Selçuklu yıldızı ve tezhip kenarları süs değil: belgeyi, kartları ve kapıyı çerçeveler.</li>
<li><b>Yazı kahramandır.</b> Uzun ünlüler büyük ve okunur; kopyada değişen harf kırmızı aşı boyasıyla işaretlenir.</li>
<li><b>Kapı, dış dünyadır.</b> Talep sahipleri yalnızca kemerli kapıda siluet; tarih içeri sözle girer.</li></ul></div>
<div class="p" style="top:590px"><h2>ÇAĞ PALETLERİ</h2>{era_html}</div>
<div class="p ty" style="top:975px"><h2>YAZI</h2>
<div class="a">Mīros nēkos <span>metin · EB Garamond</span></div>
<div class="b">KURUCULARIN KAYDI <span>başlık · Cormorant Garamond</span></div>
<div class="c">sürgün, ölü değil <span>kenar notu · IM Fell</span></div></div>
<div class="p" style="top:1225px"><h2>MOTİF</h2>
<div style="position:absolute;left:0;top:50px">{star_tile(300, 180, 100, "#c9a24a", "#1f3a6b", "#e6d2a6")}</div>
<div style="position:absolute;left:330px;top:50px;width:350px;font-size:21px;line-height:1.35;color:#3b2a1c">Sekiz kollu yıldız: kart kenarları, kapı kemeri ve belge köşeleri. Referanslar: Pentiment'in sayfa dili, Heaven's Vault'un yazı odağı, Selçuklu çini geometrisi.</div></div>
</div>
</body></html>"""

(HERE / "moodboard.html").write_text(html, encoding="utf-8")
pdf = HERE / "moodboard.pdf"
HTML(string=html, base_url=str(HERE)).write_pdf(pdf)
subprocess.run(["pdftoppm", "-r", "96", "-png", "-singlefile", str(pdf), str(HERE / "gorsel_yon_v1")], check=True)
pdf.unlink()
print(HERE / "gorsel_yon_v1.png")
