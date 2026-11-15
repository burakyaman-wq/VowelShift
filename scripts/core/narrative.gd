class_name Narrative
extends RefCounted
## Turns the player's shelved copies, answers and notes into the rumour at
## the door and the epilogue. Texts live in data/narrative/outcomes.json.

const PATH := "res://data/narrative/outcomes.json"

var t: Dictionary


func _init(path: String = PATH) -> void:
	t = RuleEngine._read_json(path)


func copy_says_dead(state: GameState) -> bool:
	return String(state.copies.get("doc_02", "")).contains(t["key_word_wrong"])


## The scribe kept the old spelling, which no one can misread.
func copy_keeps_old(state: GameState) -> bool:
	return String(state.copies.get("doc_02", "")).contains(t["key_word_old"])


## One line after a copy is handed over.
func delivered(no: int) -> String:
	return String(t.get("delivered", {}).get(str(no), ""))


## Line shown before document 3, reacting to the document-2 copy and answer.
func rumour_doc3(state: GameState) -> String:
	var dead := copy_says_dead(state)
	var line: String = t["reaction_doc3"]["dead" if dead else ("old_spelling" if copy_keeps_old(state) else "exiled")]
	var a2 := String(state.answers.get("doc_02", ""))
	if a2 != "" and ((dead and a2.begins_with(Loc.t("Sürgün"))) or (not dead and a2 == Loc.t("Öldü"))):
		line += " " + t["reaction_doc3"]["contradiction"]
	return line


## How era-3 readers understand the document-4 copy: the first noun is the doer.
func city_reading_doc4(state: GameState) -> String:
	var ws := String(state.copies.get("doc_04", "")).to_lower().split(" ", false)
	if ws.size() >= 2 and ws[0].begins_with(Loc.t("mīro")) and ws[1].begins_with(Loc.t("rīgo")):
		return t["doc4"]["subject_first"]
	return t["doc4"]["object_first"]


## The ending, a paragraph per document. A person met twice is introduced once.
func epilogue(state: GameState) -> String:
	var e: Dictionary = t["epilogue"]
	var first: String = e["doc2_dead"] if copy_says_dead(state) else (e["doc2_old_spelling"] if copy_keeps_old(state) else e["doc2_exiled"])
	var parts: PackedStringArray = [first]
	var has_copy4 := state.copies.has("doc_04")
	if has_copy4:
		if city_reading_doc4(state) == t["doc4"]["object_first"]:
			parts.append(e["doc4_literal"])
		else:
			parts.append(e["doc4_reordered"] + " " + (e["doc4_reordered_with_note"] if state.notes.has("doc_04") else e["doc4_reordered_no_note"]))
	var a4 := String(state.answers.get("doc_04", ""))
	if a4 == t["doc4"]["unclear_option"]:
		parts.append(e["doc4_answer_unclear"])
	elif a4 != "" and has_copy4 and a4 != city_reading_doc4(state):
		parts.append(e["doc4_answer_mismatch"])
	# only the margin notes the story has a fate for, in story order
	for id in e["note_fates"]:
		if state.notes.has(id):
			parts.append(String(e["note_prefix"]).format({"title": state.titles.get(id, id), "note": state.notes[id]}) + " " + String(e["note_fates"][id]))
	var out := "\n\n".join(parts)
	var intro := Loc.t("eni düzenin ölü dil uzmanı Melno")
	var at := out.find(intro)
	if at >= 0:
		var head := out.substr(0, at + intro.length())
		out = head + out.substr(head.length()).replace("Y" + intro, "Melno").replace("y" + intro, "Melno")
	return out


