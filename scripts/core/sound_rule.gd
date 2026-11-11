class_name SoundRule
extends RefCounted
## One sound change (a card in the game). A rule holds one or more
## sub-changes ("subs"); the player may have proven only some of them.

var id: String
var era: int
var kind: String
var name_tr: String
var note_tr: String
var patterns: Array[String] = []
var replacements: Array[String] = []
var _compiled: Array[RegEx] = []


static func from_dict(d: Dictionary, classes: Dictionary) -> SoundRule:
	var r := SoundRule.new()
	r.id = d["id"]
	r.era = int(d["era"])
	r.kind = d.get("kind", "")
	r.name_tr = d.get("name_tr", "")
	r.note_tr = d.get("note_tr", "")
	for sub in d["subs"]:
		var pat: String = sub[0]
		for cls_name in classes:
			pat = pat.replace("{%s}" % cls_name, classes[cls_name])
		var rx := RegEx.new()
		var err := rx.compile(pat)
		assert(err == OK, "Bad pattern in %s: %s" % [r.id, pat])
		r.patterns.append(sub[0])
		r.replacements.append(sub[1])
		r._compiled.append(rx)
	return r


func sub_count() -> int:
	return _compiled.size()


## Apply this rule to a lowercase word. `only` limits it to the given
## sub indices (the ones the player has proven); empty = all subs.
func apply(word: String, only: Array = []) -> String:
	for i in _compiled.size():
		if only.is_empty() or i in only:
			word = _compiled[i].sub(word, replacements[i], true)
	return word
