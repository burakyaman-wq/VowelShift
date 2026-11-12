extends Control
## The scribe's desk, drawn as a classical Ottoman miniature seen from above
## (assets/art/STYLE.md). One document at a time, played like a card game:
##
## 1. Each era hands over its sound-rule cards. They lie in the hand on the
##    left; the cards of earlier eras stay there too.
## 2. Lay cards in the tray. They act from left to right on every word of the
##    document, and the copy sheet shows each word as it now comes out: its
##    changed letters in red, its meaning if it is a word of this era, scraped
##    if it is not. Order matters: one card can feed the next.
## 3. Click the reed pen to write the copy in ink. A copy of real words is
##    shelved; the slip turns into the requester's question; seal an answer
##    and the next document arrives. What you wrote is what later eras read.
##
## Where a document allows it, the copy's words lie on loose slips and can be
## put in another order before the pen writes. A shelved copy takes a note in
## its margin. Between documents a page tells what the years, or the street,
## made of the last copy. The master's note (Tutor) says what to do next.

signal copy_changed(text: String)
signal copy_written(result: Dictionary)

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
const SLIP_ORIGIN := Vector2(44, 40)
const SLIP_ROW := 54.0
const SLIP_GAP := 8.0
const SLIP_WIDTH := 348.0

@export var doc_order := 1
@export var dev_cards := false          # hand over every rule up to the era, for tests
@export var era_look := 0               # paint the desk as this era whatever the document's; 0 = the document's

var engine: RuleEngine
var lib: ManuscriptLibrary
var state: GameState
var doc: Manuscript
var narrative: Narrative
var tray: RuleTray
var tiles_layer: Control
var tiles := {}
var _rest := {}
var _copy_lines: Array[Label] = []
var _ink_lines: Array[RichTextLabel] = []
var _grain: TextureRect
var _seal: TextureRect
var _slip: Control
var _words_box: Control
var _reading: Control
var _reading_words := 0
var _new_cards: Array = []   # cards this document handed over, for the master's note
var _meanings := {}           # era -> {word form -> meaning}
var _advance := false
var _word_order: Array = []   # 1-based order of the copy's words once the player has moved any; empty = as written
var _slips: Control
var _note: LineEdit
var _interlude: Control
var tutor: Tutor
var _hints_done := {}         # one-time hints already followed, kept across documents


func _ready() -> void:
	engine = RuleEngine.new()
	lib = ManuscriptLibrary.new()
	narrative = Narrative.new()
	state = GameState.new()
	state.doc_index = doc_order - 1
	_start_doc(false)


# --- what tests and other scenes call -----------------------------------------

func copy_text() -> String:
	var text := engine.apply_text(doc.old_text, tray.model.order(), state.proven)
	if _word_order.is_empty():
		return text
	var ws := text.trim_suffix(".").split(" ", false)
	if ws.size() != _word_order.size():
		return text
	var out := PackedStringArray()
	for i in _word_order:
		out.append(ws[int(i) - 1])
	return " ".join(out) + "."


## Take the word at one place in the copy and put it at another (0-based).
## Only where the document lets its words be reordered, and before it is written.
func move_word(from_pos: int, to_pos: int) -> bool:
	var n := doc.old_words().size()
	if not doc.allow_reorder or state.phase != "read" or mini(from_pos, to_pos) < 0 or maxi(from_pos, to_pos) >= n:
		return false
	if _word_order.is_empty():
		_word_order = range(1, n + 1)
	var w: int = _word_order.pop_at(from_pos)
	_word_order.insert(to_pos, w)
	_refresh()
	return true


func place_rule(rule_id: String, slot: int) -> void:
	var before := word_results()
	var out := tray.model.place(rule_id, slot)
	if out != "":
		_send_home(tiles[out])
	_arrange()
	_refresh()
	_tell_change(before, rule_id)


func take_out(rule_id: String) -> void:
	tray.model.remove(rule_id)
	_send_home(tiles[rule_id])
	_refresh()


## Each distinct word of the document as the tray now writes it:
## [{old, new, real, meaning}], in the order they first appear.
func word_results() -> Array:
	var out := []
	var seen := {}
	for w in doc.old_words():
		var key := w.to_lower()
		if seen.has(key):
			continue
		seen[key] = true
		var nw := engine.apply_text(w, tray.model.order(), state.proven)
		out.append({"old": w, "new": nw, "real": engine.is_real(nw, doc.era), "meaning": meaning_of(nw, doc.era)})
	return out


