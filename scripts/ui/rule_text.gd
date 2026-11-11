class_name RuleText
extends RefCounted
## How a rule's substitutions are written on a tile: "bh → ph", "-s → ∅",
## "kh → ş", "-o/-e → ∅". Look-around conditions are left out; the tile's
## name and pictogram carry them.


static func sub_text(rule: SoundRule, i: int) -> String:
	var pat := _strip_assertions(rule.patterns[i])
	var rep := rule.replacements[i]
	var word_final := pat.ends_with("$")
	pat = pat.trim_suffix("$")
	var dash := "-" if word_final else ""
	var left := dash + pat
	if pat.begins_with("[") and pat.ends_with("]"):
		var opts := PackedStringArray()
		for ch in pat.substr(1, pat.length() - 2):
			opts.append(dash + ch)
		left = "/".join(opts)
	return "%s → %s" % [left, rep if rep != "" else "∅"]


## The lines a tile shows: only the proven substitutions, in rule order.
static func proven_lines(rule: SoundRule, proven_idx: Array) -> PackedStringArray:
	var out := PackedStringArray()
	for i in rule.sub_count():
		if proven_idx.is_empty() or i in proven_idx:
			out.append(sub_text(rule, i))
	return out


static func _strip_assertions(p: String) -> String:
	var out := ""
	var i := 0
	while i < p.length():
		if p.substr(i, 2) == "(?":
			var depth := 0
			while i < p.length():
				if p[i] == "(":
					depth += 1
				elif p[i] == ")":
					depth -= 1
					if depth == 0:
						break
				i += 1
			i += 1
			continue
		out += p[i]
		i += 1
	return out
