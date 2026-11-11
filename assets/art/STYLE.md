# Üslup: nakkaşın masası, dört ekolde

Oyun, tam üstten görülen bir kâtip masasıdır ve bir minyatür gibi boyanmıştır. Çağ değiştikçe
resmi yapan ekol değişir: aynı masa, başka bir yüzyılın eliyle. Her görsel aynı elden çıkmış
gibi görünmeli; bunu aşağıdaki kurallar ve onları uygulayan kod (`tools/art/`) sağlar.

Bakmak için: `style/dort_cag.png` (aynı masa dört ekolde), `style/cagN_masa.png`,
`style/cagN_okuma.png`, `style/sayfa_cagN.png` (çağın bütün parçaları).

## Değişmeyen kurallar

| Konu | Kural |
|---|---|
| Bakış | Tam üstten, düz. |
| Yüzey | Bütün ekran tek boyalı sayfa. Boya önce sürülür, tahrir sonra çekilir. |
| Boya | Düz alanlar; degrade yok. Canlılık pigmentten gelir: öğütülmüş boyanın tanesi, kenarda biriken boya, fırçanın izi. |
| Çizgi | Koyu mürekkeple tahrir; her renk alanının konturu var. Kalınlığı çağa göre değişir, ama bir resimde tek kalınlık ailesi. |
| Renk | Kâğıt, mürekkep, lapis, kırmızı ve bunların açık-koyu tonları. Altın yok. |
| Oran | Önem sırası: belge, kopya, karolar ve defter iri; kâtibin eşyaları küçük ve kenarlarda. |
| Desen | Ölçülü: bordür, bohça, karolar. Masa ve yazı alanı düz. |
| Kişiler | Yok. İstek, bıraktıkları nesne ve pusulayla gelir; ikisi üst kenardan kayarak girer. |
| Belgeler | Yazı önce: ince cetvel, küçük başlık, köşe parçaları. Tam tezhip yalnızca okuma görünümünde. |
| Yazı | Her yerde Katip. |
| Seçim | Üzerine gelinen nesnenin yanında küçük kırmızı durak gülü. |
| Hareket | Kâğıt kesik: düz kayma ve dönme, ara kare az. |

## Dört ekol

| | I Selçuklu | II Klasik Osmanlı | III Taşra | IV Batılılaşma |
|---|---|---|---|---|
| Boya | Az: kâğıt, mürekkep, iki kırmızı. Lapis henüz yok. | Lapis ve kırmızı, tam parlaklıkta. | Ucuz pigment: çivit mavisi, aşı kırmızısı, esmer kâğıt. | Pastel mavi ve gül kurusu; kâğıt beyaza yakın. |
| Çizgi | Kalın, köşeli. | İnce, düzenli. | Kalın, titrek. | En ince; gravür gibi. |
| El | Emin ama sade. | Usta. | Boya çizgiden taşar ya da ona varmaz; bazı çiçekler boyanmadan kalmış. | Titreme yok; baskı gibi temiz. |
| Bordür | Kilim: iki kırmızının geçmesi, köşelerde sekiz kollu yıldız. | Halı: lapis üstünde kıvrık dal, rumi, penç. | Aynı kıvrık dalın hatırlandığı kadarı: az ve iri çiçek. | Halı yok: sol üstten ışık alan pervaz, çelenk ve güller. |
| Masa | Üç tahta, ahşap çiviler, köşelerde oyma yıldız. | Dört tahta, kenarda kemik filato. | Eğri tahtalar, çiviler, yama, yanık izleri. | Cilalı açık ahşap; ışığı yansıtır. |
| Işık | Çizilmiş: iki kareden yıldız, üç alev dili. | Çizilmiş: şemse, tığlar, alev dilleri. | Şemsenin kabası. | Gerçek: lamba çevresini ısıtır, uzak köşe kararır, eşyaların gölgesi düşer. |
| Eşyalar | Çanak kandil, taş hokka, deniz kabuğunda kırmızı, bıçak, çentikli cetvel, dayanakta iki kamış. | Çini kandil, lake kalemdan, iki hokka, makas, kalemtıraş, makta, mühre, rıhdan, çintemanili bohça. | Yangından kalanlar: yanık kalemdan, tek hokka, bıçak, çuval. | Camlı lamba, tüy kalem, cam hokka, cep saati, gözlük, mühürlü zarf. |
| Belge | Kalın kırmızı cetvel, kulaklı tablet başlık, köşelerde yıldızlı düğüm. Okumada: geçme bordür, testere dişi. | Lapis cetvel, sivri kartuş ve dalları, köşebent. Okumada: zencerek ve tığlar. | II'nin yamalı hâli. | Çift gravür çizgisi, kurdele başlık, köşelerde gül. Okumada: çelenk. |
| Karo | Taş rengi kil, kırmızı çerçeve. | İznik: beyaz sır, kobalt, köşede lale. | Köy çinicisi: kalın kobalt, iri benek. | Pastel baskı; kenarı ışık alan pahlı karo. |

