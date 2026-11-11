# Belge formatı

Her belge `data/manuscripts/` içinde bir JSON dosyasıdır. Oyun hepsini `order` alanına göre sıralar.

```json
{
  "id": "doc_02",
  "order": 2,
  "era": 2,
  "title_tr": "Kurucuların kaydı",
  "intro_tr": "",
  "requester": {"name_tr": "Saray görevlisi", "says_tr": "*Rīgos* kurucuların kaydını istiyor…"},
  "old_text": "Mīros Mērom ageti. Mēros nākos.",
  "heard": ["rīgos", "grēnos", "ēgros", "thītos"],
  "inherit_cards": [],
  "allow_reorder": false,
  "question": {"ask_tr": "Kurucunun kardeşine ne oldu?", "options_tr": ["Sürgün edildi", "Öldü", "…"]}
}
```

| Alan | Anlamı |
|---|---|
| `era` | Belgenin geldiği çağ. `old_text` bir önceki çağın yazısıyla yazılır; oyuncu onu bu çağa kopyalar. |
| `intro_tr` | Belge açılmadan önce gösterilen geçiş metni (çağ değişimi, önceki kâtibin notu). Boş olabilir. |
| `requester.says_tr` | Talep sahibinin repliği. `*italik*` kelimeler bugünün dilinden; oyuncu bunları kural kanıtı olarak kullanabilir. |
| `heard` | Repliğin bu çağdaki kelimeleri (kanıt için "duyulmuş" sayılır). Repliktekilerle aynı olmalı. |
| `inherit_cards` | Belge başında hazır verilen kartlar (örn. ustanın defterinden). |
| `allow_reorder` | Oyuncu kopyada kelimelerin sırasını değiştirebilir mi. |
| `question` | Belge sonunda talep sahibinin sorusu ve seçenekler. |

## Denetim
`godot --headless --script res://tests/run_tests.gd` her belgeyi kural motoruyla denetler:
- `old_text` kelimeleri bir önceki çağda gerçek kelime mi,
- doğru sırayla kopyası bu çağda gerçek kelime mi,
- `heard` kelimeleri bu çağda gerçek mi,
- miras kartlar var mı, en az iki seçenek var mı.