## What a word means in an era ("" if it is no word then). A form two words
## have fallen into gives both meanings.
func meaning_of(word: String, at_era: int) -> String:
	if not _meanings.has(at_era):
		var ids := engine.era_ids(at_era)
		var m := {}
		for w in engine.words:
			for tag in w["forms"]:
				var f := engine.apply_word(w["forms"][tag], ids).to_lower()
				if not m.has(f):
					m[f] = []
				if w["meaning_tr"] not in m[f]:
					m[f].append(w["meaning_tr"])
		_meanings[at_era] = m
	var hit: Array = _meanings[at_era].get(word.to_lower().trim_suffix("."), [])
	return " / ".join(PackedStringArray(hit))


## The pen: the desk writes the copy from the tray order.
func write_copy() -> Dictionary:
	if state.phase != "read":
		return {}
	var moved := not _word_order.is_empty() and _word_order != range(1, _word_order.size() + 1)
	var res := state.make_copy(doc, engine, tray.model.order(), _word_order if moved else [])
	if res["error"] != "":
		return res
	_lay_slips("")
	_ink(res)
	if not res["shelved"]:
		tutor.tell("Üstü çizili kelimeler [color=%s]bu çağın dilinde yok[/color]. Eksik bir kural mı var, yoksa karoların sırası mı yanlış? Düzelt ve kalemi yeniden tıkla." % RED_HEX)
	else:
		tutor.tell("Kopya rafa kondu.")
	if res["shelved"]:
		for t in tiles.values():
			t.locked = true
		_seal.visible = true
		_show_question()
		_show_note_field()
	_guide()
	copy_written.emit(res)
	return res


## Seal one of the requester's answers. The next document follows.
func answer_question(i: int) -> bool:
	if i >= 0 and i < doc.options.size() and _note and _note.text.strip_edges() != "":
		state.add_note(doc, _note.text)         # a note still being written goes in with the answer
	if not state.answer(doc, i):
		return false
	_advance = true
	var stamp := _tex(_slip, "muhur.png", Vector2(300, 74 + i * 32), -10.0, false)
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


## A line in the margin of the shelved copy. Whoever opens the archive later
## will read it beside the text. Writing again replaces it.
func add_note(text: String) -> bool:
	if not state.add_note(doc, text):
		return false
	if _note:
		_note.add_theme_color_override("font_color", RED)
	return true


## What the scribe learns before this document: what the years did, or what
## the street made of the last copy. Empty when there is nothing to tell.
func interlude_text() -> String:
	var parts := PackedStringArray()
	if doc.intro != "":
		parts.append(doc.intro)
	if doc.order == 3 and state.copies.has("2"):
		parts.append(narrative.rumour_doc3(state))
	return "\n\n".join(parts)


func dismiss_interlude() -> void:
	if not _interlude:
		return
	_interlude.queue_free()
	_interlude = null
	_arrive()
	_guide()


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
	_tex(page, "belge_okuma.png", Vector2(-8, -8), 0.0, true, Art.document_era(era()))
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
	_new_cards = []
	for rid in Pairing.era_rules(doc, engine):          # each era hands over its cards
		if rid not in state.cards:
			state.cards.append(rid)
			state.proven[rid] = range(engine.by_id[rid].sub_count())
			_new_cards.append(rid)
	if dev_cards:
		for era in range(1, doc.era + 1):
			for rid in engine.era_ids(era):
				if rid not in state.cards:
					state.cards.append(rid)
					state.proven[rid] = range(engine.by_id[rid].sub_count())
	_reading = null
	_interlude = null
	_note = null
	_word_order = []
	for c in get_children():
		remove_child(c)
		c.queue_free()
	tiles.clear()
	_rest.clear()
	_copy_lines.clear()
	_ink_lines.clear()
	_build()
	_refresh()
	var told := interlude_text()
	if told != "":
		for n in [_node("Belge"), _node("Kopya"), _slip]:
			n.visible = false
		_show_interlude(told, "Aradan geçen zaman" if doc.intro != "" else "Kapıda duyduğun")
	elif arrive:
		_arrive()
	_guide()


## The document, the blank sheet and the requester's slip slide in from the top edge.
func _arrive() -> void:
	for n in [_node("Belge"), _node("Kopya"), _slip]:
		var to: Vector2 = n.position
		n.visible = true
		n.position = to - Vector2(0, 900)
		var tw := create_tween()
		tw.tween_method(func(t: float) -> void:
			n.position = (to - Vector2(0, 900)).lerp(to, floorf(t * 6.0) / 6.0), 0.0, 1.0, 0.42)


