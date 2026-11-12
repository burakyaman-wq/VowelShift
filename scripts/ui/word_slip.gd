class_name WordSlip
extends Control
## One word of the copy on its own slip of paper, in a document whose words
## may be put in another order. Pick it up, carry it along the line, let go.
## Motion is paper cut-out, as everywhere on the desk.

signal dropped(slip: WordSlip)

const PAD := 6.0
const HEIGHT := 44.0
const INSET := 11.0

var index := 0              # which word of the copy this is (1-based), as the rules wrote it
var dragging := false
var _grab := Vector2.ZERO
var _mark: TextureRect


func setup(word: String, word_index: int, font: Font, font_size: int, color: Color, era: int) -> void:
	index = word_index
	name = "Fis_%d" % word_index
	var text_h := font.get_height(font_size)
	size = Vector2(font.get_string_size(word, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x + INSET * 2, maxf(HEIGHT, text_h + 14))
	custom_minimum_size = size
	pivot_offset = size / 2
	mouse_filter = Control.MOUSE_FILTER_STOP
	mouse_default_cursor_shape = Control.CURSOR_DRAG
	var paper := NinePatchRect.new()
	paper.texture = Art.tex("kelime_fisi.png", era)
	paper.position = Vector2(-PAD, -PAD)
	paper.size = size + Vector2(PAD, PAD) * 2
	paper.patch_margin_left = 18
	paper.patch_margin_right = 18
	paper.patch_margin_top = 12
	paper.patch_margin_bottom = 12
	paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(paper)
	var l := Label.new()
	l.text = word
	l.position = Vector2(INSET, (size.y - text_h) / 2)
	l.size = Vector2(size.x - INSET * 2, text_h)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	add_child(l)
	_mark = TextureRect.new()
	_mark.texture = Art.tex("durak.png", era)
	_mark.position = Vector2(size.x - 12, -22)
	_mark.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mark.visible = false
	add_child(_mark)
	mouse_entered.connect(func() -> void: _mark.visible = not dragging)
	mouse_exited.connect(func() -> void: _mark.visible = false)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			dragging = true
			_grab = get_parent().get_local_mouse_position() - position
			_mark.visible = false
			scale = Vector2.ONE * 1.06
			move_to_front()
		elif dragging:
			dragging = false
			scale = Vector2.ONE
			dropped.emit(self)
		accept_event()
	elif event is InputEventMouseMotion and dragging:
		position = get_parent().get_local_mouse_position() - _grab
		accept_event()


func center() -> Vector2:
	return position + size / 2
