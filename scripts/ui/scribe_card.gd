class_name ScribeCard
extends Control
## A scribe card: the scribe's own hand in the copy. Drag it onto a word.
## It shows how many are left for the rest of the work.

signal dropped(card: ScribeCard)
signal hovered(card: ScribeCard, on: bool)

const SIZE := Vector2(124, 160)
const BLURB := {
	"not": "Anlamı kenarda açıklar.",
	"eski": "Kaydırmadan, eski hâliyle yazar.",
	"kazi": "Kelimeyi kopyadan çıkarır.",
}

var tool := ""
var left := 0
var home := Vector2.ZERO
var dragging := false
var _grab := Vector2.ZERO
var _count: Label


func setup(kind: String, count: int, font: Font, era: int) -> void:
	tool = kind
	name = "Kart_" + kind
	size = SIZE
	custom_minimum_size = SIZE
	pivot_offset = SIZE / 2
	mouse_filter = Control.MOUSE_FILTER_STOP
	mouse_default_cursor_shape = Control.CURSOR_DRAG
	var paper := NinePatchRect.new()
	paper.texture = Art.tex("pusula.png", era)
	paper.position = Vector2(-6, -6)
	paper.size = SIZE + Vector2(12, 12)
	paper.set_patch_margin(SIDE_LEFT, 30)
	paper.set_patch_margin(SIDE_RIGHT, 40)
	paper.set_patch_margin(SIDE_TOP, 24)
	paper.set_patch_margin(SIDE_BOTTOM, 44)
	paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(paper)
	var title := _label(font, Copyist.TOOL_NAMES[kind], 20, Color("b33a29"))
	title.position = Vector2(12, 10)
	var blurb := _label(font, BLURB[kind], 16, Color("2a1b14"))
	blurb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	blurb.custom_minimum_size = Vector2(SIZE.x - 24, 0)
	blurb.position = Vector2(12, 44)
	blurb.size = Vector2(SIZE.x - 24, 70)
	_count = _label(font, "", 18, Color("2a1b14"))
	_count.position = Vector2(12, SIZE.y - 34)
	set_left(count)
	mouse_entered.connect(func() -> void: hovered.emit(self, true))
	mouse_exited.connect(func() -> void: hovered.emit(self, false))


func set_left(n: int) -> void:
	left = n
	_count.text = "%d kaldı" % n
	modulate = Color.WHITE if n > 0 else Color(1, 1, 1, 0.45)
	mouse_default_cursor_shape = Control.CURSOR_DRAG if n > 0 else Control.CURSOR_FORBIDDEN


func center() -> Vector2:
	return global_position + SIZE / 2


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed and left > 0:
			dragging = true
			_grab = get_global_mouse_position() - global_position
			move_to_front()
			scale = Vector2.ONE * 1.05
		elif not event.pressed and dragging:
			dragging = false
			scale = Vector2.ONE
			dropped.emit(self)
		accept_event()
	elif event is InputEventMouseMotion and dragging:
		global_position = get_global_mouse_position() - _grab
		accept_event()


func go_home() -> void:
	position = home


func _label(font: Font, text: String, px: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", px)
	l.add_theme_color_override("font_color", color)
	add_child(l)
	return l
