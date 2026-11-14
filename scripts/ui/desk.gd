extends Control
## The scribe's desk, drawn as a classical Ottoman miniature seen from above
## (assets/art/STYLE.md), played as a card game. One document at a time:
##
## 1. The document's words lie below it as word cards, in the old language.
## 2. Sound cards are dealt to the hand: the shifts of the era, and one that
##    does not belong. Click one (or drag it) into the strip; the strip acts
##    left to right on every word at once. Hovering a card shows, faintly,
##    what it would do. The dictionary on the left opens at whatever word the
##    pointer is over.
## 3. Where a shift has made a word fall into another word's form, or mean
##    something else, the word card is marked. Drag a scribe card onto it:
##    a margin note, the old spelling, or scraping it out. Or leave it. Two
##    scales weigh the copy: fidelity (is the old meaning kept?) and clarity
##    (can today's reader read it?).
## 4. Click the reed pen to write. A copy of real words is shelved; click the
##    requester's slip to deliver it. What you wrote is what later eras read.
##
## In a document whose words may be reordered, the word cards can be dragged.
## Between documents a page tells what the years, or the street, made of the
## last copy. The master's note (Tutor) says what to do next.

signal copy_changed(text: String)
signal copy_written(result: Dictionary)

const FONT := preload("res://assets/fonts/Katip-Regular.ttf")
const INK := Color("2a1b14")
const RED := Color("b33a29")
const PAPER := Color("ecdcb9")
const PENCIL := Color(0.33, 0.29, 0.27, 0.85)
const SCRAPED := "#9c8466"
const RED_HEX := "#b33a29"
const DESK := Rect2(70, 64, 1780, 952)
const PER_PAGE := 12
const GRID := Vector2(606, 560)
const GRID_STEP := Vector2(176, 112)
const GRID_COLS := 4
const ERA_NAMES := ["", "I. çağ", "II. çağ", "III. çağ", "IV. çağ"]

@export var doc_order := 1
## Start at this document instead (its id); wins over doc_order.
@export var doc_id := ""
## Pick up the saved run and save after every delivery.
@export var autosave := false
@export var dev_cards := false          # kept for older tests; the hand is dealt either way
@export var era_look := 0               # paint the desk as this era whatever the document's; 0 = the document's

var engine: RuleEngine
var lib: ManuscriptLibrary
var state: GameState
var doc: Manuscript
var narrative: Narrative
var tray: RuleTray
var tiles_layer: Control
var tiles := {}
var words := {}                   # key -> WordCard
var tools := {}                   # tool -> ScribeCard
var marks := {}                   # word key -> scribe card laid on it
var tutor: Tutor
var _rest := {}
var _grain: TextureRect
var _seal: TextureRect
var _slip: Control
var _slip_text: RichTextLabel
var _book_left: Control
var _book_right: Control
var _words_layer: Control
var _scales := {}                 # "fidelity"/"clarity" -> Array of pips
var _reading: Control
var _reading_words := 0
var _interlude: Control
var _page := 0
var _focus := ""                  # word key the dictionary is opened at
var _advance := false
var _word_order: Array = []       # 1-based order of the words once moved; empty = as written
var _hand: Array = []
var _page_words: Array = []        # labels of the text written on the document
var _scale_titles := {}            # "fidelity"/"clarity" -> Label with the count
var _slip_glow: Tween
var _order_warn: Label
var _stranger_line := ""
var _armed := ""                   # a scribe card picked by click, waiting for a word
var _book_page: Control
var _ribbon: Label                 # the chronicle's latest line, across the top of the desk
const TOOL_INTRO := {
	"not": "[color=%s]Kenar notu[/color]: kelimeyi yeni biçimiyle yazar, eski anlamını kenara not eder. Sadakati korur, okuru yormaz.",
	"eski": "[color=%s]Eski yazım[/color]: kelimeyi hiç değiştirmeden eski hâliyle yazar. Anlam korunur ama bugünün okuru zorlanır (anlaşılırlık −1).",
	"kazi": "[color=%s]Kazı[/color]: kelimeyi kopyadan çıkarır. Bir şey silinir (sadakat −1); kimi zaman biri tam da bunu ister.",
}


var _ink_tween: Tween


func _ready() -> void:
	engine = RuleEngine.new()
	lib = ManuscriptLibrary.new()
	narrative = Narrative.new()
	state = GameState.load_or_new() if autosave else GameState.new()
	if not autosave:
		state.doc_index = lib.index_of(doc_id) if doc_id != "" else doc_order - 1
	if state.doc_index >= lib.docs.size():
		state.doc_index = 0
	state.phase = "read"
	_start_doc(false)


# --- what tests and other scenes call -----------------------------------------

## The copy as it stands: sound cards, scribe cards and word order applied.
func evaluation() -> Dictionary:
	var moved := not _word_order.is_empty() and _word_order != range(1, _word_order.size() + 1)
	return Copyist.evaluate(doc, engine, tray.model.order(), state.proven, marks, _word_order if moved else [])


func copy_text() -> String:
	return evaluation()["copy"]


## Rows of the evaluation (one per distinct word), for the copy as it stands.
func word_results() -> Array:
	return evaluation()["rows"]


func place_rule(rule_id: String, slot: int) -> void:
	if state.phase != "read":
		return
	var before := evaluation()
	var out := tray.model.place(rule_id, slot)
	if out != "":
		_send_home(tiles[out])
	_arrange()
	_refresh()
	_tell_change(before, rule_id)


## Put a sound card at the end of the strip.
func add_rule(rule_id: String) -> void:
	var order := tray.model.order()
	if rule_id in order:
		take_out(rule_id)
		return
	var slot := 0
	for i in tray.model.slots.size():
		if tray.model.slots[i] != "":
			slot = i + 1
	if slot >= tray.model.slots.size():
		slot = tray.model.slots.find("")
	if slot >= 0:
		place_rule(rule_id, slot)