## The ending of the full run: what old Melno wrote fifty years on, one
## paragraph for each thing the city came to believe. Built from story flags.
func ending(state: GameState) -> String:
	var f := state.flags
	var out := PackedStringArray()
	# 1. What happened to Mēros
	if f.has("kronik_sessiz"):
		out.append(Loc.t("Kroniğin ilk satırında öldürmek yok. Okullarda kurucunun kardeşinin bir gün ortadan kaybolduğu öğretiliyor; kimse nasıl olduğunu sormuyor."))
	elif f.has("kronik_gercek") and (f.has("sayfa_okundu") or f.has("melno_anladi")):
		out.append(Loc.t("Okullarda kurucunun, kardeşini sürgünde öldürttüğü öğretiliyor. Melno, bu gerçeğin yüz yıl boyunca bir yanlış okumadan doğan söylentiyle yaşadığını yazdı: yaşlılar 'sürgün' kelimesini 'ölü' diye duymuştu ve haklıydılar."))
	elif f.has("kronik_gercek"):
		out.append(Loc.t("Kronik, beyin sürgün kardeşini öldürdüğünü yazıyor. Ama bunun nasıl bilindiğini kimse hatırlamıyor; çoğu kişi yeni düzenin uydurduğunu düşünüyor."))
	else:
		out.append(Loc.t("Kurucunun kardeşine ne olduğu hâlâ tartışılıyor."))
	if f.has("kazi_yapildi") or f.has("meros_kazindi"):
		out.append(Loc.t("Eski tabletlerde sürgünün adı yok; yalnız kazı izleri var. Melno o izleri 'kâtiplerin sessizliği' diye andı."))
	# 2. The mountain people
	if f.has("daglilar_suclu") and f.has("ilan_dogru"):
		out.append(Loc.t("Dağlılar önce kendi belgeleriyle suçlu sayıldı; sonra meydana asılan ilan onları akladı. Yine de şehre inen ilk kuşak taşlandı."))
	elif f.has("daglilar_suclu"):
		out.append(Loc.t("Dağlılar kendi belgeleriyle suçlu ilan edildi. Dağ yolu elli yıldır kapalı."))
	elif f.has("dag_aklandi") and (f.has("miras_daglilara") or f.has("tarla_daglilara")):
		out.append(Loc.t("Dağlılar aklandı; atalarının tarlası onlara verildi. Bugün şehrin pazarında dağ yünü satılıyor."))
	elif f.has("dag_aklandi"):
		out.append(Loc.t("Dağlılar aklandı ama şehre dönmedi. Yalnız elçinin torunu her yıl kapıdaki barış yazısını okumaya gelir."))
	# 3. The granary family
	if f.has("miras_daglilara"):
		out.append(Loc.t("Sālwa'nın soyu borçtan kurtuldu ve ambarı geri aldı. Grēna'nın torunu yazıhaneye bir çuval tahıl bıraktı."))
	elif f.has("miras_saraya"):
		out.append(Loc.t("Sālwa'nın soyu borçla kaldı; ambar saray deposu olarak kullanılıyor."))
	# 4. How the scribes are remembered
	var scraped := 0
	for k in ["tarla_kazindi", "kitlik_kazindi", "mektup_kazindi", "meros_kazindi", "kutuk_kazindi", "kazi_yapildi", "kutuk_temiz", "kronik_sessiz"]:
		if f.has(k):
			scraped += 1
	var noted := state.notes.size()
	if scraped >= 3:
		out.append(Loc.t("Melno, Leuka'dan Nīka'ya uzanan kâtip zincirini 'sarayın kalemi' diye andı: %d kez bir şey sildiler. Kenarlarda yine de %d not bıraktılar.") % [scraped, noted])
	elif f.has("dag_aklandi") and state.scores.has("doc_04") and not state.notes.has("doc_04"):
		out.append(Loc.t("Melno, kâtip zincirini hem çevirmen hem sahteci diye andı: son kâtip sırayı değiştirmiş ama nedenini yazmamıştı."))
	elif noted >= 6:
		out.append(Loc.t("Melno, Leuka'dan Nīka'ya uzanan kâtip zincirini 'çevirmenler' diye andı: kenarlara %d not bırakmışlardı; sözlüğünü onlardan derledi.") % noted)
	else:
		out.append(Loc.t("Melno, kâtip zincirinden az söz etti: kopyaları doğruydu, ama kenarları boştu."))
	return "\n\n".join(out)
