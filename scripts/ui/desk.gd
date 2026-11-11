extends Control
## The scribe's desk, drawn as a classical Ottoman miniature seen from above
## (see assets/art/STYLE.md). Rule tiles lie on the desk; dragged into the
## tray they apply left to right, and the copy sheet shows in pencil what the
## desk would write with that order.
##
## Click the document to read it large and mark words; click the reed pen to
## write the copy in ink. Real words dry glossy; words that do not exist in
## this era are scraped off, and the order can be changed and written again.
## Once every word is real the copy is shelved and the tiles are put away.
##
## Until proving rules is wired in, every rule up to the document's era is
## handed over fully proven.

signal copy_changed(text: String)
signal copy_written(result: Dictionary)

const SPRITES := "res://assets/art/sprites/"
const FONT := preload("res://assets/fonts/Katip-Regular.ttf")
const INK := Color("2a1b14")
const RED := Color("b33a29")
const PAPER := Color("ecdcb9")
const PENCIL := Color(0.33, 0.29, 0.27, 0.85)
const WET := "#2a3f86"                       # fresh ink shines blue-black, then dries
const SCRAPED := "#9c8466"
const WORD_STEP := 0.32                      # seconds between written words
const COPY_WIDTH := 330.0                    # writing width of the copy sheet
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
var _ink_lines: Array[RichTextLabel] = []
var _copy_sheet: Control
var _grain: TextureRect
var _seal: TextureRect
var _reading: Control
var _word_labels: Array[Label] = []
var _selected: Array[int] = []


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


## The pen: the desk writes the copy from the tray order. Returns make_copy's result.
func write_copy() -> Dictionary:
	if state.phase != "read":
		return {}
	var res := state.make_copy(doc, engine, tray.model.order())
	if res["error"] != "":
		return res
	_ink(res)
	if res["shelved"]:
		for t in tiles.values():
			t.locked = true
		_seal.visible = true
	copy_written.emit(res)
	return res