func take_out(rule_id: String) -> void:
	if state.phase != "read":
		return
	tray.model.remove(rule_id)
	_arrange()
	_send_home(tiles[rule_id])
	_refresh()
	if tutor:
		tutor.tell("«%s» şeritten çıktı, eline döndü." % engine.by_id[rule_id].name_tr)


## Lay a scribe card on a word. False when none of that card is left.
func mark_word(key: String, tool: String) -> bool:
	if state:
		state.flags["tanit_" + tool] = true
	key = key.to_lower()
	if state.phase != "read" or not words.has(key) or tool not in Copyist.TOOLS:
		return false
	if marks.get(key, "") != tool and tools_left(tool) <= 0:
		tutor.tell("Elinde «%s» kalmadı." % Copyist.TOOL_NAMES[tool])
		return false
	marks[key] = tool
	_refresh()
	var row: Dictionary = words[key].row
	tutor.tell("«%s» kelimesine %s kondu." % [row["old"] if tool == "eski" else row["new"], Copyist.TOOL_NAMES[tool].to_lower()])
	return true


func unmark(key: String) -> void:
	if state.phase == "read" and marks.erase(key.to_lower()):
		_refresh()


func tools_left(tool: String) -> int:
	var used := 0
	for k in marks:
		if marks[k] == tool:
			used += 1
	return state.tools.get(tool, 0) - used


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


## The pen: the copy is written as it stands, if every word is a word.
func write_copy() -> Dictionary:
	if state.phase != "read":
		return {}
	var ev := evaluation()
	var res := state.shelve(doc, ev, marks)
	if not res["shelved"]:
		if res["error"] == "not_words":
			tutor.tell("Yazılamaz: [color=%s]%s[/color] sözlükte yok. Kartları değiştir ya da Eski yazım / Kazı koy." % [RED_HEX, ", ".join(res["blocked"])])
		return res
	for t in tiles.values():
		t.locked = true
	for c in tools.values():
		c.set_left(state.tools[c.tool])
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ink(ev)
	_write_copy_on_page(ev["copy"], Copyist.gloss(ev))
	for t in Copyist.TOOLS:
		if state.tools.get(t, 0) > 0 or marks.values().has(t):
			state.flags["tanit_" + t] = true
	if true:
		var me := doc.id
		var auto := create_tween()
		auto.tween_interval(1.1)
		auto.tween_callback(func() -> void:
			if doc and doc.id == me and state.phase == "answer":
				deliver())
	var stranger := Copyist.decoy(engine, doc.era)
	_seal.visible = true
	_slip_text.text = "[color=%s]Kopya yazıldı.[/color] Sahibine gidiyor." % RED_HEX
	_glow_slip(true)
	_stranger_line = ""
	if stranger != "" and stranger in _hand:
		var used := stranger in tray.model.order()
		_stranger_line = "Bu çağa ait olmayan kart «%s» idi; %s " % [engine.by_id[stranger].name_tr, "onu kullandın." if used else "doğru, onu kullanmadın."]
	tutor.tell("Kopya yazıldı: sadakat %d / %d, anlaşılırlık %d / %d." % [ev["fidelity"], Copyist.FULL, ev["clarity"], Copyist.FULL])
	_guide()
	copy_written.emit(res)
	return res


## Hand the shelved copy over; the next document follows.
func deliver() -> bool:
	if state.phase != "answer" or _advance:
		return false
	state.phase = "done"
	state.doc_index += 1
	if autosave:
		state.save()
	_advance = true
	_glow_slip(false)
	var stamp := _tex(_slip, "muhur.png", Vector2(250, 150), -10.0, false)
	stamp.scale = Vector2(0.6, 0.6)
	var tw := create_tween()
	tw.tween_interval(0.2)
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


## What the scribe learns before this document: what the years did, or what
## the street made of the last copy. Empty when there is nothing to tell.
func interlude_text() -> String:
	var last := lib.get_doc(state.doc_index - 1) if state.doc_index > 0 else null
	var after_story := last != null and last.kind == "ana" and state.scores.has(last.id)
	if doc.intro == "" and not after_story:
		return ""
	var parts := PackedStringArray()
	if last and state.scores.has(last.id):
		parts.append(_handoff_line(last))
	if doc.intro != "":
		parts.append(doc.intro)
	return "\n\n".join(parts)


## How the last copy was weighed and what came of it, in one line.
func _plain_text(t: String) -> String:
	var rx := RegEx.new()
	rx.compile("\\[[^\\]]*\\]")
	return rx.sub(t, "", true)


## The whole chronicle, era by era, on a page over the desk; a click closes it.
func open_chronicle() -> void:
	if _book_page or state.chronicle.is_empty():
		return
	_book_page = Control.new()
	_book_page.name = "Kronik"
	_book_page.set_anchors_preset(Control.PRESET_FULL_RECT)
	_book_page.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_book_page)
	move_child(_book_page, _grain.get_index())
	var dim := ColorRect.new()
	dim.color = Color(0.08, 0.04, 0.03, 0.82)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_book_page.add_child(dim)
	var page := Control.new()
	page.position = Vector2(200, 160)
	page.size = Vector2(1520, 760)
	page.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_book_page.add_child(page)
	_tex(page, "belge_okuma.png", Vector2(-8, -8), 0.0)
	_title(page, Vector2(610, 47), 30, "Kronik")
	var scribes := {1: "I. çağ · Leuka", 2: "II. çağ · Argos", 3: "III. çağ · Nīka"}
	var lines := PackedStringArray()
	var last_era := 0
	for c in state.chronicle:
		var m := lib.find(c["doc"])
		var e := m.era if m else 0
		if e != last_era:
			lines.append("\n[color=%s]%s[/color]" % [RED_HEX, scribes.get(e, "")])
			last_era = e
		lines.append("[b]%s[/b] — %s" % [state.titles.get(c["doc"], c["doc"]), c["line"]])
	var r := _rich(page, "\n".join(lines).strip_edges(), 21)
	r.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	r.scroll_active = true
	r.scroll_following = true
	r.mouse_filter = Control.MOUSE_FILTER_PASS
	r.position = Vector2(130, 120)
	r.size = Vector2(1260, 540)
	var go := _label(page, "kapatmak için tıkla", 22, RED)
	go.position = Vector2(1120, 664)
	_book_page.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			close_chronicle())


