class_name GameState
extends RefCounted
## Everything the player has done: cards, proven sub-rules, shelved copies,
## answers and margin notes. Copies carry forward unchanged (persistent
## errors); Narrative reads this state to build rumours and the epilogue.

const SAVE_PATH := "user://save.json"
const LONG_VOWELS := {"aa": "ā", "ee": "ē", "ii": "ī", "oo": "ō", "uu": "ū"}

var doc_index := 0
var phase := "read"          # "read" -> "answer" -> next document
var cards: Array[String] = []
var proven: Dictionary = {}  # rule id -> Array[int] of proven sub indices
var copies: Dictionary = {}  # doc id -> shelved copy text
var answers: Dictionary = {} # doc id -> chosen option text
var notes: Dictionary = {}   # doc id -> margin note
var titles: Dictionary = {}  # doc id -> title, for every shelved copy
var flags: Dictionary = {}   # story flags set by delivered copies
var chronicle: Array = []    # [{"doc": id, "line": text}] in the order written


## Call when a document is put on the desk: hands over inherited cards.
func begin_doc(doc: Manuscript, engine: RuleEngine) -> void:
	phase = "read"
	tools = TOOLS_PER_DOC.duplicate()
	if not doc.tools.is_empty():
		tools = {"not": int(doc.tools.get("not", 0)), "eski": int(doc.tools.get("eski", 0)), "kazi": int(doc.tools.get("kazi", 0))}
	for rid in doc.inherit_cards:
		if rid not in cards:
			cards.append(rid)
			proven[rid] = range(engine.by_id[rid].sub_count())


# --- Proving a rule -------------------------------------------------------

static func normalize(s: String) -> String:
	s = s.strip_edges()
	for k in LONG_VOWELS:
		s = s.replace(k, LONG_VOWELS[k])
	return s


static func inflections(form: String) -> Dictionary:
	var f := form.to_lower()
	var out := {f: true}
	if f.ends_with("os"):
		var st := f.substr(0, f.length() - 2)
		for e in ["os", "om", "osyo", "es", "em", "esyo"]:
			out[st + e] = true
	elif f.ends_with("eti"):
		out[f.substr(0, f.length() - 3) + "e"] = true
	return out


## Old forms the player can see: this document plus the previous era's dictionary.
func visible_old(doc: Manuscript, engine: RuleEngine) -> Dictionary:
	var s := {}
	for w in doc.old_words():
		s[w.to_lower()] = true
	if doc.era >= 2:
		var prev := engine.era_ids(doc.era - 1)
		for w in engine.words:
			if w["pos"] == "noun" or w["pos"] == "verb":
				s.merge(inflections(engine.apply_word(w["root"], prev)))
	return s


## Current-era forms the player has seen or heard so far.
func visible_new(doc: Manuscript, lib: ManuscriptLibrary, engine: RuleEngine) -> Dictionary:
	var s := {}
	if doc.era == 1:
		for w in engine.words:
			s.merge(inflections(engine.apply_word(w["root"], engine.era_ids(1))))
	for m in lib.docs:
		if m.era == doc.era and m.order <= doc.order:
			for h in m.heard:
				s.merge(inflections(h))
	return s


