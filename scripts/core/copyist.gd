class_name Copyist
extends RefCounted
## What the scribe's copy comes to, before and after the pen.
##
## A document's words go through the sound cards in the strip, left to right.
## The scribe may then lay a scribe card on a word:
##   not   a gloss in the margin: the word is written as it now sounds, and
##         its old meaning is noted beside it
##   eski  old spelling: the word is written as it was, unshifted
##   kazi  scraped: the word is left out of the copy
## A copy is weighed on two scales, each out of FULL:
##   fidelity  is the old meaning still there? A word newly fallen into
##             another word's form (more meanings than before) costs 1 unless glossed or kept old;
##             a word that now means something else costs 2 unless kept old;
##             a scraped word costs 1.
##   clarity   can today's reader read it? Each word kept in old spelling costs 1.

const FULL := 5
const TOOLS := ["not", "eski", "kazi"]
const TOOL_NAMES := {"not": "Kenar notu", "eski": "Eski yazım", "kazi": "Kazı"}

static var _meanings := {}


## What a word form means in an era; two or more when words have fallen together.
## Era 0 is the language before the first shift.
static func meanings(engine: RuleEngine, word: String, era: int) -> Array:
	if not _meanings.has(era):
		var ids := engine.era_ids(era)
		var m := {}
		for w in engine.words:
			for tag in w["forms"]:
				var f := engine.apply_word(w["forms"][tag], ids).to_lower()
				if not m.has(f):
					m[f] = []
				if w["meaning_tr"] not in m[f]:
					m[f].append(w["meaning_tr"])
		_meanings[era] = m
	return _meanings[era].get(word.to_lower().trim_suffix("."), [])


## Today's dictionary: [form, meaning], one entry per word, alphabetical.
static func dictionary(engine: RuleEngine, era: int) -> Array:
	var ids := engine.era_ids(era)
	var out := []
	for w in engine.words:
		out.append([engine.apply_word(w["root"], ids), w["meaning_tr"]])
	out.sort_custom(func(a: Array, b: Array) -> bool: return a[0].to_lower() < b[0].to_lower())
	return out


## The card that does not belong: the first shift of the era to come.
static func decoy(engine: RuleEngine, era: int) -> String:
	for r in engine.rules:
		if r.era == era + 1:
			return r.id
	return ""


## The sound cards dealt for a document: its era's shifts and one stranger.
static func hand(doc: Manuscript, engine: RuleEngine) -> Array:
	var out: Array = []
	for rid in engine.era_ids(doc.era):
		if engine.by_id[rid].era == doc.era:
			out.append(rid)
	for rid in doc.inherit_cards:
		if rid not in out:
			out.append(rid)
	var d := decoy(engine, doc.era)
	if d != "":
		out.append(d)
	return out


## {rows, copy, blocked, fidelity, clarity}
## rows: one per distinct word, in order of first appearance:
##   {key, old, new, final, mark, in_dict, collision, shifted, was, now}
## `marks` maps a word's key (lowercase) to a scribe card; `word_order` is the
## 1-based order of the copy's words when the scribe has moved them.
static func evaluate(doc: Manuscript, engine: RuleEngine, order: Array, proven: Dictionary,
		marks: Dictionary, word_order: Array = []) -> Dictionary:
	var rows := []
	var by_key := {}
	for w in doc.old_words():
		var key := w.to_lower()
		if by_key.has(key):
			continue
		var nw := engine.apply_text(w, order, proven)
		var was := meanings(engine, w, doc.era - 1)
		var now := meanings(engine, nw, doc.era)
		var mark: String = marks.get(key, "")
		var row := {
			"key": key, "old": w, "new": nw, "mark": mark,
			"final": w if mark == "eski" else ("" if mark == "kazi" else nw),
			"in_dict": not now.is_empty(),
			"collision": now.size() > 1 and now.size() > was.size(),
			"shifted": not was.is_empty() and not now.is_empty() and not _meet(was, now),
			"was": was, "now": now,
		}
		by_key[key] = row
		rows.append(row)
	var fidelity := FULL
	var clarity := FULL
	var blocked := PackedStringArray()
	for r in rows:
		match r["mark"]:
			"eski":
				clarity -= 1
			"kazi":
				fidelity -= 1
			_:
				if not r["in_dict"]:
					blocked.append(r["new"])
				elif r["shifted"]:
					fidelity -= 2
				elif r["collision"] and r["mark"] != "not":
					fidelity -= 1
	# The copy keeps the document's sentences: a full stop stays with its
	# sentence even when the word that carried it is scraped.
	var tokens: Array = []
	var stops: Array = []
	for tok in doc.old_text.split(" ", false):
		var bare := tok.trim_suffix(".")
		tokens.append(by_key[bare.to_lower()]["final"])
		stops.append(tok.ends_with("."))
	if word_order.size() == tokens.size():
		tokens = word_order.map(func(i: int) -> String: return tokens[i - 1])
	var words := PackedStringArray()
	for i in tokens.size():
		if tokens[i] != "":
			words.append(tokens[i])
		if stops[i] and not words.is_empty() and not words[-1].ends_with("."):
			words[-1] += "."
	var copy := " ".join(words)
	if not copy.ends_with("."):
		copy += "."
	return {
		"rows": rows, "copy": copy, "blocked": blocked,
		"fidelity": maxi(0, fidelity), "clarity": maxi(0, clarity),
	}


## The margin note a copy carries: every glossed word with its old meaning.
static func gloss(ev: Dictionary) -> String:
	var out := PackedStringArray()
	for r in ev["rows"]:
		if r["mark"] == "not":
			out.append("%s: %s" % [r["new"], " / ".join(PackedStringArray(r["was"]))])
	return "; ".join(out)


static func _meet(a: Array, b: Array) -> bool:
	for x in a:
		if x in b:
			return true
	return false