func close_chronicle() -> void:
	if _book_page:
		_book_page.queue_free()
		_book_page = null


func _handoff_line(last: Manuscript) -> String:
	var sc: Dictionary = state.scores[last.id]
	return "[color=%s]«%s» teslim edildi:[/color] sadakat %d / %d, anlaşılırlık %d / %d. %s" % [RED_HEX, last.title, sc["fidelity"], Copyist.FULL, sc["clarity"], Copyist.FULL, state.chronicle_of(last.id)]


func dismiss_interlude() -> void:
	if not _interlude:
		return
	_interlude.queue_free()
	_interlude = null
	_node("Terazi").visible = true
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
	var tw := page.create_tween()
	tw.tween_method(func(t: float) -> void:
		page.scale = Vector2.ONE * lerpf(0.45, 1.0, floorf(t * 3.0) / 3.0), 0.0, 1.0, 0.15)


func close_reading() -> void:
	if _reading:
		_reading.queue_free()
		_reading = null
		_reading_words = 0


func reading_word_count() -> int:
	return _reading_words


## The era the desk is painted in.
func era() -> int:
	return era_look if era_look > 0 else doc.era


# --- a document on the desk ---------------------------------------------------

func _start_doc(arrive: bool) -> void:
	if _ink_tween and _ink_tween.is_valid():
		_ink_tween.kill()
	doc = lib.get_doc(state.doc_index).resolved(state.flags)
	state.begin_doc(doc, engine)
	_hand = Copyist.hand(doc, engine)
	for rid in _hand:
		if rid not in state.cards:
			state.cards.append(rid)
		state.proven[rid] = range(engine.by_id[rid].sub_count())
	_reading = null
	_interlude = null
	_book_page = null
	_armed = ""
	_word_order = []
	marks = {}
	_focus = ""
	_page = 0
	for c in get_children():
		remove_child(c)
		c.queue_free()
	tiles.clear()
	words.clear()
	tools.clear()
	_rest.clear()
	_build()
	_refresh()
	var told := interlude_text()
	if told != "":
		for n in _arriving():
			n.visible = false
		_node("Terazi").visible = false
		_show_interlude(told, "Aradan geçen zaman" if doc.intro != "" else "Teslimden sonra")
	elif arrive:
		_arrive()
	_guide()
	var last := lib.get_doc(state.doc_index - 1) if state.doc_index > 0 else null
	if told == "" and last and state.scores.has(last.id) and tutor:
		tutor.tell("Teslim edildi; ne olduğu yukarıdaki kronikte.")


func _arriving() -> Array:
	return [_node("Belge"), _words_layer, _slip]