## A page laid over the desk between two documents; a click puts it away.
func _show_interlude(text: String, heading: String) -> void:
	_interlude = Control.new()
	_interlude.name = "Ara"
	_interlude.set_anchors_preset(Control.PRESET_FULL_RECT)
	_interlude.mouse_filter = Control.MOUSE_FILTER_STOP
	_interlude.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	_interlude.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed:
			dismiss_interlude())
	add_child(_interlude)
	move_child(_interlude, _grain.get_index())
	var page := Control.new()
	page.position = Vector2(200, 160)
	page.size = Vector2(1520, 760)
	page.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_interlude.add_child(page)
	_tex(page, "belge_okuma.png", Vector2(-8, -8), 0.0)
	_title(page, Vector2(610, 47), 30, heading)
	var r := _rich(page, _red_marks(text), 30)
	r.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	r.position = Vector2(150, 150)
	r.size = Vector2(1220, 500)
	var go := _label(page, "devam etmek için tıkla", 20, PENCIL)
	go.position = Vector2(1150, 668)


## *words* of today's language, as the data marks them, in red.
static func _red_marks(text: String) -> String:
	var rx := RegEx.new()
	rx.compile("\\*([^*]+)\\*")
	return rx.sub(text, "[color=%s]$1[/color]" % RED_HEX, true)


func _node(node_name: String) -> Control:
	return get_node_or_null(node_name) as Control


func _build() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_tex(self, "masa.png", Vector2.ZERO, 0.0, false)

	var page := _sheet("Belge", "belge_kagit.png", Vector2(610, 150), Vector2(680, 440), -1.2, 8.0, Art.document_era(era()))
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
	_words_box = Control.new()
	_words_box.name = "Kelimeler"
	_words_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sheet.add_child(_words_box)
	_slips = Control.new()
	_slips.name = "Fisler"
	_slips.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sheet.add_child(_slips)
	_seal = _tex(sheet, "muhur.png", Vector2(300, 392), -12.0, false)
	_seal.visible = false

	var pen := Control.new()
	pen.name = "Kalem"
	pen.position = Vector2(1290, 768)
	pen.size = Vector2(250, 18)
	pen.rotation_degrees = -12.0
	add_child(pen)
	_tex(pen, "kalem.png", Vector2(-8, -8), 0.0)
	_clickable(pen, func() -> void: write_copy(), Vector2(240, -30))

	var hand := _label(self, "Elindeki kartlar", 26, PAPER)
	hand.name = "El"
	hand.position = Vector2(92, 316)
	hand.size = Vector2(480, 470)
	hand.mouse_filter = Control.MOUSE_FILTER_IGNORE

	_slip = _sheet("Pusula", "pusula.png", Vector2(1530, 790), Vector2(360, 250), -6.0)
	var says := _rich(_slip, doc.says_bbcode().replace("[i]", "[color=%s]" % RED_HEX).replace("[/i]", "[/color]"), 17)
	says.position = Vector2(18, 14)
	says.size = Vector2(324, 186)

	tray = RuleTray.new()
	tray.era = era()
	tray.position = Vector2(600, 790)
	add_child(tray)

	tiles_layer = Control.new()
	tiles_layer.name = "Karolar"
	tiles_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	tiles_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(tiles_layer)
	for rid in state.cards:
		_add_tile(rid, false)

	tutor = Tutor.new()
	add_child(tutor)
	tutor.setup(FONT, era())

	_grain = TextureRect.new()
	_grain.name = "SayfaDokusu"
	_grain.texture = Art.tex("sayfa_doku.png")
	_grain.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_MUL
	_grain.material = mat
	add_child(_grain)


# --- words and cards ------------------------------------------------------------

