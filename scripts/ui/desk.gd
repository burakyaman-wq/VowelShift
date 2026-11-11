extends Control
## The scribe's desk, drawn as a classical Ottoman miniature seen from above
## (see assets/art/STYLE.md). Rule tiles lie on the desk; dragged into the
## tray they apply left to right, and the copy sheet shows in pencil what the
## desk would write with that order.
##
## Until proving rules is wired in (task 18), every rule up to the document's
## era is handed over fully proven.

signal copy_changed(text: String)

const SPRITES := "res://assets/art/sprites/"
const FONT := preload("res://assets/fonts/Katip-Regular.ttf")
const INK := Color("2a1b14")
const RED := Color("b33a29")
const PAPER := Color("ecdcb9")
const PENCIL := Color(0.33, 0.29, 0.27, 0.85)
const DESK := Rect2(70, 64, 1780, 952)      # where a tile may be put down

@export var doc_order := 2

var engine: RuleEngine
var lib: ManuscriptLibrary
var state: GameState
var doc: Manuscript
var tray: RuleTray
var tiles_layer: Control
var tiles := {}            # rule id -> RuleTile
var _rest := {}            # rule id -> [position, rotation] on the desk
var _copy_lines: Array[Label] = []


func _ready() -> void:
	engine = RuleEngine.new()
	lib = ManuscriptLibrary.new()
	state = GameState.new()
	doc = lib.get_doc(doc_order - 1)
	state.doc_index = doc_order - 1
	state.begin_doc(doc, engine)
	_hand_over_cards()
	_build()
	_refresh()


# --- what tests and later tasks call ----------------------------------------

func place_rule(rule_id: String, slot: int) -> void:
	var out := tray.model.place(rule_id, slot)
	if out != "":
		_send_home(tiles[out])
	_arrange()
	_refresh()


func take_out(rule_id: String) -> void:
	tray.model.remove(rule_id)
	_send_home(tiles[rule_id])
	_refresh()


func copy_text() -> String:
	return engine.apply_text(doc.old_text, tray.model.order(), state.proven)


# --- building the desk -------------------------------------------------------

func _hand_over_cards() -> void:
	for era in range(1, doc.era + 1):
		for rid in engine.era_ids(era):
			if rid not in state.cards:
				state.cards.append(rid)
				state.proven[rid] = range(engine.by_id[rid].sub_count())


