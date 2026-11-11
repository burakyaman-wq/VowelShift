# Brif: Görsel dilin Fable 5.2 ile elden geçirilmesi

Bu belge görsel elden geçirme işinin brifidir; iş bu sohbette (claude.ai/code) yürür.
Oturum bu dosyayı ve aşağıda adı geçen dosyaları okuyarak başlar; önceki sohbetleri bilmez.

## Başlatma

```
cd VowelShift
claude --model claude-fable-5-2 --effort xhigh
> docs/FABLE_BRIEF.md dosyasını oku ve 1. adımdan başla.
```

- `/status` ile ücretin Console API anahtarından geçtiğini doğrula; `/cost` ile harcamayı izle.
- Console'da bu iş için ayrı workspace ve harcama tavanı aç.
- Her adımın sonunda dur, Burak'a ekran görüntülerini göster, onay al. Onaysız sonraki adıma geçme.

## Oyun ve durum (kısa)

- **Ses Kayması / VowelShift**, Godot 4.7.2, GitHub Game Off 2026 (tema SHIFT). Teslim: 2 Aralık 00:37 (İstanbul).
- Kâtip, kayan bir ön-dilin 4 çağında el yazmalarını kopyalar: ses kurallarını eşleştirerek kanıtlar,
  kural karolarını tepsiye dizer, kopyayı mürekkeple yazar, istekte bulunanın sorusunu cevaplar.
- Belge 1 baştan sona oynanıyor. 1041 test, 0 hata. Görsel dil onaylı (Nakkaş Osman üslubu); şimdi
  işçiliği yükseltme zamanı.

## Önce oku

1. `assets/art/STYLE.md` — üslup kuralları. **Bunlar değişmez**; iş, kuralları daha iyi uygulamak.
2. `tools/art/minyatur.py` — stil motoru (palet `C`, `LINE`, motifler, nesneler, sahneler, `export_sprites`).
3. `scripts/ui/desk.gd`, `rule_tile.gd`, `rule_tray.gd` — sprite'ların nerede ve hangi boyutta kullanıldığı.
4. `assets/art/style/godot_*.png` — oyundaki mevcut hâl.

## Değişmeyecekler (sözleşme)

- **AI görsel üretimi serbest (Burak'ın kararı, 11 Kasım 2026).** Görüntü üreten araçlar kullanılabilir;
  çıktılar üslup kurallarına uymalı ve oyunda tek elden çıkmış görünmeli. Kod (SVG) ve Burak'ın
  Illustrator rötuşu yine kullanılır. **AI beyanı açık kalır:** itch.io sayfasında ve README'de hangi
  asset'lerin AI ile üretildiği yazılır (`assets/art/AI_LOG.md`).
- Üslup kuralları (`STYLE.md`): tam üstten, düz boya, ince tahrir, altın yok, ışık yok, kişi yok,
  belgelerde yazı önce, her yerde Katip.
- Sprite **dosya adları ve piksel boyutları** aynı kalır (aşağıdaki tablo). Değişmesi gerekirse
  `desk.gd` yerleşimi aynı commit'te güncellenir ve testler geçer.
- Oyun mantığı (`scripts/core/`), veri (`data/`) ve testlerin mantığı değişmez.
- Katip fontu (`assets/fonts/Katip-Regular.ttf`) değişmez; OFL, ayrılmış ad EURM10 kullanılmaz.

| Sprite | Boyut |
|---|---|
| masa_cag2 | 1920×1080 |
| belge_kagit | 680×440 |
| belge_okuma | 1520×760 |
| kopya_kagit | 420×500 |
| defter | 520×420 |
| pusula | 360×250 |
| tepsi, karo_cerceve, picto_R1..R8, durak, kalem, muhur, sayfa_doku | mevcut boyutlar |

## Adımlar

### 1. Teşhis (kod yazmadan)
Mevcut `godot_*.png` görüntülerini incele. Klasik minyatür referanslarına göre (Nakkaş Osman,
Şehinşahname, Surname-i Hümayun) en zayıf 10 noktayı yaz: kompozisyon, çizgi, renk dengesi, motif
işçiliği, ölçek hiyerarşisi, doku. Her biri için önerilen düzeltme. **Burak onaylar.**

### 2. Stil motoru
`minyatur.py`'yi yeniden düzenle:
- Tahrir: çizgi kalınlığında elden gelen nefes (uçlarda incelme), köşelerde hafif yuvarlanma.
- Boya: düz alanın içinde ölçülü fırça izi ve kenara doğru hafif koyulaşma (degrade değil, boya birikmesi).
- Motif kütüphanesi: rumi, hatayi, bulut, çintemani, geçme, çini — her biri parametrik ve aynı elden.
- Palet: mevcut renkler korunur; açık-koyu tonların sayısı ve kullanım oranları netleşir.
Çıktı: önce/sonra karşılaştırması (aynı sahne). **Burak onaylar.**

### 3. II. çağ asset'leri
Tablodaki her sprite'ı yeni motorla yeniden üret. Masa, belge, okuma görünümü ve karolar öncelikli.
Oyunda ekran görüntüsü al (komutlar aşağıda). **Burak onaylar**, istediği parçaları Illustrator'da
rötuşlar; rötuşlar koda geri işlenir.

### 4. Çağ I, III, IV
`STYLE.md`'deki çağ tablosuna göre her çağ için masa plakası + belge kâğıdı + karo çerçevesi:
- I Selçuklu: geometrik, kalın köşeli çizgi, kâğıt ve kırmızı, yıldız/geçme.
- III Taşra: naif, kalın titrek çizgi, eksik/taşkın boya, yamalar.
- IV Batılılaşma: perspektif ve gölge girer, lapis ve kırmızı pastelleşir.
Dosya adı düzeni: `masa_cag1.png`, `belge_kagit_cag1.png` vb. Çağ II adları aynen kalır.
Her çağ ayrı onay.

### 5. Hareket ve ince işler
Kâğıt kesik hareket (kayma, dönme, az ara kare), mürekkebin yazılışı, mühür basılması, istek
pusulasının üstten girişi. Sadece görsel/zamanlama; oyun mantığına dokunma.

## Kabul ölçütleri

- Her ekran tek elden çıkmış gibi; hiçbir parça "başka yerden toplanmış" görünmüyor.
- Belgelerde yazı alanı süslemeden geniş; 1280×720'de metin rahat okunuyor.
- Önemli nesneler iri, küçük eşyalar küçük; göz önce belgeye gidiyor.
- Testler: 0 hata. Web export'ta (GL Compatibility) görüntüler bozulmuyor.
- `assets/art/STYLE.md` yeni motora göre güncel.

## Komutlar

```
# Sprite'lar
cd tools/art && python3 minyatur.py --sprites

# Testler
godot --headless --import
godot --headless --script res://tests/run_tests.gd

# Oyundan ekran görüntüsü (Linux; macOS/Windows'ta xvfb-run olmadan)
SHOTS=/tmp/shots xvfb-run -s "-screen 0 1920x1080x24" godot --rendering-driver opengl3 \
  --resolution 1920x1080 --script res://tests/screenshot_desk.gd
```

## Çalışma kuralları

- Dil: Türkçe. Kararlar için seçenek sun, birini öner; karar Burak'ın.
- Takvim/tarih önerme; yalnızca görev.
- Her adım ayrı commit, doğrudan `main`'e. Commit mesajı sonuna:
  `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>`
- Bütçe: adım 1–2 high effort yeterli olabilir; xhigh'ı adım 3–4'ün uzun üretimleri için tut.
  Uzun oturumlarda `/compact` kullan.
