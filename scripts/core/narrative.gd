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
	if a2 != "" and ((dead and a2.begins_with("Sürgün")) or (not dead and a2 == "Öldü")):
		line += " " + t["reaction_doc3"]["contradiction"]
	return line


## How era-3 readers understand the document-4 copy: the first noun is the doer.
func city_reading_doc4(state: GameState) -> String:
	var ws := String(state.copies.get("doc_04", "")).to_lower().split(" ", false)
	if ws.size() >= 2 and ws[0].begins_with("mīro") and ws[1].begins_with("rīgo"):
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
	var intro := "eni düzenin ölü dil uzmanı Melno"
	var at := out.find(intro)
	if at >= 0:
		var head := out.substr(0, at + intro.length())
		out = head + out.substr(head.length()).replace("Y" + intro, "Melno").replace("y" + intro, "Melno")
	return out
