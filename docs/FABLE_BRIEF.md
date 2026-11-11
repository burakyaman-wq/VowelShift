# Görsel elden geçirme: durum ve kalanlar

Bu iş 11 Kasım 2026'da bu sohbette (claude.ai/code, Fable 5.2) yapıldı. Kurallar `assets/art/STYLE.md`
içinde; bu dosya neyin bittiğini ve neyin kaldığını tutar.

## Biten

1. **Teşhis.** Eski ekranın on zayıf noktası (bordür, masa, ışık, eşyalar, çizgi, boya, karolar, defter,
   belge, küçük parçalar).
2. **Stil motoru.** `tools/art/nakkas.py`: boya ve tahrir ayrı katmanlar, pigment geçişi. `motif.py`: motifler.
3. **II. çağ.** Bütün sprite'lar yeniden çizildi.
4. **I, III ve IV. çağ.** Dört ekolün plakası, belgesi, okuma sayfası, karosu ve ortak parçaları.
   Oyun sprite'ı çağa göre seçiyor (`scripts/ui/art.gd`): masa belgenin çağını, belge bir önceki çağı,
   karo kuralının çağını giyiyor; IV. çağda gölge düşüyor.
5. Testler: 1041 denetim, 0 hata.

## Kalan

- **Burak'ın gözü.** Her çağın ekranına bak (`assets/art/style/cagN_masa.png`); istediğin nesneye
  Illustrator'da dokun (`style/sprites_src/*.svg`), değişikliği koda geri işleyelim.
- **Karar: belge bir önceki çağın ekolünde.** Beğenmezsen `Art.document_era` tek satır.
- **Hareket ve ince işler.** Mürekkebin yazılışı, mühür basılması, pusulanın girişi; yalnız zamanlama ve görsel.
- **IV. çağ oyunda henüz yok** (dilimde belgeler I, II, II, III. çağda). Sprite'lar hazır; `era_look = 4` ile görülür.
- **itch.io gizli taslağı.** Web build alındı ve başsız Chrome'da denendi (`tools/web_build.sh`,
  `tests/web_smoke.js`): 15,5 MB zip, motor yerelde 3 saniyede açılıyor. Yüklemeyi Burak yapacak.
- **Kapak.** Taslak hazır: `style/kapak.png` (1260×1000) ve `kapak_630.png`; `tools/art/kapak.py` üretir.

## Komutlar

```
cd tools/art && python3 minyatur.py --sheet          # sprite'lar
godot --headless --import && godot --headless --script res://tests/run_tests.gd
SHOTS=/tmp/shots xvfb-run -s "-screen 0 1920x1080x24" godot --rendering-driver opengl3 \
  --resolution 1920x1080 --script res://tests/screenshot_desk.gd     # DOC=n, ERA=n ile tek belge
```
