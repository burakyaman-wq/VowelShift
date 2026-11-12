class_name WordCard
extends Control
## One word of the document, as the strip of sound cards now writes it.
## Its changed letters are red; a word no dictionary of the era knows is
## struck through; a word that has fallen into another word's form wears a
## red mark. A scribe card laid on it is shown at its foot. Hovering a sound
## card in the hand shows, faintly, what this word would become.
## In a document whose words may be reordered, the card can be dragged.

signal hovered(card: WordCard, on: bool)
signal dropped(card: WordCard)
signal clicked(card: WordCard)

const SIZE := Vector2(168, 104)
const INK := Color("2a1b14")
const RED := Color("b33a29")
const PENCIL := Color("4a3a2e")
const SCRAPED := "#7d5f43"
const MARK_TEXT := {"not": "kenar notu", "eski": "eski yazım", "kazi": "kazındı"}

var key := ""
var index := 0              # place in the document (1-based), for reordering
var movable := false
var dragging := false
var row: Dictionary = {}
var _grab := Vector2.ZERO
var _press := Vector2.ZERO
var _word: RichTextLabel
var _was: Label
var _foot: Label
var _ghost: Label
var _flag: TextureRect
var _font: Font


func setup(font: Font, era: int, word_index: int, can_move: bool) -> void:
	_font = font
	index = word_index
	movable = can_move
	size = SIZE
	custom_minimum_size = SIZE
	pivot_offset = SIZE / 2
	mouse_filter = Control.MOUSE_FILTER_STOP
	mouse_default_cursor_shape = Control.CURSOR_DRAG if can_move else Control.CURSOR_ARROW
	var paper := NinePatchRect.new()
	paper.texture = Art.tex("kelime_fisi.png", era)
	paper.position = Vector2(-6, -6)
	paper.size = SIZE + Vector2(12, 12)
	for side in [SIDE_LEFT, SIDE_RIGHT]:
		paper.set_patch_margin(side, 18)
	for side in [SIDE_TOP, SIDE_BOTTOM]:
		paper.set_patch_margin(side, 12)
	paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(paper)
	_word = RichTextLabel.new()
	_word.bbcode_enabled = true
	_word.fit_content = true
	_word.scroll_active = false
	_word.autowrap_mode = TextServer.AUTOWRAP_OFF
	_word.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_word.add_theme_font_override("normal_font", font)
	_word.add_theme_font_size_override("normal_font_size", 28)
	_word.add_theme_color_override("default_color", INK)
	_word.position = Vector2(12, 6)
	_word.size = Vector2(SIZE.x - 24, font.get_height(28))
	add_child(_word)
	_was = _label(17, PENCIL)
	_was.position = Vector2(14, 6 + font.get_height(28) - 4)
	_foot = _label(17, RED)
	_foot.position = Vector2(14, SIZE.y - font.get_height(17) - 4)
	_ghost = _label(19, Color(0.12, 0.24, 0.6))
	_ghost.position = Vector2(14, SIZE.y - font.get_height(19) - 2)
	_flag = TextureRect.new()
	_flag.texture = Art.tex("durak.png", era)
	_flag.position = Vector2(SIZE.x - 22, -10)
	_flag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_flag)
	mouse_entered.connect(func() -> void:
		if not dragging:
			scale = Vector2.ONE * 1.04
		hovered.emit(self, true))
	mouse_exited.connect(func() -> void:
		if not dragging:
			scale = Vector2.ONE
		hovered.emit(self, false))


## Show a row of Copyist.evaluate.
func show_row(r: Dictionary, inked: bool = false) -> void:
	row = r
	key = r["key"]
	name = "Kelime_" + key
	var shown: String
	match r["mark"]:
		"eski":
			shown = r["old"]
		"kazi":
			shown = "[color=%s][s]%s[/s][/color]" % [SCRAPED, r["new"]]
		_:
			if not r["in_dict"]:
				shown = "[color=%s][s]%s[/s][/color]" % [SCRAPED, r["new"]]
			elif inked:
				shown = r["new"]
			else:
				shown = _red_letters(r["new"], Pairing.diff_marks(r["old"], r["new"])[1])
	_word.text = shown
	_was.text = "değişmedi" if r["new"] == r["old"] else "eski: " + r["old"]
	var issue := ""
	if not r["in_dict"]:
		issue = "sözlükte yok"
	elif r["shifted"]:
		issue = "anlamı kaydı"
	elif r["collision"]:
		issue = "iki anlam"
	elif not r.get("elder", []).is_empty():
		issue = "yaşlılar başka okur"
	_foot.text = MARK_TEXT.get(r["mark"], issue)
	_flag.visible = r["mark"] == "" and issue != "" and issue != "sözlükte yok"
	_ghost.text = ""
	_foot.visible = true


## What the hovered sound card would make of this word ("" to clear);
## a form that is no word of the era is said so.
func preview(form: String, is_word: bool = true) -> void:
	_ghost.text = ("→ " + form + ("" if is_word else " (yok)")) if form != "" and form != row.get("new", "") else ""
	_foot.visible = _ghost.text == ""


func center() -> Vector2:
	return global_position + SIZE / 2


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_press = get_global_mouse_position()
			if movable:
				dragging = true
				_grab = get_parent().get_local_mouse_position() - position
				move_to_front()
				scale = Vector2.ONE * 1.05
		else:
			var moved := get_global_mouse_position().distance_to(_press) > 6.0
			if dragging:
				dragging = false
				scale = Vector2.ONE
			if moved and movable:
				dropped.emit(self)
			else:
				clicked.emit(self)
		accept_event()
	elif event is InputEventMouseMotion and dragging:
		position = get_parent().get_local_mouse_position() - _grab
		accept_event()


func _label(px: int, color: Color) -> Label:
	var l := Label.new()
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_theme_font_override("font", _font)
	l.add_theme_font_size_override("font_size", px)
	l.add_theme_color_override("font_color", color)
	add_child(l)
	return l


static func _red_letters(w: String, m: PackedInt32Array) -> String:
	var out := ""
	for i in w.length():
		out += ("[color=#b33a29]%s[/color]" % w[i]) if m[i] == 1 else w[i]
	return out