## The document, its words and the requester's slip slide in from the top edge.
func _arrive() -> void:
	for n in _arriving():
		var to: Vector2 = n.position
		n.visible = true
		n.position = to - Vector2(0, 900)
		var tw: Tween = n.create_tween()
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
	var dim := ColorRect.new()
	dim.color = Color(0.08, 0.04, 0.03, 0.82)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_interlude.add_child(dim)
	var page := Control.new()
	var short := text.length() < 360
	page.position = Vector2(200, 160)
	page.size = Vector2(1520, 760)
	page.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_interlude.add_child(page)
	_tex(page, "belge_okuma.png", Vector2(-8, -8), 0.0)
	_title(page, Vector2(610, 47), 30, heading)
	var r := _rich(page, _red_marks(text), 34 if short else 30)
	r.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	r.position = Vector2(150, 260 if short else 150)
	r.size = Vector2(1220, 300 if short else 500)
	var go := _label(page, "devam etmek için tıkla", 24, RED)
	go.position = Vector2(1120, 664)


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

	# the document, centre top
	var page := _sheet("Belge", "belge_kagit.png", Vector2(610, 100), Vector2(680, 440), -1.2, 8.0, Art.document_era(era()))
	_clickable(page, open_reading, Vector2(664, -12))
	_title(page, Vector2(190, 47), 28)
	_page_words = _write_text(page, doc.old_text, 680 - 52 - 110, 64, Vector2(60, 108), 300.0, INK)
	_seal = _tex(page, "muhur.png", Vector2(588, 352), -12.0, false)
	_seal.visible = false

	# the dictionary, left
	var book := _sheet("Defter", "defter.png", Vector2(64, 120), Vector2(520, 420), 1.0, 20.0)
	_label(book, "Sözlük · " + ERA_NAMES[doc.era], 22, RED).position = Vector2(22, 10)
	_book_left = Control.new()
	_book_left.mouse_filter = Control.MOUSE_FILTER_IGNORE
	book.add_child(_book_left)
	_book_right = Control.new()
	_book_right.position = Vector2(278, 0)
	_book_right.mouse_filter = Control.MOUSE_FILTER_IGNORE
	book.add_child(_book_right)

	# the requester's slip, the scales and the pen, right
	_slip = _sheet("Pusula", "pusula.png", Vector2(1336, 96), Vector2(360, 250), -3.0)
	_slip_text = _rich(_slip, doc.says_bbcode().replace("[i]", "[color=%s]" % RED_HEX).replace("[/i]", "[/color]"), 17)
	_slip_text.position = Vector2(18, 14)
	_slip_text.size = Vector2(324, 186)
	_clickable(_slip, func() -> void: deliver(), Vector2(330, -10))
	_build_scales(Vector2(1346, 380))
	var pen := Control.new()
	pen.name = "Kalem"
	pen.position = Vector2(1360, 676)
	pen.size = Vector2(250, 18)
	pen.rotation_degrees = -10.0
	add_child(pen)
	_tex(pen, "kalem.png", Vector2(-8, -8), 0.0)
	_clickable(pen, func() -> void: write_copy(), Vector2(240, -30))

	# the word cards, below the document
	_words_layer = Control.new()
	_words_layer.name = "Kelimeler"
	_words_layer.position = GRID
	_words_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_words_layer)
	var seen := {}
	var ws := doc.old_words()
	for i in ws.size():
		var key := ws[i].to_lower()
		if seen.has(key):
			continue
		seen[key] = true
		var c := WordCard.new()
		_words_layer.add_child(c)
		c.setup(FONT, era(), i + 1, doc.allow_reorder)
		c.repeats = Array(ws).filter(func(w: String) -> bool: return w.to_lower() == key).size()
		c.hovered.connect(_on_word_hovered)
		c.clicked.connect(_on_word_clicked)
		c.dropped.connect(_on_word_dropped)
		words[key] = c

	_order_warn = _label(_words_layer, "", 21, Color("f0b8a0"))
	_order_warn.position = Vector2(GRID_STEP.x + 8, GRID_STEP.y + 18)
	_order_warn.size = Vector2(GRID_STEP.x * 3 - 20, 70)
	_order_warn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART

	# the strip and the hand
	tray = RuleTray.new()
	tray.era = era()
	tray.position = Vector2(600, 790)
	add_child(tray)
	tiles_layer = Control.new()
	tiles_layer.name = "Karolar"
	tiles_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	tiles_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(tiles_layer)
	for rid in _hand:
		_add_tile(rid)

	# the scribe cards, bottom right
	# a job that has not reached the scribe cards yet shows none of them
	var shown := Copyist.TOOLS.filter(func(t: String) -> bool: return state.tools[t] > 0 or doc.tools.is_empty())
	if not shown.is_empty():
		_label(self, "Kâtip kartları · kelimeye sürükle", 20, PAPER).position = Vector2(1460, 770)
	for i in Copyist.TOOLS.size():
		var tool: String = Copyist.TOOLS[i]
		var sc := ScribeCard.new()
		add_child(sc)
		sc.setup(tool, state.tools[tool], FONT, era())
		sc.home = Vector2(1456 + shown.find(tool) * 134, 806)
		sc.position = sc.home
		sc.visible = tool in shown
		sc.dropped.connect(_on_tool_dropped)
		sc.clicked.connect(_on_tool_clicked)
		tools[tool] = sc

	var strip := NinePatchRect.new()
	strip.texture = Art.tex("kelime_fisi.png", era())
	for side in [SIDE_LEFT, SIDE_RIGHT]:
		strip.set_patch_margin(side, 18)
	for side in [SIDE_TOP, SIDE_BOTTOM]:
		strip.set_patch_margin(side, 12)
	strip.position = Vector2(600, 18)
	strip.size = Vector2(700, 76)
	strip.mouse_filter = Control.MOUSE_FILTER_STOP
	strip.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	strip.tooltip_text = "Kroniğin tamamı"
	add_child(strip)
	_clickable(strip, open_chronicle, Vector2(664, 22))
	_ribbon = _label(strip, "", 16, INK)
	_ribbon.position = Vector2(18, 8)
	_ribbon.size = Vector2(664, 60)
	_ribbon.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_ribbon.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_ribbon.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var latest: String = state.chronicle[-1]["line"] if not state.chronicle.is_empty() else ""
	_ribbon.text = ("Kronik: " + _plain_text(latest) if latest != "" else "Kronik: henüz bir şey yazılmadı.") + "  (tıkla: tamamı)"
	strip.visible = true

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


func _build_scales(at: Vector2) -> void:
	var box := Control.new()
	box.name = "Terazi"
	box.position = at
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(box)
	var rows := [["fidelity", "Sadakat", "eski anlam korunuyor mu"], ["clarity", "Anlaşılırlık", "bugünün okuru anlıyor mu"]]
	for i in rows.size():
		var y := i * 92.0
		_scale_titles[rows[i][0]] = _label(box, rows[i][1], 24, PAPER)
		_scale_titles[rows[i][0]].position = Vector2(0, y)
		_label(box, rows[i][2], 18, PAPER).position = Vector2(0, y + 34)
		var pips := []
		for k in Copyist.FULL:
			var p := TextureRect.new()
			p.texture = Art.tex("durak.png", era())
			p.position = Vector2(232 + k * 44, y + 2)
			p.scale = Vector2.ONE * 1.6
			p.mouse_filter = Control.MOUSE_FILTER_IGNORE
			box.add_child(p)
			pips.append(p)
		_scales[rows[i][0]] = pips


# --- words, cards and the dictionary -----------------------------------------

## The document's words, laid out on its page. Returns how many.
func _write_words(parent: Control, width: float, start: int, origin: Vector2, height: float) -> int:
	return _write_text(parent, doc.old_text, width, start, origin, height, INK).size()