## Kim hangi ekolü giyer

Kaymayı oyuncuya gösteren şey, aynı masada farklı çağların yan yana durmasıdır.

- **Masa ve kâtibin eşyaları** (plaka, defter, kopya kâğıdı, pusula, tepsi, kalem, mühür): belgenin çağı.
- **Kopyalanan belge**: bir önceki çağ. Belge masadan eskidir (I. çağda daha eskisi olmadığından kendi çağı).
- **Kural karosu**: kuralın bulunduğu çağ. Karo doğduğu günkü hâliyle kalır; ileriki çağlarda masada
  dört ekolün karoları birlikte durur.
- **Gölge**: IV. çağdan itibaren serbest duran her şeyin altında.

Kod: `scripts/ui/art.gd`.

## Üretim

| Dosya | İşi |
|---|---|
| `tools/art/nakkas.py` | Çekirdek. Resim bir gösterim listesidir; boya ve tahrir ayrı katmanlarda çizilir, sonra `pigment()` boyar: tane, kenar birikmesi, fırça izi, nefesli çizgi, ortak el titremesi. |
| `tools/art/motif.py` | Palet, dört ekolün ayarları, motifler: penç, lale, karanfil, rumi, çintemani, zencerek, kıvrık dal, geçme, yıldız, kartuş, köşebent, tığ, gül, çelenk, yanık. |
| `tools/art/masa.py` | Her çağın masa plakası ve eşyaları. |
| `tools/art/kagit.py` | Belgeler, kopya kâğıdı, pusula, defter. |
| `tools/art/karo.py` | Karolar, piktogramlar, tepsi, durak, mühür. |
| `tools/art/minyatur.py` | Dışa aktarım. |

```
cd tools/art
python3 minyatur.py              # dört çağın bütün sprite'ları (iki çekirdekte yaklaşık 2 dakika)
python3 minyatur.py 1 masa karo  # yalnızca I. çağın adı geçenleri
python3 minyatur.py --sheet      # style/sayfa_cagN.png
```

- II. çağ sprite'ları yalın adla durur (`belge_kagit.png`); ötekiler `_cagN` alır. Olmayan sprite yalın ada düşer.
- Her sprite'ın katmanlı SVG'si `style/sprites_src/` içindedir; grup adları Illustrator'da katman adı olur.
  Burak istediği nesneye Illustrator'da dokunur; değişiklik koda geri işlenir ki kurallar korunsun.
- Bir ekolün eli `motif.py` içindeki `ERAS` tablosundan ayarlanır: çizgi kalınlığı, titreme, çizginin boyayı
  ne kadar ıskaladığı, boyanın ne kadar taştığı, çizginin nefesi, pigmentin kabalığı.
- AI görsel üretimi serbest (11 Kasım 2026), ama şu ana kadar kullanılmadı: bütün görseller koddan çıkıyor.
  Kullanılırsa çıktı bu kurallara uyar ve `AI_LOG.md`'ye yazılır. AI beyanı itch.io sayfasında açık kalır.
