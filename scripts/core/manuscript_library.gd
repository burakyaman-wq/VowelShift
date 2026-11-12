class_name ManuscriptLibrary
extends RefCounted
## Loads every manuscript in data/manuscripts, sorted by `order`,
## and checks each one against the rule engine.

const DIR := "res://data/manuscripts"

var docs: Array[Manuscript] = []


func _init(dir: String = DIR) -> void:
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".json"):
			docs.append(Manuscript.from_dict(RuleEngine._read_json(dir.path_join(f))))
	docs.sort_custom(func(a, b): return a.order < b.order)


## The document with this id, or null.
func find(id: String) -> Manuscript:
	for m in docs:
		if m.id == id:
			return m
	return null


## Its place in the run (0-based), or -1.
func index_of(id: String) -> int:
	for i in docs.size():
		if docs[i].id == id:
			return i
	return -1


func get_doc(i: int) -> Manuscript:
	return docs[i] if i >= 0 and i < docs.size() else null


## Content errors a writer should fix. Empty array = the library is sound.
func validate(engine: RuleEngine) -> PackedStringArray:
	var errs: PackedStringArray = []
	var seen := {}
	for m in docs:
		if seen.has(m.order):
			errs.append("%s: order %d is used twice" % [m.id, m.order])
		seen[m.order] = true
		for text in m.all_old_texts():
			for tok in text.split(" ", false):
				var w := tok.trim_suffix(".").trim_suffix(",")
				if not engine.is_real(w, m.era - 1):
					errs.append("%s: '%s' is not an era-%d word" % [m.id, w, m.era - 1])
		var canonical: Array = []
		for rid in engine.era_ids(m.era):
			if engine.by_id[rid].era == m.era:
				canonical.append(rid)
		for w in m.old_words():
			var copy := engine.apply_word(w, canonical)
			if not engine.is_real(copy, m.era):
				errs.append("%s: correct copy '%s' of '%s' is not an era-%d word" % [m.id, copy, w, m.era])
		for h in m.heard:
			if not engine.is_real(h, m.era):
				errs.append("%s: heard word '%s' is not an era-%d word" % [m.id, h, m.era])
		for c in m.inherit_cards:
			if not engine.by_id.has(c):
				errs.append("%s: unknown inherited card %s" % [m.id, c])
		for c in m.cards:
			if not engine.by_id.has(c):
				errs.append("%s: unknown card %s" % [m.id, c])
		if m.ask != "" and m.options.size() < 2:
			errs.append("%s: question needs at least two options" % m.id)
	return errs
