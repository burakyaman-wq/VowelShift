class_name RuleEngine
extends RefCounted
## Loads the sound rules and lexicon and derives word forms across eras.
## Mirrors tools/simulate.py; tests/run_tests.gd keeps the two in sync.

const RULES_PATH := "res://data/rules/rules.json"
const WORDS_PATH := "res://data/words/words.json"

var rules: Array[SoundRule] = []
var by_id: Dictionary = {}
var words: Array = []
var _real_cache: Dictionary = {}
var _names: Dictionary = {}


func _init(rules_path: String = RULES_PATH, words_path: String = WORDS_PATH) -> void:
	var rd: Dictionary = _read_json(rules_path)
	for d in rd["rules"]:
		var r := SoundRule.from_dict(d, rd.get("classes", {}))
		rules.append(r)
		by_id[r.id] = r
	words = _read_json(words_path)["words"]
	if Loc.lang == "en" and words_path == WORDS_PATH:
		var en: Dictionary = _read_json("res://data/words/meanings_en.json")
		for w in words:
			w["meaning_tr"] = en.get(str(int(w["id"])), w["meaning_tr"])


static func _read_json(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	assert(f != null, "Cannot open %s" % path)
	var data = JSON.parse_string(f.get_as_text())
	assert(data is Dictionary, "Bad JSON in %s" % path)
	return data


## Canonical rule ids up to and including `era`.
func era_ids(era: int) -> Array[String]:
	var out: Array[String] = []
	for r in rules:
		if r.era <= era:
			out.append(r.id)
	return out


## Apply rules in the given order. `proven` maps rule id -> Array of sub
## indices; a rule missing from it (or an empty map) applies fully.
func apply_word(word: String, order: Array, proven: Dictionary = {}) -> String:
	var cap := word.length() > 0 and word[0] != word[0].to_lower()
	var w := word.to_lower()
	for rid in order:
		var only: Array = proven.get(rid, [])
		w = by_id[rid].apply(w, only)
	if cap and w.length() > 0:
		w = w[0].to_upper() + w.substr(1)
	return w


## Apply to a sentence, keeping sentence punctuation on each token.
func apply_text(text: String, order: Array, proven: Dictionary = {}) -> String:
	var out: PackedStringArray = []
	for tok in text.split(" ", false):
		var dot := tok.ends_with(".")
		var core := tok.trim_suffix(".")
		out.append(apply_word(core, order, proven) + ("." if dot else ""))
	return " ".join(out)


## Every inflected lexicon form as written in `era` (lowercase).
func real_words(era: int) -> Dictionary:
	if _real_cache.has(era):
		return _real_cache[era]
	var ids := era_ids(era)
	var s := {}
	for w in words:
		for tag in w["forms"]:
			s[apply_word(w["forms"][tag], ids).to_lower()] = true
	_real_cache[era] = s
	return s


## Is this word (any era's form) a name? Names keep their capital wherever they stand.
func is_name(word: String) -> bool:
	if _names.is_empty():
		for w in words:
			if w.get("domain", "") == "proper":
				for f in w["forms"].values():
					for e in range(0, 5):
						_names[apply_word(f, era_ids(e)).to_lower()] = true
	return _names.has(word.to_lower())


func is_real(word: String, era: int) -> bool:
	return real_words(era).has(word.to_lower().trim_suffix("."))
