extends Control
## The scribe's desk, drawn as a classical Ottoman miniature seen from above
## (assets/art/STYLE.md). One document at a time:
##
## 1. Pair words: click an old word (in the document, or in the old dictionary
##    from the second era on), then a new one (the dictionary of today in the
##    first era, or a word heard from the requester). A good pair goes into
##    the notebook with its changed letters in red.
## 2. Two pairs that show the same change prove it: that line is inked onto
##    its rule tile, and a new tile appears on the desk if it is the first.
## 3. Put tiles in the tray; the copy sheet shows in pencil what that order
##    would write. Click the reed pen to write it in ink. Words that are not
##    words of this era are scraped; change the order and write again.
## 4. A copy of real words is shelved. The slip turns into the requester's
##    question; seal an answer and the next document arrives.

signal copy_changed(text: String)
signal copy_written(result: Dictionary)
signal pair_made(result: Dictionary)

const SPRITES := "res://assets/art/sprites/"
const FONT := preload("res://assets/fonts/Katip-Regular.ttf")
const INK := Color("2a1b14")
const RED := Color("b33a29")
const PAPER := Color("ecdcb9")
const PENCIL := Color(0.33, 0.29, 0.27, 0.85)
const WET := "#2a3f86"
const SCRAPED := "#9c8466"
const RED_HEX := "#b33a29"
const WORD_STEP := 0.32
const COPY_WIDTH := 330.0
const DESK := Rect2(70, 64, 1780, 952)
const PER_PAGE := 12

@export var doc_order := 1
@export var dev_cards := false          # hand over every rule up to the era, for tests

var engine: RuleEngine
var lib: ManuscriptLibrary
var state: GameState
var doc: Manuscript
var narrative: Narrative
var tray: RuleTray
var tiles_layer: Control
var tiles := {}
var pairs: Array[Dictionary] = []
var _rest := {}
var _copy_lines: Array[Label] = []
var _ink_lines: Array[RichTextLabel] = []
var _grain: TextureRect
var _seal: TextureRect
var _slip: Control
var _book: Control
var _book_left: Control
var _pairs_box: Control
var _reading: Control
var _reading_words := 0
var _pick := {}              # {"word", "role", "label"} waiting for its partner
var _bad := ""               # the last pair that did not hold, shown struck
var _page := 0
var _advance := false


func _ready() -> void:
	engine = RuleEngine.new()
	lib = ManuscriptLibrary.new()
	narrative = Narrative.new()
	state = GameState.new()
	state.doc_index = doc_order - 1
	_start_doc(false)


# --- what tests and other scenes call -----------------------------------------

func copy_text() -> String:
	return engine.apply_text(doc.old_text, tray.model.order(), state.proven)


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


## Put an old and a new word side by side. Returns Pairing.make's result.
func try_pair(old: String, nw: String) -> Dictionary:
	var res := Pairing.make(doc, lib, engine, state, old, nw)
	if res["ok"]:
		var dup := false
		for p in pairs:
			dup = dup or (p["old"] == res["old"] and p["new"] == res["new"])
		if not dup:
			pairs.append(res)
		_bad = ""
		_prove_what_pairs_show()
	else:
		_bad = "%s → %s" % [res["old"], res["new"]]
	_draw_pairs()
	pair_made.emit(res)
	return res


## The pen: the desk writes the copy from the tray order.
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
		_show_question()
	copy_written.emit(res)
	return res


## Seal one of the requester's answers. The next document follows.
func answer_question(i: int) -> bool:
	if not state.answer(doc, i):
		return false
	_advance = true
	var stamp := _tex(_slip, "muhur.png", Vector2(300, 74 + i * 32), -10.0)
	stamp.scale = Vector2(0.42, 0.42)
	var tw := create_tween()
	tw.tween_interval(1.4)
	tw.tween_callback(next_document)
	return true


func next_document() -> void:
	if not _advance:
		return
	_advance = false
	if state.doc_index >= lib.docs.size():
		_show_ending()
		return
	_start_doc(true)


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
	_title(page, Vector2(610, 47), 30)
	_reading_words = _write_words(page, 1520 - 52 - 200, 120, Vector2(90, 120), 580.0)
	var tw := create_tween()
	tw.tween_method(func(t: float) -> void:
		page.scale = Vector2.ONE * lerpf(0.45, 1.0, floorf(t * 3.0) / 3.0), 0.0, 1.0, 0.15)


