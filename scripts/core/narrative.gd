class_name Narrative
extends RefCounted
## Turns the player's shelved copies, answers and notes into the rumour at
## the door and the epilogue. Texts live in data/narrative/outcomes.json.

const PATH := "res://data/narrative/outcomes.json"

var t: Dictionary


func _init(path: String = PATH) -> void:
	t = RuleEngine._read_json(path)


func copy_says_dead(state: GameState) -> bool:
	return String(state.copies.get("2", "")).contains(t["key_word_wrong"])


## Line shown before document 3, reacting to the document-2 copy and answer.
func rumour_doc3(state: GameState) -> String:
	var dead := copy_says_dead(state)
	var line: String = t["reaction_doc3"]["dead" if dead else "exiled"]
	var a2 := String(state.answers.get("2", ""))
	if a2 != "" and ((dead and a2.begins_with("Sürgün")) or (not dead and a2 == "Öldü")):
		line += " " + t["reaction_doc3"]["contradiction"]
	return line


## How era-3 readers understand the document-4 copy: the first noun is the doer.
func city_reading_doc4(state: GameState) -> String:
	var ws := String(state.copies.get("4", "")).to_lower().split(" ", false)
	if ws.size() >= 2 and ws[0].begins_with("mīro") and ws[1].begins_with("rīgo"):
		return t["doc4"]["subject_first"]
	return t["doc4"]["object_first"]


func epilogue(state: GameState) -> String:
	var e: Dictionary = t["epilogue"]
	var parts: PackedStringArray = [e["doc2_dead"] if copy_says_dead(state) else e["doc2_exiled"]]
	var has_copy4 := state.copies.has("4")
	if has_copy4:
		if city_reading_doc4(state) == t["doc4"]["object_first"]:
			parts.append(e["doc4_literal"])
		else:
			parts.append(e["doc4_reordered"])
			parts.append(e["doc4_reordered_with_note"] if state.notes.has("4") else e["doc4_reordered_no_note"])
	var a4 := String(state.answers.get("4", ""))
	if a4 == t["doc4"]["unclear_option"]:
		parts.append(e["doc4_answer_unclear"])
	elif a4 != "" and has_copy4 and a4 != city_reading_doc4(state):
		parts.append(e["doc4_answer_mismatch"])
	var keys := state.notes.keys()
	keys.sort_custom(func(a, b): return int(a) < int(b))
	for no in keys:
		parts.append(String(e["note_prefix"]).format({"no": no, "note": state.notes[no]}) + " " + String(e["note_fates"].get(no, "")))
	return " ".join(parts)
