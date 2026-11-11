# Ses Kayması — oyuncu rehberi

Sen bir yazıhanede kâtipsin. Masana eski metinler gelir; dil yüzyıllar içinde kaydığı için onları bugünün yazısıyla kopyalaman gerekir.

## Dilbilgisi
| Ek | Görev | Örnek |
|---|---|---|
| -os | özne (yapan) | dīwos = tanrı |
| -om | nesne (-ı, -i) | dīwom = tanrıyı |
| -osyo | iyelik (-ın, -in) | dīwosyo = tanrının |
| o → e | çoğul | dīwes = tanrılar |
| -eti | fiil: yapar | dōneti = verir |

Cümle düzeni Türkçedeki gibi: Özne — Nesne — Fiil. Fiilsiz cümle "-dır" demektir: "Mīros rēgos." = Mīros beydir.

## Her belgede işin
1. **Oku:** Eski metnin kelimelerini sözlüğündeki bugünkü kelimelerle eşleştir. Talep sahibinin konuşmasındaki *italik* kelimeler bugünün dilinden.
2. **Kural bul:** Bir ses değişimini fark edince masaya söyle. Masa ancak İKİ örnek çiftle kanıtlarsan kural kartını verir:
   `python3 masa.py <adın> kural "gh -> kh" eskiKelime:yeniKelime eskiKelime:yeniKelime`
3. **Kopyala:** Kartlarını istediğin sırayla tablete diz. Her kelimeye kartları soldan sağa uygula ve kopyayı kendin yaz. Masa yalnızca kopyandaki kelimelerin gerçek kelime olup olmadığını söyler:
   `python3 masa.py <adın> kopyala "R1,R2" "kopya metni"`
4. **Cevapla:** Talep sahibinin sorusunu kendi kopyandan cevapla:
   `python3 masa.py <adın> cevap "cevabın"`

Durumu görmek için: `python3 masa.py <adın> durum`