func close_reading() -> void:
	if _reading:
		_reading.queue_free()
		_reading = null
		_reading_words = 0


func reading_word_count() -> int:
	return _reading_words


# --- a document on the desk ---------------------------------------------------

func _start_doc(arrive: bool) -> void:
	doc = lib.get_doc(state.doc_index)
	state.begin_doc(doc, engine)
	if dev_cards:
		for era in range(1, doc.era + 1):
			for rid in engine.era_ids(era):
				if rid not in state.cards:
					state.cards.append(rid)
					state.proven[rid] = range(engine.by_id[rid].sub_count())
	pairs.clear()
	_pick = {}
	_bad = ""
	_page = 0
	_reading = null
	for c in get_children():
		remove_child(c)
		c.queue_free()
	tiles.clear()
	_rest.clear()
	_copy_lines.clear()
	_ink_lines.clear()
	_build()
	_refresh()
	if arrive:
		for n in [_node("Belge"), _node("Kopya"), _slip]:
			var to: Vector2 = n.position
			n.position = to - Vector2(0, 900)
			var tw := create_tween()
			tw.tween_method(func(t: float) -> void:
				n.position = (to - Vector2(0, 900)).lerp(to, floorf(t * 6.0) / 6.0), 0.0, 1.0, 0.42)


func _node(node_name: String) -> Control:
	return get_node_or_null(node_name) as Control


func _build() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_tex(self, "masa_cag2.png", Vector2.ZERO, 0.0)

	var page := _sheet("Belge", "belge_kagit.png", Vector2(610, 150), Vector2(680, 440), -1.2)
	_clickable(page, open_reading, Vector2(664, -12))
	_title(page, Vector2(190, 47), 28)
	_write_words(page, 680 - 52 - 110, 64, Vector2(60, 108), 300.0)

	var sheet := _sheet("Kopya", "kopya_kagit.png", Vector2(1330, 250), Vector2(420, 500), 3.0)
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

	_book = _sheet("Defter", "defter.png", Vector2(64, 330), Vector2(520, 420), 1.5, 20.0)
	_label(_book, "Sözlük" if doc.era == 1 else "Eski sözlük", 24, RED).position = Vector2(22, 10)
	_book_left = Control.new()
	_book_left.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_book.add_child(_book_left)
	_draw_dictionary()
	_label(_book, "Duyduklarım", 24, RED).position = Vector2(282, 10)
	for i in doc.heard.size():
		var h := _label(_book, doc.heard[i], 20, INK)
		h.position = Vector2(286, 44 + i * 27)
		_pickable(h, doc.heard[i], "new")
	var py := 44 + maxi(doc.heard.size(), 1) * 27 + 14
	_label(_book, "Eşleşmeler", 24, RED).position = Vector2(282, py)
	_pairs_box = Control.new()
	_pairs_box.position = Vector2(286, py + 34)
	_pairs_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_book.add_child(_pairs_box)
	_draw_pairs()

	_slip = _sheet("Pusula", "pusula.png", Vector2(1530, 790), Vector2(360, 250), -6.0)
	var says := _rich(_slip, doc.says_bbcode().replace("[i]", "[color=%s]" % RED_HEX).replace("[/i]", "[/color]"), 17)
	says.position = Vector2(18, 14)
	says.size = Vector2(324, 186)

	tray = RuleTray.new()
	tray.position = Vector2(600, 790)
	add_child(tray)

	tiles_layer = Control.new()
	tiles_layer.name = "Karolar"
	tiles_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	tiles_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(tiles_layer)
	for rid in state.cards:
		_add_tile(rid, false)

	_grain = TextureRect.new()
	_grain.name = "SayfaDokusu"
	_grain.texture = load(SPRITES + "sayfa_doku.png")
	_grain.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_MUL
	_grain.material = mat
	add_child(_grain)


# --- words, the dictionary and pairs ----------------------------------------

