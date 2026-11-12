class_name Tutor
extends Control
## The master's note: one line at a time on what to do next, a red stop
## mark beating beside the thing to do it with, and a pencilled line on what
## the last action did. The desk decides the steps (desk.gd, _guide); this
## only shows them.

const CARD := Rect2(64, 576, 524, 196)

var _card: Control
var _title: Label
var _say: RichTextLabel
var _said: RichTextLabel
var _mark: TextureRect
var _beat: Tween
var _font: Font


func setup(font: Font, era: int) -> void:
	name = "Usta"
	_font = font
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card = Control.new()
	_card.position = CARD.position
	_card.size = CARD.size
	_card.rotation_degrees = -0.8
	_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_card)
	var paper := NinePatchRect.new()
	paper.texture = Art.tex("pusula.png", era)
	paper.position = Vector2(-8, -8)
	paper.size = CARD.size + Vector2(16, 16)
	paper.patch_margin_left = 40
	paper.patch_margin_right = 60
	paper.patch_margin_top = 30
	paper.patch_margin_bottom = 60
	paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card.add_child(paper)
	_title = _label("Ustanın notu", 20, Color("b33a29"))
	_title.position = Vector2(20, 10)
	_say = _rich(19, Color("2a1b14"))
	_say.position = Vector2(20, 40)
	_say.size = Vector2(CARD.size.x - 44, 104)
	_said = _rich(17, Color(0.33, 0.29, 0.27))
	_said.size = Vector2(CARD.size.x - 120, 44)
	_said.position = Vector2(20, 146)
	_mark = TextureRect.new()
	_mark.texture = Art.tex("durak.png", era)
	_mark.pivot_offset = Vector2(16, 16)
	_mark.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mark.visible = false
	add_child(_mark)
	_beat = create_tween().set_loops()
	_beat.tween_property(_mark, "scale", Vector2.ONE * 2.6, 0.45)
	_beat.tween_property(_mark, "scale", Vector2.ONE * 1.7, 0.45)


## What to do now, and where. An empty text hides the card's line.
func show_step(bbcode: String, target: Rect2) -> void:
	_say.text = bbcode
	_mark.visible = target.size != Vector2.ZERO
	if _mark.visible:
		_mark.position = Vector2(target.end.x - 24, target.position.y - 8)
	_card.visible = bbcode != "" or _said.text != ""


## What the last action did.
func tell(bbcode: String) -> void:
	_said.text = bbcode
	_card.visible = true


func step_text() -> String:
	return _say.text


func feedback_text() -> String:
	return _said.text


func _label(text: String, size_px: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_theme_font_override("font", _font)
	l.add_theme_font_size_override("font_size", size_px)
	l.add_theme_color_override("font_color", color)
	_card.add_child(l)
	return l


func _rich(size_px: int, color: Color) -> RichTextLabel:
	var r := RichTextLabel.new()
	r.bbcode_enabled = true
	r.scroll_active = false
	r.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.add_theme_font_override("normal_font", _font)
	r.add_theme_font_size_override("normal_font_size", size_px)
	r.add_theme_color_override("default_color", color)
	_card.add_child(r)
	return r
