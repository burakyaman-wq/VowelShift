class_name Manuscript
extends RefCounted
## One document that comes to the desk. Loaded from data/manuscripts/*.json
## (format: data/manuscripts/FORMAT.md).

var id: String
var order: int
var era: int
var title: String
var intro: String
var requester_name: String
var requester_says: String
var old_text: String
var heard: PackedStringArray = []
var inherit_cards: PackedStringArray = []
var allow_reorder := false
## Where word order carries the meaning: how the copy must begin (word prefixes).
var reading_key: PackedStringArray = []
var ask: String
var options: PackedStringArray = []
## "ana" (a story document, may open a page after delivery) or "kisa" (a short job).
var kind := "ana"
## The sound cards dealt for this job; empty = the era's cards plus the stranger.
var cards: PackedStringArray = []
## Scribe cards for this job; empty = the usual set (GameState.TOOLS_PER_DOC).
var tools: Dictionary = {}
## What delivering it does: [{when, set, chronicle}]; see FORMAT.md.
var outcomes: Array = []
## The line written when the copy is handed over (if no outcome says otherwise).
var delivered: String = ""
## Versions of this document that depend on earlier choices: [{when, old_text?, says_tr?, title_tr?, intro_tr?}].
var variants: Array = []
var _raw: Dictionary = {}


static func from_dict(d: Dictionary) -> Manuscript:
	var m := Manuscript.new()
	m.id = d["id"]
	m.order = int(d["order"])
	m.era = int(d["era"])
	m.title = d.get("title_tr", "")
	m.intro = d.get("intro_tr", "")
	m.requester_name = d["requester"]["name_tr"]
	m.requester_says = d["requester"]["says_tr"]
	m.old_text = d["old_text"]
	m.heard = PackedStringArray(d.get("heard", []))
	m.inherit_cards = PackedStringArray(d.get("inherit_cards", []))
	m.allow_reorder = bool(d.get("allow_reorder", false))
	m.reading_key = PackedStringArray(d.get("reading_key", []))
	var q: Dictionary = d.get("question", {})
	m.ask = q.get("ask_tr", "")
	m.options = PackedStringArray(q.get("options_tr", []))
	m.kind = d.get("kind", "ana")
	m.cards = PackedStringArray(d.get("cards", []))
	m.tools = d.get("tools", {})
	m.outcomes = d.get("outcomes", [])
	m.delivered = d.get("delivered_tr", "")
	m.variants = d.get("variants", [])
	m._raw = d
	return m


## This document as it comes to a desk where `flags` are set: the first
## matching variant's fields replace the plain ones.
func resolved(flags: Dictionary) -> Manuscript:
	for v in variants:
		if Manuscript.holds(v.get("when", {}), flags):
			var d := _raw.duplicate(true)
			for k in ["old_text", "title_tr", "intro_tr"]:
				if v.has(k):
					d[k] = v[k]
			if v.has("says_tr"):
				d["requester"]["says_tr"] = v["says_tr"]
			d.erase("variants")
			return Manuscript.from_dict(d)
	return self


## Every text this document can come with (the plain one and each variant).
func all_old_texts() -> PackedStringArray:
	var out: PackedStringArray = [old_text]
	for v in variants:
		if v.has("old_text"):
			out.append(v["old_text"])
	return out


## Does a condition hold? Keys (all must hold): flag, not_flag, copy_has,
## copy_lacks, mark [key, tool], order. An empty condition always holds.
static func holds(when: Dictionary, flags: Dictionary, ev: Dictionary = {}, marks: Dictionary = {}) -> bool:
	if when.has("flag") and not flags.has(when["flag"]):
		return false
	if when.has("not_flag") and flags.has(when["not_flag"]):
		return false
	var copy := String(ev.get("copy", "")).to_lower()
	if when.has("copy_has") and not copy.contains(String(when["copy_has"]).to_lower()):
		return false
	if when.has("copy_lacks") and copy.contains(String(when["copy_lacks"]).to_lower()):
		return false
	if when.has("mark") and marks.get(when["mark"][0], "") != when["mark"][1]:
		return false
	if when.has("order") and ev.get("order", "") != when["order"]:
		return false
	return true


## Words of the old text without punctuation, in order.
func old_words() -> PackedStringArray:
	var out: PackedStringArray = []
	for tok in old_text.split(" ", false):
		out.append(tok.trim_suffix(".").trim_suffix(","))
	return out


## Requester line with *italic* markers turned into RichTextLabel BBCode.
func says_bbcode() -> String:
	var rx := RegEx.new()
	rx.compile("\\*([^*]+)\\*")
	return rx.sub(requester_says, "[i]$1[/i]", true)