## The document's words as separate, clickable words. Returns how many.
func _write_words(parent: Control, width: float, start: int, origin: Vector2, height: float) -> int:
	var lines := _sentences(doc.old_text)
	var fs := _fit(lines, width, start)
	var space := FONT.get_string_size(" ", HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var top := origin.y + maxf(0.0, (height - lines.size() * fs * 1.55) / 2.0)
	var count := 0
	for li in lines.size():
		var x := origin.x
		for w in lines[li].split(" ", false):
			var l := _label(parent, w, fs, INK)
			l.position = Vector2(x, top + li * fs * 1.55)
			_pickable(l, w, "old")
			x += FONT.get_string_size(w, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + space
			count += 1
	return count


## Today's dictionary in the first era; from the second on, the old one.
func dictionary() -> Array:
	var ids := engine.era_ids(doc.era if doc.era == 1 else doc.era - 1)
	var out := []
	for w in engine.words:
		out.append([engine.apply_word(w["root"], ids), w["meaning_tr"]])
	out.sort_custom(func(a: Array, b: Array) -> bool: return a[0].to_lower() < b[0].to_lower())
	return out


func _draw_dictionary() -> void:
	for c in _book_left.get_children():
		c.queue_free()
	var entries := dictionary()
	var pages := ceili(entries.size() / float(PER_PAGE))
	var role := "new" if doc.era == 1 else "old"
	for k in PER_PAGE:
		var i := _page * PER_PAGE + k
		if i >= entries.size():
			break
		var l := _label(_book_left, "%s — %s" % entries[i], 18, INK)
		l.position = Vector2(24, 44 + k * 27)
		l.size = Vector2(232, 26)
		l.clip_text = true
		_pickable(l, entries[i][0], role)
	var prev := _label(_book_left, "‹", 28, RED)
	prev.position = Vector2(30, 372)
	_clickable(prev, func() -> void: _turn(-1), Vector2(18, -6))
	_label(_book_left, "%d / %d" % [_page + 1, pages], 18, INK).position = Vector2(112, 380)
	var nxt := _label(_book_left, "›", 28, RED)
	nxt.position = Vector2(220, 372)
	_clickable(nxt, func() -> void: _turn(1), Vector2(18, -6))


func _turn(step: int) -> void:
	var pages := ceili(dictionary().size() / float(PER_PAGE))
	_page = posmod(_page + step, pages)
	_draw_dictionary()


func _pickable(l: Label, word: String, role: String) -> void:
	l.mouse_filter = Control.MOUSE_FILTER_STOP
	l.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	l.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			_on_pick(word, role, l)
			l.accept_event())


func _on_pick(word: String, role: String, l: Label) -> void:
	if _pick.is_empty():
		_pick = {"word": word, "role": role, "label": l}
		l.add_theme_color_override("font_color", RED)
		return
	var first: Label = _pick["label"]
	if is_instance_valid(first):
		first.add_theme_color_override("font_color", INK)
	if first == l:
		_pick = {}
		return
	if _pick["role"] == role:
		_pick = {"word": word, "role": role, "label": l}
		l.add_theme_color_override("font_color", RED)
		return
	var old: String = _pick["word"] if _pick["role"] == "old" else word
	var nw: String = word if _pick["role"] == "old" else _pick["word"]
	_pick = {}
	try_pair(old, nw)


func _draw_pairs() -> void:
	for c in _pairs_box.get_children():
		c.queue_free()
	if pairs.is_empty() and _bad == "":
		var hint := _label(_pairs_box, "Belgeden bir kelime seç, sonra %s karşılığını." % ("sözlükte" if doc.era == 1 else "duyduklarında"), 16, PENCIL)
		hint.size = Vector2(214, 80)
		hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		return
	var shown := pairs.slice(maxi(0, pairs.size() - 7))
	var y := 0.0
	for p in shown:
		var r := _rich(_pairs_box, _marked(p["old"], p["new"]), 18)
		r.position = Vector2(0, y)
		r.size = Vector2(220, 26)
		y += 26
	if _bad != "":
		var b := _rich(_pairs_box, "[color=%s][s]%s[/s][/color]" % [SCRAPED, _bad], 18)
		b.position = Vector2(0, y)
		b.size = Vector2(220, 26)


## "ghewom → khewom" with the changed letters in red.
func _marked(old: String, nw: String) -> String:
	var marks := Pairing.diff_marks(old, nw)
	return "%s → %s" % [_red_letters(old, marks[0]), _red_letters(nw, marks[1])]


func _red_letters(w: String, m: PackedInt32Array) -> String:
	var out := ""
	for i in w.length():
		out += ("[color=%s]%s[/color]" % [RED_HEX, w[i]]) if m[i] == 1 else w[i]
	return out


## Every substitution shown by two pairs with different old words is proven.
func _prove_what_pairs_show() -> void:
	var seen := {}
	for p in pairs:
		for s in p["subs"]:
			var key := "%s:%d" % [s[0], s[1]]
			if not seen.has(key):
				seen[key] = {}
			seen[key][p["old"]] = "%s:%s" % [p["old"], p["new"]]
	for key in seen:
		var ev: Dictionary = seen[key]
		if ev.size() < 2:
			continue
		var rid: String = key.get_slice(":", 0)
		var i := int(key.get_slice(":", 1))
		if state.proven.has(rid) and i in state.proven[rid]:
			continue
		var r: SoundRule = engine.by_id[rid]
		var res := state.prove_rule(doc, lib, engine, r.patterns[i], r.replacements[i], ev.values().slice(0, 2))
		if res["ok"]:
			if tiles.has(rid):
				tiles[rid].set_proven(RuleText.proven_lines(r, state.proven[rid]))
			else:
				_add_tile(rid, true)


func _add_tile(rid: String, arriving: bool) -> void:
	var i := tiles.size()
	var t := RuleTile.new()
	tiles_layer.add_child(t)
	t.setup(engine.by_id[rid], state.proven.get(rid, []), FONT)
	var spot := Vector2(80 + (i % 4) * 112 + (i / 4) * 56, 786 + (i % 2) * 14 + (i / 4) * 40)
	var rot: float = [-4.0, 3.0, -2.0, 5.0][i % 4]
	_rest[rid] = [spot, rot]
	t.dropped.connect(_on_tile_dropped)
	tiles[rid] = t
	if arriving:
		t.position = Vector2(300, 540)
		t.slide_to(spot, rot, 0.3)
	else:
		t.position = spot
		t.rotation_degrees = rot


# --- copying, the question, the end -------------------------------------------

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


## Write the copy word by word in wet ink; real words dry, others are scraped.
func _ink(res: Dictionary) -> void:
	for l in _copy_lines:
		l.text = ""
	var rejected: PackedStringArray = res["rejected"]
	var lines := _sentences(res["copy"])
	var cfs := _fit(lines, COPY_WIDTH, 38)
	var tw := create_tween()
	for li in _ink_lines.size():
		var ink := _ink_lines[li]
		ink.add_theme_font_size_override("normal_font_size", cfs)
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


## The slip turns over: the requester's question and the answers to seal.
func _show_question() -> void:
	for c in _slip.get_children():
		if c is RichTextLabel or c is Label:
			c.queue_free()
	var ask := _label(_slip, doc.ask, 19, RED)
	ask.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ask.position = Vector2(18, 14)
	ask.size = Vector2(324, 50)
	for i in doc.options.size():
		var o := _label(_slip, doc.options[i], 18, INK)
		o.position = Vector2(30, 70 + i * 32)
		var idx := i
		_clickable(o, func() -> void: answer_question(idx), Vector2(-24, 2))


func _show_ending() -> void:
	var page := _sheet("Son", "belge_okuma.png", Vector2(200, 160), Vector2(1520, 760), 0.0)
	move_child(page, _grain.get_index())
	var r := _rich(page, narrative.epilogue(state), 30)
	r.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	r.position = Vector2(120, 140)
	r.size = Vector2(1280, 560)


# --- helpers ---------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if _reading and event.is_action_pressed("ui_cancel"):
		close_reading()


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


func _title(page: Control, pos: Vector2, size_px: int) -> void:
	var title := _label(page, doc.title, size_px, PAPER)
	title.position = pos
	title.size = Vector2(300, 46)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER


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


func _rich(parent: Node, bbcode: String, font_size: int) -> RichTextLabel:
	var r := RichTextLabel.new()
	r.bbcode_enabled = true
	r.text = bbcode
	r.scroll_active = false
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.add_theme_font_override("normal_font", FONT)
	r.add_theme_font_size_override("normal_font_size", font_size)
	r.add_theme_color_override("default_color", INK)
	parent.add_child(r)
	return r


func _fit(lines: PackedStringArray, width: float, start: int) -> int:
	var fs := start
	for ln in lines:
		var w := FONT.get_string_size(ln, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		if w > width:
			fs = int(floor(fs * width / w))
	return fs


static func _sentences(text: String) -> PackedStringArray:
	var out := PackedStringArray()
	for part in text.split(". ", false):
		out.append(part if part.ends_with(".") else part + ".")
	return out
