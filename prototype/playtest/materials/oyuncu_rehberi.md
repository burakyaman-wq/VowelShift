# Ses Kayması — oyuncu rehberi

Sen bir yazıhanede kâtipsin. Masana eski metinler gelir; dil yüzyıllar içinde kaydığı için onları bugünün yazısıyla kopyalaman gerekir.

## Dilbilgisi
| Ek | Ne demek | Örnek |
|---|---|---|
| -os | yapan kişi ya da şey | dīwos = tanrı |
| -om | -ı, -i (etkilenen) | dīwom = tanrıyı |
| -osyo | -nın, -nin (sahiplik) | dīwosyo = tanrının |
| o → e | çoğul | dīwes = tanrılar |
| -eti | fiil: yapar | dōneti = verir |

Cümle düzeni Türkçedeki gibi: yapan — etkilenen — fiil. Fiilsiz cümle "-dır" demektir: "Mīros rēgos." = Mīros beydir.

**Uzun ünlüler:** ā ē ī ō ū üstü çizgili harflerdir; çizgisiz a e i o u'dan farklıdır. Yazamıyorsan çift harf kullan: aa = ā, ee = ē, ii = ī, oo = ō, uu = ū.

## Her belgede işin
1. **Oku:** Eski metnin kelimelerini sözlüğündeki bugünkü kelimelerle eşleştir. Talep sahibinin konuşmasındaki *italik* kelimeler bugünün dilinden.
2. **Kural kanıtla:** Bir ses değişimini fark edince masaya söyle. Masa ancak İKİ örnek çiftle kanıtlarsan kartı verir. Örnekler senin gördüğün kelimelerden olmalı: eski kelime masadaki metinden (ya da eski sözlüğünden), yeni kelime sözlüğünden ya da talep sahibinden. **Örnek çiftte ekler aynı olmalı:** eski kelime -om ile bitiyorsa yeni kelime de -om ile bitmeli (`ghewom:khewom`); sözlükteki kelimeye dilbilgisi kartındaki eki kendin ekleyebilirsin. Kart yalnızca kanıtladığın değişimi içerir; aynı kartın başka bir değişimini ayrıca kanıtlarsan kart güncellenir.
   `python3 masa.py <adın> kural "gh -> kh" eskiKelime:yeniKelime eskiKelime:yeniKelime`
3. **Kopyala:** Kartlarını istediğin sırayla tablete diz; masa her kelimeye kartları soldan sağa uygular ve kopyayı yazar. Bu çağın dilinde olmayan bir kelime çıkarsa kopya rafa konmaz.
   `python3 masa.py <adın> kopyala "kartadi1,kartadi2"`
   Masa izin verirse kelimelerin sırasını da değiştirebilirsin: `kopyala "kartlar" "3,4,1,2,5"` (numaralar eski metindeki kelime sırası).
   Ses kaybını yazmak için: `kural "-s -> ∅" ...` ya da `kural "-m -> ∅" ...`. Bir ek düşüyorsa yeni kelimede o ek görünmez; bu durumda ek uyumu şartı aranmaz.
4. **Not düş (isteğe bağlı):** Rafa konan kopyanın kenarına bir not bırakabilirsin; sonraki kâtipler okur.
   `python3 masa.py <adın> not "notun"`
5. **Cevapla:** Talep sahibi bir soru sorar; seçeneklerden birini seç.
   `python3 masa.py <adın> cevap <numara>`

Durumu görmek için: `python3 masa.py <adın> durum`