## Player claims `frm -> to`, backed by two "old:new" example pairs.
## Returns {ok, card, updated, problems: PackedStringArray}.
func prove_rule(doc: Manuscript, lib: ManuscriptLibrary, engine: RuleEngine,
		claim_from: String, claim_to: String, pairs: Array) -> Dictionary:
	var frm := normalize(claim_from)
	var to := normalize(claim_to)
	if to in ["", "∅", "Ø", "-", "0"]:
		to = ""
	if frm.begins_with("-"):
		frm = frm.substr(1) + "$"
	elif to == "" and not frm.ends_with("$"):
		frm += "$"

	var new_ids: Array = []
	for rid in engine.era_ids(doc.era):
		if engine.by_id[rid].era == doc.era:
			new_ids.append(rid)
	var hit := ""
	var hit_i := -1
	for rid in new_ids:
		var r: SoundRule = engine.by_id[rid]
		for i in r.sub_count():
			if r.patterns[i] == frm and r.replacements[i] == to:
				hit = rid
				hit_i = i

	var problems: PackedStringArray = []
	var vo := visible_old(doc, engine)
	var vn := visible_new(doc, lib, engine)
	var olds := {}
	for p in pairs:
		var parts: PackedStringArray = normalize(String(p)).to_lower().split(":")
		if parts.size() != 2:
			problems.append("'%s' eski:yeni biçiminde değil" % p)
			continue
		var old := parts[0].trim_suffix(".")
		var nw := parts[1].trim_suffix(".")
		olds[old] = true
		var rx := RegEx.new()
		rx.compile(frm)
		if not vo.has(old):
			problems.append("'%s' masada görünen eski bir kelime değil" % old)
		elif not vn.has(nw):
			problems.append("'%s' henüz bu çağda duyduğun ya da sözlüğünde olan bir kelime değil" % nw)
		elif rx.search(old) == null:
			problems.append("'%s' içinde '%s' yok" % [old, frm.trim_suffix("$")])
		elif engine.apply_word(old, new_ids) != nw:
			problems.append("'%s → %s' bu değişimi göstermiyor" % [old, nw])
	if olds.size() < 2:
		problems.append("iki farklı örnek gerekiyor")

	if hit == "" or not problems.is_empty():
		return {"ok": false, "card": hit, "updated": false, "problems": problems}
	var updated := hit in cards
	if not proven.has(hit):
		proven[hit] = []
	if hit_i not in proven[hit]:
		proven[hit].append(hit_i)
	if hit not in cards:
		cards.append(hit)
	return {"ok": true, "card": hit, "updated": updated, "problems": problems}


# --- Copying ---------------------------------------------------------------

## The desk writes the copy from the card order (only proven subs apply).
## `reorder` is a 1-based word order, allowed only if the document permits it.
## Returns {copy, rejected: PackedStringArray, shelved: bool, error: String}.
## The scribe cards left for the rest of the work. They are spent when a
## copy that uses them is shelved.
## Scribe cards for the document on the desk; a fresh set comes with every document.
const TOOLS_PER_DOC := {"not": 3, "eski": 2, "kazi": 1}
var tools := TOOLS_PER_DOC.duplicate()
## Per document: {"fidelity": n, "clarity": n}.
var scores := {}


## Shelve a copy the desk has weighed (Copyist.evaluate). Refused while a word
## is not a word of the era, or when the scribe cards it uses are spent.
func shelve(doc: Manuscript, ev: Dictionary, marks: Dictionary) -> Dictionary:
	if phase != "read":
		return {"shelved": false, "error": "already_copied"}
	if not ev["blocked"].is_empty():
		return {"shelved": false, "error": "not_words", "blocked": ev["blocked"]}
	var need := {}
	for k in marks:
		need[marks[k]] = need.get(marks[k], 0) + 1
	for t in need:
		if need[t] > tools.get(t, 0):
			return {"shelved": false, "error": "no_" + t}
	for t in need:
		tools[t] -= need[t]
	copies[doc.id] = ev["copy"]
	var g := Copyist.gloss(ev)
	if g != "":
		notes[doc.id] = g
	titles[doc.id] = doc.title
	scores[doc.id] = {"fidelity": ev["fidelity"], "clarity": ev["clarity"]}
	titles[doc.id] = doc.title
	var line := doc.delivered
	var told := false
	for o in doc.outcomes:
		if not Manuscript.holds(o.get("when", {}), flags, ev, marks):
			continue
		var sets = o.get("set", [])
		for f in (sets if sets is Array else [sets]):
			flags[String(f)] = true
		if o.has("chronicle") and not told:
			line = o["chronicle"]
			told = true
	if line != "":
		chronicle.append({"doc": doc.id, "line": line})
	phase = "answer"
	return {"shelved": true, "error": "", "copy": ev["copy"], "line": line}


