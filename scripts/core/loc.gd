class_name Loc
extends RefCounted
## The game's two languages. Turkish is written in the code and data; English
## comes from `*_en` fields in the data and from the table below, keyed by the
## Turkish text. Set `Loc.lang` before the game's data is loaded.

static var lang := "tr"
const SETTINGS := "user://ayarlar.json"


## The interface text in the current language.
static func t(tr: String) -> String:
	if lang == "en":
		return UI.EN.get(tr, tr)
	return tr


## A data field in the current language: d[key_en] if present, else d[key_tr] (or d[key]).
static func pick(d: Dictionary, key: String) -> String:
	if lang == "en" and d.has(key + "_en"):
		return d[key + "_en"]
	return d.get(key + "_tr", d.get(key, ""))


static func set_lang(l: String) -> void:
	lang = l
	Copyist._meanings = {}
	save_choice()


static func load_choice() -> void:
	var f := FileAccess.open(SETTINGS, FileAccess.READ)
	if f:
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary and d.has("lang"):
			lang = d["lang"]
			return
	lang = "en" if OS.has_feature("web") else "tr"


static func save_choice() -> void:
	var f := FileAccess.open(SETTINGS, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify({"lang": lang}))
