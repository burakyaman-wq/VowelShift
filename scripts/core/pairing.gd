class_name Pairing
extends RefCounted
## Two words the player puts side by side: an old one (from the document or
## the old dictionary) and a new one (from the current dictionary or heard).
## If the new word is the old one after this era's changes, the pair is good
## evidence, and it shows which substitutions happened.

const ENDINGS := ["osyo", "esyo", "os", "om", "es", "em", "eti", "e"]


static func ending(w: String) -> String:
	for e in ENDINGS:
		if w.ends_with(e) and w.length() > e.length() + 1:
			return e
	return ""


## The new word inflected like the old one, when that form exists:
## ghewom with khewos gives khewom.
static func match_affix(old: String, nw: String) -> String:
	var eo := ending(old)
	var en := ending(nw)
	if eo == "" or en == "" or eo == en:
		return nw
	var cand := nw.substr(0, nw.length() - en.length()) + eo
	return cand if GameState.inflections(nw).has(cand) else nw


## Rules first seen in this document's era: the ones a pair can show.
static func era_rules(doc: Manuscript, engine: RuleEngine) -> Array:
	var out := []
	for rid in engine.era_ids(doc.era):
		if engine.by_id[rid].era == doc.era:
			out.append(rid)
	return out


## {ok, old, new, subs: Array of [rule id, sub index], problem}
## The desk knows which word is old and which is new from where it was picked.
static func make(doc: Manuscript, lib: ManuscriptLibrary, engine: RuleEngine, state: GameState, old: String, nw: String) -> Dictionary:
	old = old.to_lower().trim_suffix(".")
	nw = nw.to_lower().trim_suffix(".")
	if not state.visible_old(doc, engine).has(old):
		return {"ok": false, "old": old, "new": nw, "subs": [], "problem": "bu eski kelime masada görünmüyor"}
	nw = match_affix(old, nw)
	if not state.visible_new(doc, lib, engine).has(nw):
		return {"ok": false, "old": old, "new": nw, "subs": [], "problem": "bu yeni kelime henüz bilinmiyor"}
	var ids := era_rules(doc, engine)
	if engine.apply_word(old, ids) != nw:
		return {"ok": false, "old": old, "new": nw, "subs": [], "problem": "bu iki kelime birbirinin karşılığı değil"}
	var subs := []
	for rid in ids:
		var r: SoundRule = engine.by_id[rid]
		for i in r.sub_count():
			if r.apply(old, [i]) != old:
				subs.append([rid, i])
	return {"ok": true, "old": old, "new": nw, "subs": subs, "problem": ""}


## Letters that differ, for showing a pair: [marks_a, marks_b] (1 = changed).
static func diff_marks(a: String, b: String) -> Array:
	var n := a.length()
	var m := b.length()
	var dp := []
	for i in n + 1:
		var row := PackedInt32Array()
		row.resize(m + 1)
		dp.append(row)
	for i in range(n - 1, -1, -1):
		for j in range(m - 1, -1, -1):
			dp[i][j] = dp[i + 1][j + 1] + 1 if a[i] == b[j] else maxi(dp[i + 1][j], dp[i][j + 1])
	var ma := PackedInt32Array()
	ma.resize(n)
	ma.fill(1)
	var mb := PackedInt32Array()
	mb.resize(m)
	mb.fill(1)
	var i := 0
	var j := 0
	while i < n and j < m:
		if a[i] == b[j]:
			ma[i] = 0
			mb[j] = 0
			i += 1
			j += 1
		elif dp[i + 1][j] >= dp[i][j + 1]:
			i += 1
		else:
			j += 1
	return [ma, mb]
