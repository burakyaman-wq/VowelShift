# Üslup: Nakkaş Osman'ın masası

Oyun, klasik Osmanlı minyatürünün diliyle çizilmiş, tam üstten görülen bir kâtip masasıdır.
Her görsel aynı elden çıkmış gibi görünmeli; bunu aşağıdaki kurallar ve onları uygulayan kod
(`tools/art/minyatur.py`) sağlar. İlk deneme: `style/cag2_masa.png`, `style/cag2_okuma.png`.

## Kurallar

| Konu | Kural |
|---|---|
| Bakış | Tam üstten, düz. Perspektif ve gölge yok (IV. çağ hariç). |
| Çizgi | İnce, düzenli tahrir; koyu mürekkep `#2a1b14`, 1080p'de 2 px. Her renk alanının konturu var. |
| Renk | Kâğıt, mürekkep, lapis, kırmızı ve bu ikisinin açık-koyu tonları. Altın yok. Düz boya, degrade yok. |
| Yüzey | Bütün ekran tek boyalı sayfa: ortak kâğıt dokusu, hafif boya dalgalanması, konturlarda elden gelen hafif titreme. |
| Işık | Yok. Kandilin ışığı çizilmiş bir şeydir: soluk bir ışık dairesi ve yükselen alev dilleri. |
| Oran | Önem sırası: belge, kopya, karolar ve defter iri; kandil, hokka, kalem küçük. |
| Yoğunluk | Dengeli: orta açık, kâtibin eşyaları kenarlarda. |
| Desen | Ölçülü: halı bordürü, bohça (çintemani), çini karolar. Masa ve kâğıt düz. |
| Masa | Koyu kırmızı-kahve düz boyalı tahta, ince damar ve tahta ekleri; çevresinde halının lapis bordürü. |
| Kişiler | Yok. İstek, bıraktıkları nesne ve konuşmalarını taşıyan pusulayla gelir; ikisi üst kenardan kayarak girer. |
| Belgeler | Yazı önce: ince lapis ve kırmızı cetvel, küçük lapis başlık kartuşu, köşe parçaları, cümle sonlarında durak gülü. Metin sayfaya sığacak boyda yazılır. |
| Okuma görünümü | Belge ekranı doldurur; çerçeve yalnızca burada. |
| Yazı | Her yerde Katip. |
| Seçim | Üzerine gelinen nesnenin yanında küçük kırmızı durak gülü. |
| Hareket | Kâğıt kesik: düz kayma ve dönme, ara kare az. |

## Çağ kayması (tarihsel ekoller)

| Çağ | Ekol | Ne değişir |
|---|---|---|
| I | Selçuklu | Geometrik, taş oyma gibi; kalın köşeli çizgi; boya az (kâğıt ve kırmızı); geçme ve yıldız desenleri. |
| II | Klasik Osmanlı | Taban üslup (bu belge). |
| III | Taşra | Naif, kalın ve titrek çizgi; boya eksik ya da taşkın; yamalar. |
| IV | Batılılaşma | Perspektif ve gölge girer; lapis ve kırmızı pastelleşir. |

## Üretim

- Kod çizer: katmanlı SVG, grup adları Illustrator'da katman adı olur. Metinler Katip ile dış hatta çevrilir.
- AI görsel üretimi serbest (11 Kasım 2026). Çıktı bu kurallara uyar; her AI asset'i `AI_LOG.md`'ye
  yazılır (araç, model, istem, düzenleme). AI beyanı itch.io sayfasında açık kalır.
- Burak istediği nesneye Illustrator'da dokunur; değişen nesne koda geri işlenir ki kurallar korunsun.
- PNG: `rsvg-convert`, ardından ortak kâğıt dokusu ve boya dalgalanması.

```
cd tools/art && python3 minyatur.py
```