## The chronicle line written when `doc_id` was delivered ("" if none).
func chronicle_of(doc_id: String) -> String:
	for c in chronicle:
		if c["doc"] == doc_id:
			return c["line"]
	return ""


func make_copy(doc: Manuscript, engine: RuleEngine, order: Array, reorder: Array = []) -> Dictionary:
	if phase != "read":
		return {"copy": "", "rejected": [], "shelved": false, "error": "already_copied"}
	for rid in order:
		if rid not in cards:
			return {"copy": "", "rejected": [], "shelved": false, "error": "missing_card"}
	if order.size() != _unique(order).size():
		return {"copy": "", "rejected": [], "shelved": false, "error": "duplicate_card"}
	var copy := engine.apply_text(doc.old_text, order, proven)
	if not reorder.is_empty():
		if not doc.allow_reorder:
			return {"copy": "", "rejected": [], "shelved": false, "error": "reorder_not_allowed"}
		var ws: PackedStringArray = copy.trim_suffix(".").split(" ", false)
		var sorted_r := reorder.duplicate()
		sorted_r.sort()
		if sorted_r != range(1, ws.size() + 1):
			return {"copy": "", "rejected": [], "shelved": false, "error": "bad_reorder"}
		var out: PackedStringArray = []
		for i in reorder:
			out.append(ws[int(i) - 1])
		copy = " ".join(out) + "."
	var rejected: PackedStringArray = []
	for tok in copy.split(" ", false):
		var w := tok.trim_suffix(".")
		if not engine.is_real(w, doc.era):
			rejected.append(w.to_lower())
	var shelved := rejected.is_empty()
	if shelved:
		copies[doc.id] = copy
		phase = "answer"
	return {"copy": copy, "rejected": rejected, "shelved": shelved, "error": ""}


func add_note(doc: Manuscript, text: String) -> bool:
	if text.strip_edges() == "" or not copies.has(doc.id):
		return false
	notes[doc.id] = text.strip_edges()
	titles[doc.id] = doc.title
	return true


func answer(doc: Manuscript, option_index: int) -> bool:
	if phase != "answer" or option_index < 0 or option_index >= doc.options.size():
		return false
	answers[doc.id] = doc.options[option_index]
	doc_index += 1
	phase = "read"
	return true


static func _unique(a: Array) -> Array:
	var seen := {}
	for x in a:
		seen[x] = true
	return seen.keys()


# --- Saving ----------------------------------------------------------------

func to_dict() -> Dictionary:
	return {"doc_index": doc_index, "phase": phase, "cards": cards, "proven": proven,
		"copies": copies, "answers": answers, "notes": notes, "titles": titles,
		"flags": flags, "chronicle": chronicle, "scores": scores}


static func from_dict(d: Dictionary) -> GameState:
	var g := GameState.new()
	g.doc_index = int(d.get("doc_index", 0))
	g.phase = d.get("phase", "read")
	for c in d.get("cards", []):
		g.cards.append(String(c))
	for k in d.get("proven", {}):
		g.proven[k] = d["proven"][k].map(func(x): return int(x))
	g.copies = d.get("copies", {})
	g.answers = d.get("answers", {})
	g.notes = d.get("notes", {})
	g.titles = d.get("titles", {})
	g.flags = d.get("flags", {})
	g.chronicle = d.get("chronicle", [])
	for k in d.get("scores", {}):
		var sc: Dictionary = d["scores"][k]
		g.scores[k] = {"fidelity": int(sc["fidelity"]), "clarity": int(sc["clarity"])}
	return g


func save(path: String = SAVE_PATH) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(to_dict()))


static func load_or_new(path: String = SAVE_PATH) -> GameState:
	if not FileAccess.file_exists(path):
		return GameState.new()
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
	return from_dict(data) if data is Dictionary else GameState.new()