## The document's words, laid out on its page. Returns how many.
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
			x += FONT.get_string_size(w, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + space
			count += 1
	return count


func _marked(old: String, nw: String) -> String:
	var marks := Pairing.diff_marks(old, nw)
	return "%s → %s" % [_red_letters(old, marks[0]), _red_letters(nw, marks[1])]


func _red_letters(w: String, m: PackedInt32Array) -> String:
	var out := ""
	for i in w.length():
		out += ("[color=%s]%s[/color]" % [RED_HEX, w[i]]) if m[i] == 1 else w[i]
	return out


## A rule card in the hand, at its resting place.
func _add_tile(rid: String, arriving: bool) -> void:
	var i := tiles.size()
	var t := RuleTile.new()
	tiles_layer.add_child(t)
	t.setup(engine.by_id[rid], state.proven.get(rid, []), FONT, era())
	var spot := Vector2(82 + (i % 3) * 166, 364 + (i / 3) * 212)
	var rot: float = [-3.0, 2.0, -1.5, 2.5, -2.0, 1.0][i % 6]
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
	var loose := drafting and doc.allow_reorder
	var cfs := _fit(lines, COPY_WIDTH, 38)
	for i in _copy_lines.size():
		_copy_lines[i].text = ""
		_copy_lines[i].add_theme_font_size_override("font_size", cfs)
	_lay_slips(copy if loose else "")
	_draw_word_cards(drafting)
	if tutor:
		_guide()
	if drafting:
		for ink in _ink_lines:
			ink.text = ""
	copy_changed.emit(copy)


## On the copy sheet, while it is still blank: every word as the tray now
## writes it. Changed letters red; a word of this era in ink with its meaning
## in pencil beneath; a word of no era struck through.
func _draw_word_cards(show: bool) -> void:
	for c in _words_box.get_children():
		_words_box.remove_child(c)
		c.queue_free()
	if not show:
		return
	var rows := word_results()
	var top := 236.0 if doc.allow_reorder else 30.0
	var step := minf(58.0, (488.0 - top) / maxf(rows.size(), 1))
	var big_px := 28 if step >= 54 else 22
	for k in rows.size():
		var r: Dictionary = rows[k]
		var shown := _red_letters(r["new"], Pairing.diff_marks(r["old"], r["new"])[1])
		if not r["real"]:
			shown = "[color=%s][s]%s[/s][/color]" % [SCRAPED, r["new"]]
		var big := _rich(_words_box, shown, big_px)
		big.position = Vector2(40, top + k * step)
		big.size = Vector2(170, step)
		var note: String = r["meaning"] if r["real"] else "bu çağda yok"
		var small := _label(_words_box, ("eski: %s" % r["old"]) if r["new"] != r["old"] else "değişmedi", 14, PENCIL)
		small.position = Vector2(42, top + k * step + big_px + 4)
		var mean := _label(_words_box, note, 17, INK if r["real"] else Color(SCRAPED))
		mean.position = Vector2(214, top + k * step + 6)
		mean.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		mean.custom_minimum_size = Vector2(168, 0)
		mean.size = Vector2(168, step - 6)
		if note.length() > 22:
			mean.add_theme_font_size_override("font_size", 14)


## The draft as loose slips, one word each, in the order they now stand.
func _lay_slips(copy: String) -> void:
	for c in _slips.get_children():
		_slips.remove_child(c)
		c.queue_free()
	if copy == "":
		return
	var ws := copy.trim_suffix(".").split(" ", false)
	var at := SLIP_ORIGIN
	for k in ws.size():
		var slip := WordSlip.new()
		_slips.add_child(slip)
		slip.setup(ws[k], int(_word_order[k]) if _word_order.size() == ws.size() else k + 1, FONT, 30, PENCIL, era())
		if at.x > SLIP_ORIGIN.x and at.x + slip.size.x > SLIP_ORIGIN.x + SLIP_WIDTH:
			at = Vector2(SLIP_ORIGIN.x, at.y + SLIP_ROW)
		slip.position = at
		slip.rotation_degrees = [-1.2, 0.8, -0.5, 1.1][k % 4]
		slip.dropped.connect(_on_slip_dropped)
		at.x += slip.size.x + SLIP_GAP
	_label(_slips, ".", 30, PENCIL).position = at + Vector2(-4, 0)
	var hint := _label(_slips, "Fişleri sürükle; yazı o sırayla yazılır.", 16, PENCIL)
	hint.position = Vector2(SLIP_ORIGIN.x, at.y + SLIP_ROW + 4)


## A slip let go: the words now read in the order the slips lie, row by row.
func _on_slip_dropped(_slip: WordSlip) -> void:
	var slips: Array = []
	for c in _slips.get_children():
		if c is WordSlip:
			slips.append(c)
	slips.sort_custom(func(a: WordSlip, b: WordSlip) -> bool:
		var ra := roundi((a.center().y - SLIP_ORIGIN.y - WordSlip.HEIGHT / 2) / SLIP_ROW)
		var rb := roundi((b.center().y - SLIP_ORIGIN.y - WordSlip.HEIGHT / 2) / SLIP_ROW)
		return ra < rb if ra != rb else a.center().x < b.center().x)
	_word_order = slips.map(func(s: WordSlip) -> int: return s.index)
	_refresh()


## Once the copy is shelved its margin takes a line: pencil while it is being
## written, red ink once it is entered.
func _show_note_field() -> void:
	var sheet := _node("Kopya")
	var rule := ColorRect.new()
	rule.color = Color(PENCIL, 0.35)
	rule.position = Vector2(36, 484)
	rule.size = Vector2(246, 1.5)
	rule.rotation_degrees = -2.0
	rule.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sheet.add_child(rule)
	_note = LineEdit.new()
	_note.name = "KenarNotu"
	_note.placeholder_text = "kenara not düş"
	_note.max_length = 40
	_note.position = Vector2(34, 446)
	_note.size = Vector2(250, 40)
	_note.rotation_degrees = -2.0
	_note.context_menu_enabled = false
	for box in ["normal", "focus", "read_only"]:
		_note.add_theme_stylebox_override(box, StyleBoxEmpty.new())
	_note.add_theme_font_override("font", FONT)
	_note.add_theme_font_size_override("font_size", 22)
	_note.add_theme_color_override("font_color", PENCIL)
	_note.add_theme_color_override("font_placeholder_color", Color(PENCIL, 0.6))
	_note.add_theme_color_override("caret_color", INK)
	_note.text_changed.connect(_on_note_typed)
	_note.text_submitted.connect(func(t: String) -> void:
		add_note(t)
		_note.release_focus())
	_note.focus_exited.connect(func() -> void:
		if _note:
			add_note(_note.text))
	sheet.add_child(_note)


## Only what the reed can write: letters the hand has no shape for are dropped.
func _on_note_typed(typed: String) -> void:
	var clean := ""
	for ch in typed:
		if FONT.has_char(ch.unicode_at(0)):
			clean += ch
	if clean != typed:
		var caret := _note.caret_column
		_note.text = clean
		_note.caret_column = mini(caret, clean.length())
	_note.add_theme_color_override("font_color", PENCIL)


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
	var page := _sheet("Son", "belge_okuma.png", Vector2(200, 160), Vector2(1520, 760), 0.0, 8.0, Art.document_era(era()))
	move_child(page, _grain.get_index())
	_title(page, Vector2(610, 47), 30, "Yüz yıl sonra")
	var r := _rich(page, narrative.epilogue(state), 30)
	r.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	r.position = Vector2(120, 140)
	r.size = Vector2(1280, 560)


# --- the master's note ---------------------------------------------------------

## The one thing to do next, and the stop mark beside where to do it.
## The first document walks through every step; later ones only add what is new.
func _guide() -> void:
	if not tutor or not is_instance_valid(tutor):
		return
	var step := _next_step()
	tutor.show_step(step[0], step[1])


func _next_step() -> Array:
	var none := Rect2()
	if _interlude:
		return ["", none]
	if state.phase == "answer":
		return ["Kopya rafta. İstersen kâğıdın altına bir [color=%s]kenar notu[/color] yaz. Sonra pusuladaki soruyu kopyaladığın metne göre cevapla: bir cevaba tıkla." % RED_HEX, _rect("Pusula")]
	var rows := word_results()
	var wrong := rows.filter(func(r: Dictionary) -> bool: return not r["real"]).size()
	var order := tray.model.order()
	if order.is_empty():
		if doc.era == 1:
			return ["Belge eski dilde yazılmış; onu bugünün diliyle kopyalayacaksın. Sol tarafta [color=%s]ses kuralı kartların[/color] var. Bir kartı tutup aşağıdaki [color=%s]tepsiye sürükle[/color]." % [RED_HEX, RED_HEX], _hand_rect()]
		if not _new_cards.is_empty():
			return ["Yeni çağ, yeni kartlar: [color=%s]%s[/color]. Eski çağların kartları da elinde ama onlar işini çoktan yaptı. Yeni kartları tepsiye diz." % [RED_HEX, ", ".join(_new_cards.map(func(r: String) -> String: return engine.by_id[r].name_tr))], _hand_rect()]
		return ["Bu belgenin kartlarını tepsiye diz.", _hand_rect()]
	if wrong > 0:
		if doc.era == 1 and order.size() == 1:
			return ["Kart, belgedeki bütün kelimelere uygulandı: kopya kâğıdında değişen harfler [color=%s]kırmızı[/color]. Üstü çizili kelimeler bu çağda yok; [color=%s]öbür kartı da tepsiye koy[/color]." % [RED_HEX, RED_HEX], _hand_rect()]
		if order.size() >= 2:
			return ["Hâlâ %d kelime bu çağda yok. Kartlar tepsiye [color=%s]soldan sağa[/color] uygulanır ve sıra önemlidir: bir kart öbürünün yaptığını bir basamak daha kaydırabilir. Sırayı değiştir ya da eksik kartı ekle." % [wrong, RED_HEX], tray.get_global_rect()]
		return ["Hâlâ %d kelime bu çağda yok. Elindeki öbür kartları dene." % wrong, _hand_rect()]
	if doc.allow_reorder:
		return ["Bütün kelimeler bu çağın dilinde. Ama ekler düştü; kimin kimi öldürdüğünü artık [color=%s]kelimelerin sırası[/color] söylüyor: önce gelen yapandır. Fişleri sürükleyip anlamı koruyan sırayı kur, sonra kalemi tıkla." % RED_HEX, _rect("Kopya")]
	if doc.era == 1:
		return ["Bütün kelimeler bu çağın dilinde; anlamları altlarında. [color=%s]Kalemi tıkla[/color], mürekkeple yaz." % RED_HEX, _rect("Kalem")]
	return ["Bütün kelimeler bu çağın dilinde. Anlamlarına bak: istediğin bu mu? Öyleyse [color=%s]kalemi tıkla[/color]. Yazdığın, sonraki çağların okuyacağı metin olur." % RED_HEX, _rect("Kalem")]


func _hand_rect() -> Rect2:
	for rid in state.cards:
		if tiles.has(rid) and not tray.model.order().has(rid):
			return tiles[rid].get_global_rect()
	return _rect("El")


## Say what laying a card did to the words.
func _tell_change(before: Array, rule_id: String) -> void:
	if not tutor:
		return
	var after := word_results()
	var changed := 0
	for i in after.size():
		if after[i]["new"] != before[i]["new"]:
			changed += 1
	var r: SoundRule = engine.by_id[rule_id]
	if changed == 0:
		tutor.tell("«%s» bu sırada hiçbir kelimeyi değiştirmedi." % r.name_tr)
	else:
		tutor.tell("«%s» %d kelimeyi değiştirdi." % [r.name_tr, changed])


func _rect(node_name: String) -> Rect2:
	var n := _node(node_name)
	return n.get_global_rect() if n else Rect2()


func _all_real(text: String) -> bool:
	for tok in text.split(" ", false):
		if not engine.is_real(tok.trim_suffix("."), doc.era):
			return false
	return true


# --- helpers ---------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if _interlude and (event.is_action_pressed("ui_cancel") or event.is_action_pressed("ui_accept")):
		dismiss_interlude()
	elif _reading and event.is_action_pressed("ui_cancel"):
		close_reading()


func _clickable(node: Control, action: Callable, mark_at: Vector2) -> void:
	node.mouse_filter = Control.MOUSE_FILTER_STOP
	node.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var mark := _tex(node, "durak.png", mark_at, 0.0, false)
	mark.visible = false
	node.mouse_entered.connect(func() -> void: mark.visible = true)
	node.mouse_exited.connect(func() -> void: mark.visible = false)
	node.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			action.call())


func _title(page: Control, pos: Vector2, size_px: int, text: String = "") -> void:
	var title := _label(page, text if text != "" else doc.title, size_px, PAPER)
	title.position = pos
	title.size = Vector2(300, 46)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER


## The era the desk is painted in.
func era() -> int:
	return era_look if era_look > 0 else doc.era


func _sheet(node_name: String, file: String, pos: Vector2, sz: Vector2, rot: float, pad: float = 8.0, look: int = 0) -> Control:
	var c := Control.new()
	c.name = node_name
	c.position = pos
	c.size = sz
	c.pivot_offset = sz / 2
	c.rotation_degrees = rot
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(c)
	_tex(c, file, Vector2(-pad, -pad), 0.0, true, look)
	return c


## A sprite in the school of the desk's era (or of `look`). Loose things on
## the desk cast a shadow once shadows have entered painting.
func _tex(parent: Node, file: String, pos: Vector2, rot: float, loose: bool = true, look: int = 0) -> TextureRect:
	var t := TextureRect.new()
	t.texture = Art.tex(file, look if look > 0 else era())
	t.position = pos
	t.rotation_degrees = rot
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if loose and Art.casts_shadow(era()):
		parent.add_child(Art.shadow_of(t.texture, pos))
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