## The document, large, with every word ready to be marked.
func open_reading() -> void:
	if _reading:
		return
	_reading = Control.new()
	_reading.name = "Okuma"
	_reading.set_anchors_preset(Control.PRESET_FULL_RECT)
	_reading.mouse_filter = Control.MOUSE_FILTER_STOP
	_reading.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed:
			close_reading())
	add_child(_reading)
	move_child(_reading, _grain.get_index())
	var page := Control.new()
	page.position = Vector2(200, 160)
	page.size = Vector2(1520, 760)
	page.pivot_offset = page.size / 2
	page.mouse_filter = Control.MOUSE_FILTER_STOP
	_reading.add_child(page)
	_tex(page, "belge_okuma.png", Vector2(-8, -8), 0.0)
	var title := _label(page, doc.title, 30, PAPER)
	title.position = Vector2(610, 47)
	title.size = Vector2(300, 46)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var lines := _sentences(doc.old_text)
	var fs := _fit(lines, 1520 - 52 - 200, 120)
	var space := FONT.get_string_size(" ", HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var top := 120.0 + (580.0 - lines.size() * fs * 1.55) / 2.0
	_word_labels.clear()
	for li in lines.size():
		var x := 90.0
		for w in lines[li].split(" ", false):
			var idx := _word_labels.size()
			var l := _label(page, w, fs, RED if idx in _selected else INK)
			l.position = Vector2(x, top + li * fs * 1.55)
			l.mouse_filter = Control.MOUSE_FILTER_STOP
			l.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
			l.gui_input.connect(func(e: InputEvent) -> void:
				if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
					toggle_word(idx))
			var mark := _tex(l, "durak.png", Vector2(FONT.get_string_size(w, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x - 6, -6), 0.0)
			mark.visible = false
			l.mouse_entered.connect(func() -> void: mark.visible = true)
			l.mouse_exited.connect(func() -> void: mark.visible = false)
			_word_labels.append(l)
			x += FONT.get_string_size(w, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + space
	var tw := create_tween()
	tw.tween_method(func(t: float) -> void:
		page.scale = Vector2.ONE * lerpf(0.45, 1.0, floorf(t * 3.0) / 3.0), 0.0, 1.0, 0.15)


func close_reading() -> void:
	if _reading:
		_reading.queue_free()
		_reading = null
		_word_labels.clear()


## Mark or unmark a word of the document (red ink), for proving rules.
func toggle_word(i: int) -> void:
	if i in _selected:
		_selected.erase(i)
	else:
		_selected.append(i)
	if i < _word_labels.size():
		_word_labels[i].add_theme_color_override("font_color", RED if i in _selected else INK)


func selected_words() -> PackedStringArray:
	var ws := doc.old_words()
	var out := PackedStringArray()
	for i in _selected:
		out.append(ws[i])
	return out


func reading_word_count() -> int:
	return _word_labels.size()


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
	_clickable(page, open_reading, Vector2(664, -12))
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
	_copy_sheet = sheet
	for i in 4:
		var l := _label(sheet, "", 38, PENCIL)
		l.position = Vector2(44, 40 + i * 70)
		_copy_lines.append(l)
		var ink := RichTextLabel.new()
		ink.bbcode_enabled = true
		ink.fit_content = true
		ink.scroll_active = false
		ink.autowrap_mode = TextServer.AUTOWRAP_OFF
		ink.position = Vector2(44, 40 + i * 70)
		ink.size = Vector2(360, 60)
		ink.mouse_filter = Control.MOUSE_FILTER_IGNORE
		ink.add_theme_font_override("normal_font", FONT)
		ink.add_theme_font_size_override("normal_font_size", 38)
		ink.add_theme_color_override("default_color", INK)
		sheet.add_child(ink)
		_ink_lines.append(ink)
	_seal = _tex(sheet, "muhur.png", Vector2(300, 392), -12.0)
	_seal.visible = false

	var pen := Control.new()
	pen.name = "Kalem"
	pen.position = Vector2(1296, 772)
	pen.size = Vector2(230, 12)
	pen.rotation_degrees = -12.0
	add_child(pen)
	_tex(pen, "kalem.png", Vector2(-8, -8), 0.0)
	_clickable(pen, func() -> void: write_copy(), Vector2(222, -30))

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
	_grain = grain
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
	var drafting := state.phase == "read"
	var cfs := _fit(lines, COPY_WIDTH, 38)
	for i in _copy_lines.size():
		_copy_lines[i].text = lines[i] if i < lines.size() and drafting else ""
		_copy_lines[i].add_theme_font_size_override("font_size", cfs)
	if drafting:
		for ink in _ink_lines:
			ink.text = ""
	copy_changed.emit(copy)


## Write the copy word by word in wet ink. Real words dry to plain ink;
## words that are not words of this era are scraped and struck through.
func _ink(res: Dictionary) -> void:
	for l in _copy_lines:
		l.text = ""
	var rejected: PackedStringArray = res["rejected"]
	var lines := _sentences(res["copy"])
	var cfs := _fit(lines, COPY_WIDTH, 38)
	for ink in _ink_lines:
		ink.add_theme_font_size_override("normal_font_size", cfs)
	var tw := create_tween()
	for li in _ink_lines.size():
		var ink := _ink_lines[li]
		ink.text = ""
		if li >= lines.size():
			continue
		var wet := PackedStringArray()
		var dry := PackedStringArray()
		for w in lines[li].split(" ", false):
			var bad := w.trim_suffix(".").to_lower() in rejected
			wet.append(("[color=%s][s]%s[/s][/color]" % [SCRAPED, w]) if bad else ("[color=%s]%s[/color]" % [WET, w]))
			dry.append(("[color=%s][s]%s[/s][/color]" % [SCRAPED, w]) if bad else w)
		ink.text = " ".join(wet)
		ink.visible_characters = 0
		var count := 0
		for w in lines[li].split(" ", false):
			count += w.length() + 1
			var upto := count
			tw.tween_interval(WORD_STEP)
			tw.tween_callback(func() -> void: ink.visible_characters = upto)
		var dried := " ".join(dry)
		tw.tween_callback(func() -> void:
			var t2 := create_tween()
			t2.tween_interval(1.0)
			t2.tween_callback(func() -> void: ink.text = dried))


# --- helpers ---------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if _reading and event.is_action_pressed("ui_cancel"):
		close_reading()


## Make a thing on the desk clickable, with the red rose beside it on hover.
func _clickable(node: Control, action: Callable, mark_at: Vector2) -> void:
	node.mouse_filter = Control.MOUSE_FILTER_STOP
	node.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var mark := _tex(node, "durak.png", mark_at, 0.0)
	mark.visible = false
	node.mouse_entered.connect(func() -> void: mark.visible = true)
	node.mouse_exited.connect(func() -> void: mark.visible = false)
	node.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			action.call())

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
