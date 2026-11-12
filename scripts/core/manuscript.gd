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
	m.ask = d["question"]["ask_tr"]
	m.options = PackedStringArray(d["question"]["options_tr"])
	return m


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