## A text laid out on a page, one sentence a line, as large as fits the box.
func _write_text(parent: Control, text: String, width: float, start: int, origin: Vector2, height: float, color: Color) -> Array:
	var lines := _sentences(text)
	var fs := mini(_fit(lines, width, start), int(height / (lines.size() * 1.55)))
	var space := FONT.get_string_size(" ", HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var top := origin.y + maxf(0.0, (height - lines.size() * fs * 1.55) / 2.0)
	var out := []
	for li in lines.size():
		var x := origin.x
		for w in lines[li].split(" ", false):
			var l := _label(parent, w, fs, color)
			l.position = Vector2(x, top + li * fs * 1.55)
			x += FONT.get_string_size(w, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + space
			out.append(l)
	return out


## The pen has written: the old text moves up, the copy is written under it.
func _write_copy_on_page(copy: String, gloss: String = "", ink: Color = INK) -> void:
	var page := _node("Belge")
	for l in _page_words:
		if is_instance_valid(l):
			l.get_parent().remove_child(l)
			l.queue_free()
	_page_words = _write_text(page, doc.old_text, 680 - 52 - 110, 40, Vector2(60, 92), 126.0, PENCIL)
	var tag := _label(page, "Kopyan" if ink == INK else "Kopyan · kurşun kalemle", 18, RED)
	tag.position = Vector2(60, 222)
	_page_words.append(tag)
	_page_words += _write_text(page, copy, 680 - 52 - 110, 44, Vector2(60, 250), 140.0 if gloss == "" else 108.0, ink)
	if gloss != "":
		var margin := _label(page, "Kenarda: " + gloss, 17, RED)
		margin.position = Vector2(60, 362)
		margin.size = Vector2(470, 24)
		margin.clip_text = true
		margin.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		_page_words.append(margin)


func _glow_slip(on: bool) -> void:
	if _slip_glow and _slip_glow.is_valid():
		_slip_glow.kill()
	if not _slip:
		return
	_slip.modulate = Color.WHITE
	if on:
		_slip_glow = _slip.create_tween().set_loops()
		_slip_glow.tween_property(_slip, "modulate", Color(1.25, 1.12, 0.85), 0.55)
		_slip_glow.tween_property(_slip, "modulate", Color.WHITE, 0.55)


func _add_tile(rid: String) -> void:
	var i := tiles.size()
	var t := RuleTile.new()
	tiles_layer.add_child(t)
	t.setup(engine.by_id[rid], state.proven.get(rid, []), FONT, era())
	var spot := Vector2(70 + i * 168, 806)
	var rot: float = [-2.5, 1.5, -1.0, 2.0][i % 4]
	_rest[rid] = [spot, rot]
	t.dropped.connect(_on_tile_dropped)
	t.clicked.connect(func(tile: RuleTile) -> void: add_rule(tile.rule_id))
	t.hovered.connect(_on_tile_hovered)
	tiles[rid] = t
	t.position = spot
	t.rotation_degrees = rot


func _on_tile_dropped(tile: RuleTile) -> void:
	var slot := tray.slot_at(tile.center())
	if slot >= 0:
		place_rule(tile.rule_id, slot)
		return
	tray.model.remove(tile.rule_id)
	_arrange()
	_send_home(tile)
	_refresh()


## A sound card under the pointer: show faintly what it would do.
func _on_tile_hovered(tile: RuleTile, on: bool) -> void:
	if state.phase != "read" or tile.dragging:
		return
	var order := tray.model.order()
	if not on or tile.rule_id in order:
		for c in words.values():
			c.preview("")
		return
	var ev := Copyist.evaluate(doc, engine, order + [tile.rule_id], state.proven, marks)
	for r in ev["rows"]:
		var tag := "anlam kayar" if r["shifted"] else ("iki anlam" if r["collision"] else "")
		words[r["key"]].preview(r["new"], r["in_dict"], tag)


func _on_word_hovered(card: WordCard, on: bool) -> void:
	if on and not card.dragging:
		_focus = card.key
		_open_dictionary_at(card.row)
	elif not on and _focus == card.key and not card.dragging:
		_focus = ""
		_draw_entry({})


func _on_word_clicked(card: WordCard) -> void:
	if _armed != "":
		var tool := _armed
		_disarm()
		if not mark_word(card.key, tool):
			tutor.tell("Bu kelimeye konamaz ya da o karttan kalmadı.")
		return
	if marks.has(card.key):
		unmark(card.key)
		tutor.tell("«%s» kelimesinden kâtip kartı kaldırıldı." % card.row["new"])
	elif state.phase == "read":
		var r: Dictionary = card.row
		if r.get("collision", false) or r.get("shifted", false) or not r.get("elder", []).is_empty():
			tutor.tell("Sağdaki bir kâtip kartını bu kelimenin üstüne sürükle.")
		else:
			tutor.tell("«%s» kelimesinde sorun yok; kâtip kartı gerekmez." % r.get("new", ""))


## A word card let go: the words now read in the order the cards lie.
func _on_word_dropped(_card: WordCard) -> void:
	var cards: Array = words.values()
	cards.sort_custom(func(a: WordCard, b: WordCard) -> bool:
		var ra := roundi(a.position.y / GRID_STEP.y)
		var rb := roundi(b.position.y / GRID_STEP.y)
		return ra < rb if ra != rb else a.position.x < b.position.x)
	_word_order = cards.map(func(c: WordCard) -> int: return c.index)
	_refresh()
	if tutor:
		tutor.tell("Sıra değişti: " + evaluation()["copy"])


func _on_tool_clicked(card: ScribeCard) -> void:
	if state.phase != "read" or card.left <= 0:
		return
	var was := _armed
	_disarm()
	if was == card.tool:
		return
	_armed = card.tool
	card.armed = true
	tutor.tell("%s seçildi: şimdi bir kelime kartına tıkla." % Copyist.TOOL_NAMES[card.tool])


func _disarm() -> void:
	if _armed != "" and tools.has(_armed) and is_instance_valid(tools[_armed]):
		tools[_armed].armed = false
	_armed = ""


func _on_tool_dropped(card: ScribeCard) -> void:
	var at := card.center()
	card.go_home()
	for c in words.values():
		if c.get_global_rect().grow(10).has_point(at):
			mark_word(c.key, card.tool)
			return


func _arrange() -> void:
	for i in tray.model.slots.size():
		var rid := tray.model.slots[i]
		if rid != "":
			tiles[rid].slide_to(tray.tile_spot(i) - tiles_layer.global_position, 0.0)


func _send_home(tile: RuleTile) -> void:
	var rest: Array = _rest[tile.rule_id]
	tile.slide_to(rest[0], rest[1])


## Everything that follows from the strip, the scribe cards and the order.
func _refresh() -> void:
	var ev := evaluation()
	if state.phase == "read" and _node("Belge"):
		_write_copy_on_page(ev["copy"], Copyist.gloss(ev), PENCIL)
	var order: Array = _word_order if not _word_order.is_empty() else range(1, doc.old_words().size() + 1)
	# lay the cards out in the order they read, each distinct word once
	var laid := {}
	var k := 0
	for i in order:
		var key := doc.old_words()[int(i) - 1].to_lower()
		if laid.has(key):
			continue
		laid[key] = true
		var c: WordCard = words[key]
		c.position = Vector2((k % GRID_COLS) * GRID_STEP.x, (k / GRID_COLS) * GRID_STEP.y)
		c.rotation_degrees = [-1.0, 0.8, -0.4, 1.2][k % 4]
		k += 1
	for r in ev["rows"]:
		words[r["key"]].show_row(r, state.phase != "read")
	for t in tools:
		tools[t].set_left(tools_left(t) if state.phase == "read" else state.tools[t])
	_show_scales(ev)
	if _order_warn:
		_order_warn.text = {"wrong": "Şehir bu sırayı ters okur: önce gelen yapandır.", "unexplained": "Sıra aslından farklı: bir kelimeye Kenar notu koy."}.get(ev["order"], "")
	if _focus != "" and words.has(_focus):
		_open_dictionary_at(words[_focus].row)
	else:
		_draw_dictionary([])
		_draw_entry({})
	if tutor:
		_guide()
	copy_changed.emit(ev["copy"])


func _show_scales(ev: Dictionary) -> void:
	for scale_name in _scales:
		var n: int = ev[scale_name]
		var pips: Array = _scales[scale_name]
		for i in pips.size():
			pips[i].modulate = Color.WHITE if i < n else Color(1, 1, 1, 0.16)
		var title: Label = _scale_titles[scale_name]
		var text := "%s  %d / %d" % ["Sadakat" if scale_name == "fidelity" else "Anlaşılırlık", n, Copyist.FULL]
		if title.text != text:
			var was_shown := title.text.contains(" / ")
			var grew := was_shown and n > int(title.text.get_slice(" / ", 0).right(1))
			title.text = text
			if not was_shown:
				continue
			title.pivot_offset = Vector2(0, 14)
			var tw := title.create_tween()
			title.modulate = Color("e9c46a") if grew else Color("ff8a70")
			tw.tween_property(title, "modulate", Color.WHITE, 0.6)


## The dictionary opened at a word: its page, its entry lit, and on the right
## what the word means now and meant before.
func _open_dictionary_at(row: Dictionary) -> void:
	var lit: Array = row.get("now", [])
	if lit.is_empty() and row.get("mark", "") == "eski":
		lit = row["was"]
	var entries := Copyist.dictionary(engine, doc.era)
	for i in entries.size():
		if entries[i][1] in lit:
			_page = i / PER_PAGE
			break
	_draw_dictionary(lit)
	_draw_entry(row)


func _draw_dictionary(lit: Array) -> void:
	for c in _book_left.get_children():
		_book_left.remove_child(c)
		c.queue_free()
	var entries := Copyist.dictionary(engine, doc.era)
	var pages := ceili(entries.size() / float(PER_PAGE))
	for k in PER_PAGE:
		var i := _page * PER_PAGE + k
		if i >= entries.size():
			break
		var on: bool = entries[i][1] in lit
		var l := _label(_book_left, "%s — %s" % entries[i], 17, RED if on else INK)
		l.text_overrun_behavior = TextServer.OVERRUN_TRIM_WORD   # the right-hand page shows it whole
		l.position = Vector2(24, 46 + k * 27)
		l.size = Vector2(236, 26)
	var prev := _label(_book_left, "‹", 32, RED)
	prev.position = Vector2(14, 364)
	prev.custom_minimum_size = Vector2(56, 44)
	prev.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_clickable(prev, func() -> void: _turn(-1), Vector2(18, -6))
	_label(_book_left, "%d / %d" % [_page + 1, pages], 18, INK).position = Vector2(112, 380)
	var nxt := _label(_book_left, "›", 32, RED)
	nxt.position = Vector2(200, 364)
	nxt.custom_minimum_size = Vector2(56, 44)
	nxt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_clickable(nxt, func() -> void: _turn(1), Vector2(18, -6))


func _turn(step: int) -> void:
	var pages := ceili(Copyist.dictionary(engine, doc.era).size() / float(PER_PAGE))
	_page = posmod(_page + step, pages)
	_draw_dictionary([])


## The right-hand page: the word under the pointer, looked up.
func _draw_entry(row: Dictionary) -> void:
	for c in _book_right.get_children():
		_book_right.remove_child(c)
		c.queue_free()
	if row.is_empty():
		var hint := _label(_book_right, "Bir kelime kartının üstüne gel: anlamı burada açılır.", 18, INK)
		hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		hint.custom_minimum_size = Vector2(216, 0)
		hint.position = Vector2(8, 50)
		hint.size = Vector2(216, 120)
		return
	var shown: String = row["old"] if row["mark"] == "eski" else row["new"]
	_label(_book_right, shown, 30, INK).position = Vector2(8, 40)
	var y := 96.0
	var now: Array = row["now"] if row["mark"] != "eski" else row["was"]
	if now.is_empty():
		_label(_book_right, "Sözlükte yok.", 18, RED).position = Vector2(8, y)
		y += 34
	for i in now.size():
		var m := _label(_book_right, ("%d. %s" % [i + 1, now[i]]) if now.size() > 1 else now[i], 18, INK)
		m.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		m.custom_minimum_size = Vector2(216, 0)
		m.position = Vector2(8, y)
		m.size = Vector2(216, 50)
		y += 30 * maxi(1, m.get_line_count())
	var warning := ""
	if row["collision"] and row["mark"] == "":
		warning = "İki kelime aynı biçime düştü."
	elif not row.get("elder", []).is_empty() and row["mark"] == "":
		warning = "Yaşlılar eski dille okur: «%s»." % " / ".join(PackedStringArray(row["elder"]))
	if warning != "":
		var warn := _label(_book_right, warning, 17, RED)
		warn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		warn.custom_minimum_size = Vector2(216, 0)
		warn.position = Vector2(8, y + 4)
		warn.size = Vector2(216, 44)
		y += 50
	y += 16
	_label(_book_right, "Eskiden", 16, PENCIL).position = Vector2(8, y)
	var was := _label(_book_right, "%s — %s" % [row["old"], " / ".join(PackedStringArray(row["was"]))], 17, INK)
	was.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	was.custom_minimum_size = Vector2(216, 0)
	was.position = Vector2(8, y + 24)
	was.size = Vector2(216, 70)


# --- writing and the end ---------------------------------------------------------

func _ink(ev: Dictionary) -> void:
	_ink_tween = create_tween()
	for r in ev["rows"]:
		var c: WordCard = words[r["key"]]
		_ink_tween.tween_interval(0.12)
		_ink_tween.tween_callback(func() -> void:
			if is_instance_valid(c):
				c.show_row(r, true)
				c.scale = Vector2.ONE * 1.06)
		_ink_tween.tween_interval(0.08)
		_ink_tween.tween_callback(func() -> void:
			if is_instance_valid(c):
				c.scale = Vector2.ONE)


func _show_ending() -> void:
	var cover := Control.new()
	cover.name = "SonPerde"
	cover.set_anchors_preset(Control.PRESET_FULL_RECT)
	cover.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(cover)
	move_child(cover, _grain.get_index())
	var page := _sheet("Son", "belge_okuma.png", Vector2(200, 160), Vector2(1520, 760), 0.0, 8.0, Art.document_era(era()))
	move_child(page, _grain.get_index())
	_title(page, Vector2(610, 47), 30, "Elli yıl sonra")
	var r := _rich(page, _scales_line() + "\n\n" + narrative.ending(state), 23)
	r.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	r.scroll_active = true
	r.mouse_filter = Control.MOUSE_FILTER_PASS
	r.position = Vector2(120, 122)
	r.size = Vector2(1280, 548)
	var again := _label(page, "Son · baştan oynamak için tıkla", 22, RED)
	again.position = Vector2(1000, 650)
	page.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT and is_inside_tree() and get_tree().current_scene == self:
			if autosave and FileAccess.file_exists(GameState.SAVE_PATH):
				DirAccess.remove_absolute(ProjectSettings.globalize_path(GameState.SAVE_PATH))
			get_tree().change_scene_to_file("res://scenes/baslik.tscn"))


func _scales_line() -> String:
	var f := 0
	var c := 0
	for k in state.scores:
		f += state.scores[k]["fidelity"]
		c += state.scores[k]["clarity"]
	var full := Copyist.FULL * state.scores.size()
	return "[color=%s]Terazin: sadakat %d / %d, anlaşılırlık %d / %d.[/color]" % [RED_HEX, f, full, c, full]


# --- the master's note ---------------------------------------------------------

## The one thing to do next, and the stop mark beside where to do it.
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
		return [_stranger_line + "Kopya yazıldı; [color=%s]sahibine gidiyor[/color]." % RED_HEX, _rect("Pusula")]
	if state.phase != "read":
		return ["", none]
	var ev := evaluation()
	var order := tray.model.order()
	if order.is_empty():
		if doc.order == 1:
			return ["Eski belgeyi bugünün diline kopyalayacaksın. Sol alttaki [color=%s]ses kartlarından birine tıkla[/color]: şeride iner ve bütün kelimeler birlikte değişir. Kartın üstüne gelince sonucunu önceden görürsün." % RED_HEX, _hand_rect()]
		var before := lib.get_doc(state.doc_index - 1) if state.doc_index > 0 else null
		var stranger := Copyist.decoy(engine, doc.era)
		var has_stranger := stranger != "" and stranger in _hand
		var had_stranger := before != null and stranger in Copyist.hand(before, engine)
		if before and before.era != doc.era:
			return ["Yeni çağ: sözlük ve ses kartları değişti.%s" % (" [color=%s]Biri bu çağa ait değil[/color]. İpucu: istek notundaki kırmızı kelimeler bu çağın dilinden; kartların önizlemesini onlarla karşılaştır." % RED_HEX if has_stranger else " Kartların üstüne gelip önizlemeye bak."), _hand_rect()]
		if has_stranger and not had_stranger:
			return ["Elinde yeni bir kart var ve [color=%s]biri bu çağa ait değil[/color]: kelimeleri sözlükte olmayan ya da başka anlama gelen biçimlere çevirir. Önizlemeye ve istek notundaki kırmızı kelimelere bak; o kartı şeride koyma." % RED_HEX, _hand_rect()]
		if has_stranger:
			return ["Ses kartları aynı; [color=%s]yabancı kart yine elinde[/color]." % RED_HEX, _hand_rect()]
		if _hand.size() == 1:
			return ["Yeni iş. [color=%s]Ses kartına tıkla[/color]; kelimelerin nasıl değiştiğine bak." % RED_HEX, _hand_rect()]
		return ["Yeni iş. Hangi ses kartları bu belgeye uyuyor? Kartın üstüne gel, önizlemeye bak; [color=%s]uyanları şeride koy[/color]." % RED_HEX, _hand_rect()]
	if not ev["blocked"].is_empty():
		var where := tray.get_global_rect() if order.size() >= 2 else _hand_rect()
		if doc.era == 1:
			return ["Altında «sözlükte yok» yazan kelimeler bugün okunamaz. Eksik bir kart ekle ya da yanlış olanı çıkar: şeritteki bir karta tıklarsan eline döner.", where]
		return ["Altında «sözlükte yok» yazan kelimeler bugün okunamaz. Başka bir kart ekle ya da sırayı değiştir: kartlar soldan sağa uygulanır. Şeritteki bir kartı başka yuvaya sürükleyebilir ya da tıklayıp eline alabilirsin.", where]
	for t in Copyist.TOOLS:
		if state.tools.get(t, 0) > 0 and not state.flags.has("tanit_" + t):
			var target := _choice_word(t)
			if target != "":
				return ["Yeni kâtip kartı. " + (TOOL_INTRO[t] % RED_HEX) + " Bu işte seçim senin: «%s» kelimesine koymak ya da koymamak; ikisinin de sonucu olacak." % words[target].row.get("new", ""), words[target].get_global_rect()]
			return ["Yeni kâtip kartı. " + (TOOL_INTRO[t] % RED_HEX) + " Kartı bir kelimenin üstüne sürükle ya da karta tıklayıp kelimeye tıkla; geri almak için kelimeye tıkla.", _below_header(tools[t].get_global_rect())]
	var can_mark := tools_left("not") > 0 or tools_left("eski") > 0
	for r in ev["rows"]:
		if r["mark"] != "" or not can_mark:
			continue
		var at: Rect2 = words[r["key"]].get_global_rect()
		if r["shifted"]:
			return ["«%s» artık [color=%s]başka bir şey anlatıyor[/color] (sözlüğe bak). Şeritte bu çağa ait olmayan bir kart olabilir: ona tıklayıp geri al. Ya da kelimeye Eski yazım koy." % [r["new"], RED_HEX], at]
		if r["collision"]:
			return ["«%s» artık [color=%s]iki kelimenin biçimi[/color]; okur hangisi olduğunu bilemez. Sağ alttaki Kenar notu kartını bu kelimenin üstüne sürükle. Kâtip kartları her işte yeniden dağıtılır." % [r["new"], RED_HEX], at]
		if not r["elder"].is_empty():
			return ["«%s» bugün doğru, ama eski dili bilen [color=%s]yaşlılar onu «%s» diye okur[/color]. Kenar notu ya da Eski yazım bu yanlış okumayı önler; ya da öyle bırak." % [r["new"], RED_HEX, " / ".join(PackedStringArray(r["elder"]))], at]
	match ev["order"]:
		"wrong":
			return ["Ekler düştü; şehir kimin yaptığını artık kelime sırasından anlar: [color=%s]önce gelen yapandır[/color]. Eski yazıda -s ile biten kelime yapandı, -m ile biten etkilenen; kartın altındaki 'eski:' satırına bak. Kelime kartlarını sürükleyip sırayı kur." % RED_HEX, _words_layer.get_global_rect() if _words_layer else none]
		"unexplained":
			if tools_left("not") > 0:
				return ["Sıra artık doğru, ama aslından farklı. Nedenini yazmak için bir kelimeye [color=%s]Kenar notu[/color] koy; yoksa kopya sahte sanılabilir." % RED_HEX, _words_layer.get_global_rect() if _words_layer else none]
	for o in doc.outcomes:
		var w: Dictionary = o.get("when", {})
		if w.has("mark") and words.has(w["mark"][0]) and not marks.has(w["mark"][0]) and tools_left(w["mark"][1]) > 0 and not state.flags.has("secim_" + doc.id):
			var card: WordCard = words[w["mark"][0]]
			return ["Bu işte bir [color=%s]seçim[/color] var: «%s» kelimesine %s koymak ya da olduğu gibi bırakmak. İkisinin de sonucu olacak. Karar ver, sonra kalemi tıkla." % [RED_HEX, card.row.get("new", ""), Copyist.TOOL_NAMES[w["mark"][1]]], card.get_global_rect()]
	if ev["fidelity"] < Copyist.FULL or ev["clarity"] < Copyist.FULL:
		return ["Kopya yazılabilir ama terazi tam değil: sadakat %d / %d, anlaşılırlık %d / %d. İstersen düzelt; beğendiysen [color=%s]kalemi tıkla[/color]." % [ev["fidelity"], Copyist.FULL, ev["clarity"], Copyist.FULL, RED_HEX], _rect("Kalem")]
	return ["Kopya hazır, terazi tam. [color=%s]Kalemi tıkla[/color]." % RED_HEX, _rect("Kalem")]


## The word this job's story asks `tool` of ("" if none).
func _choice_word(tool: String) -> String:
	for o in doc.outcomes:
		var w: Dictionary = o.get("when", {})
		if w.has("mark") and w["mark"][1] == tool and words.has(w["mark"][0]):
			return w["mark"][0]
	return ""


## A scribe card's rect without its top, so the pointer stays off the header above it.
func _below_header(r: Rect2) -> Rect2:
	return Rect2(r.position + Vector2(8, 96), r.size - Vector2(8, 96))


func _hand_rect() -> Rect2:
	for rid in _hand:
		if tiles.has(rid) and not tray.model.order().has(rid):
			return tiles[rid].get_global_rect()
	return tray.get_global_rect()


func _rect(node_name: String) -> Rect2:
	var n := _node(node_name)
	return n.get_global_rect() if n else Rect2()


## Say what laying a card did to the words.
func _tell_change(before: Dictionary, rule_id: String) -> void:
	if not tutor:
		return
	var after := evaluation()
	var changed := 0
	var drifted := PackedStringArray()
	for i in after["rows"].size():
		var a: Dictionary = after["rows"][i]
		if a["new"] != before["rows"][i]["new"]:
			changed += 1
			if a["shifted"] and not before["rows"][i]["shifted"]:
				drifted.append(a["new"])
	var r: SoundRule = engine.by_id[rule_id]
	var line := "«%s» hiçbir kelimeyi değiştirmedi." % r.name_tr if changed == 0 else "«%s» %d kelimeyi değiştirdi." % [r.name_tr, changed]
	if not drifted.is_empty():
		line += " [color=%s]%s[/color] artık başka bir anlam taşıyor." % [RED_HEX, ", ".join(drifted)]
	tutor.tell(line)


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
	var down := [Vector2.INF]
	node.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT:
			if e.pressed:
				down[0] = e.global_position
			elif down[0] != Vector2.INF and e.global_position.distance_to(down[0]) <= 8.0:
				down[0] = Vector2.INF
				action.call()
			else:
				down[0] = Vector2.INF)


func _title(page: Control, pos: Vector2, size_px: int, text: String = "") -> void:
	var t := text if text != "" else doc.title
	var fs := size_px
	while fs > 16 and FONT.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > 250:
		fs -= 1
	var title := _label(page, t, fs, PAPER)
	title.position = pos
	title.size = Vector2(300, 46)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER


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