func _build() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_tex(self, "masa_cag2.png", Vector2.ZERO, 0.0)

	var page := _sheet("Belge", "belge_kagit.png", Vector2(610, 150), Vector2(680, 440), -1.2)
	var title := _label(page, doc.title, 28, PAPER)
	title.position = Vector2(190, 47)
	title.size = Vector2(300, 46)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var lines := _sentences(doc.old_text)
	var fs := _fit(lines, 680 - 52 - 110, 64)
	for i in lines.size():
		var l := _label(page, lines[i], fs, INK)
		l.position = Vector2(60, 108 + i * fs * 1.62)
		var mark := _tex(page, "durak.png", Vector2(60 + FONT.get_string_size(lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 6, l.position.y + fs * 0.55), 0.0)
		mark.scale = Vector2(0.8, 0.8)

	var sheet := _sheet("Kopya", "kopya_kagit.png", Vector2(1330, 250), Vector2(420, 500), 3.0)
	for i in 4:
		var l := _label(sheet, "", 38, PENCIL)
		l.position = Vector2(44, 40 + i * 70)
		_copy_lines.append(l)

	var book := _sheet("Defter", "defter.png", Vector2(84, 400), Vector2(470, 350), 2.0, 20.0)
	_label(book, "Kanıtlananlar", 24, RED).position = Vector2(22, 16)
	var y := 50.0
	for rid in state.cards:
		for t in RuleText.proven_lines(engine.by_id[rid], state.proven.get(rid, [])):
			_label(book, t, 19, INK).position = Vector2(26, y)
			y += 28
	_label(book, "Duyduklarım", 24, RED).position = Vector2(257, 16)
	for i in doc.heard.size():
		_label(book, doc.heard[i], 20, INK).position = Vector2(261, 50 + i * 30)

	var slip := _sheet("Pusula", "pusula.png", Vector2(1530, 790), Vector2(360, 250), -6.0)
	var says := RichTextLabel.new()
	says.bbcode_enabled = true
	says.text = doc.says_bbcode().replace("[i]", "[color=#b33a29]").replace("[/i]", "[/color]")
	says.position = Vector2(18, 14)
	says.size = Vector2(324, 186)
	says.scroll_active = false
	says.mouse_filter = Control.MOUSE_FILTER_IGNORE
	says.add_theme_font_override("normal_font", FONT)
	says.add_theme_font_size_override("normal_font_size", 17)
	says.add_theme_color_override("default_color", INK)
	slip.add_child(says)

	tray = RuleTray.new()
	tray.position = Vector2(600, 790)
	add_child(tray)

	tiles_layer = Control.new()
	tiles_layer.name = "Karolar"
	tiles_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	tiles_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(tiles_layer)
	for i in state.cards.size():
		var rid: String = state.cards[i]
		var t := RuleTile.new()
		tiles_layer.add_child(t)
		t.setup(engine.by_id[rid], state.proven.get(rid, []), FONT)
		t.position = Vector2(96 + i * 112, 800 + (i % 2) * 14)
		t.rotation_degrees = [-4.0, 3.0, -2.0, 5.0][i % 4]
		_rest[rid] = [t.position, t.rotation_degrees]
		t.dropped.connect(_on_tile_dropped)
		tiles[rid] = t

	var grain := TextureRect.new()
	grain.name = "SayfaDokusu"
	grain.texture = load(SPRITES + "sayfa_doku.png")
	grain.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_MUL
	grain.material = mat
	add_child(grain)


func _on_tile_dropped(tile: RuleTile) -> void:
	var slot := tray.slot_at(tile.center())
	if slot >= 0:
		place_rule(tile.rule_id, slot)
		return
	tray.model.remove(tile.rule_id)
	tile.position = tile.position.clamp(DESK.position, DESK.end - RuleTile.SIZE)
	_rest[tile.rule_id] = [tile.position, tile.rotation_degrees]
	_arrange()
	_refresh()


func _arrange() -> void:
	for i in tray.model.slots.size():
		var rid := tray.model.slots[i]
		if rid != "":
			tiles[rid].slide_to(tray.tile_spot(i) - tiles_layer.global_position, 0.0)


func _send_home(tile: RuleTile) -> void:
	var rest: Array = _rest[tile.rule_id]
	tile.slide_to(rest[0], rest[1])


func _refresh() -> void:
	var copy := copy_text()
	var lines := _sentences(copy)
	for i in _copy_lines.size():
		_copy_lines[i].text = lines[i] if i < lines.size() else ""
	copy_changed.emit(copy)


# --- helpers ---------------------------------------------------------------

func _sheet(node_name: String, file: String, pos: Vector2, sz: Vector2, rot: float, pad: float = 8.0) -> Control:
	var c := Control.new()
	c.name = node_name
	c.position = pos
	c.size = sz
	c.pivot_offset = sz / 2
	c.rotation_degrees = rot
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(c)
	_tex(c, file, Vector2(-pad, -pad), 0.0)
	return c


func _tex(parent: Node, file: String, pos: Vector2, rot: float) -> TextureRect:
	var t := TextureRect.new()
	t.texture = load(SPRITES + file)
	t.position = pos
	t.rotation_degrees = rot
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(t)
	return t


func _label(parent: Node, text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	parent.add_child(l)
	return l


## Largest size (up to `start`) at which every line fits `width`.
func _fit(lines: PackedStringArray, width: float, start: int) -> int:
	var fs := start
	for ln in lines:
		var w := FONT.get_string_size(ln, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		if w > width:
			fs = int(floor(fs * width / w))
	return fs


## One sentence per line, each keeping its full stop.
static func _sentences(text: String) -> PackedStringArray:
	var out := PackedStringArray()
	for part in text.split(". ", false):
		out.append(part if part.ends_with(".") else part + ".")
	return out
