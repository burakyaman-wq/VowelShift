class_name RuleTile
extends Control
## A glazed rule tile. The cobalt pictogram and the name sit under the glaze
## and never change; the proven correspondences are written over it in ink.
## Pick it up with the mouse and drop it in the tray. Motion is paper
## cut-out: the tile lifts a little when held and slides in a few steps.

signal picked(tile: RuleTile)
signal dropped(tile: RuleTile)

const SPRITES := "res://assets/art/sprites/"
const SIZE := Vector2(150, 200)
const PAD := 8.0
const INK := Color("2a1b14")
const LAPIS_DK := Color("1e3171")
const STEPS := 4.0

var rule_id := ""
var dragging := false
var locked := false        # set once the copy is shelved
var _grab := Vector2.ZERO
var _tween: Tween
var _hover: TextureRect
var _lines: Array[Label] = []
var _font: Font


func setup(rule: SoundRule, proven_idx: Array, font: Font) -> void:
	rule_id = rule.id
	_font = font
	name = "Karo_" + rule.id
	size = SIZE
	custom_minimum_size = SIZE
	pivot_offset = SIZE / 2
	mouse_filter = Control.MOUSE_FILTER_STOP
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	_add_texture("karo_cerceve.png")
	_add_texture("picto_%s.png" % rule.id)
	var title := _label(_two_lines(rule.name_tr, 15, SIZE.x - 54), 15, LAPIS_DK)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_constant_override("line_spacing", -7)
	title.position = Vector2(14, 14)
	title.size = Vector2(SIZE.x - 28, 40)
	for i in 3:
		var l := _label("", 19, INK)
		l.position = Vector2(22, 112 + i * 22)
		_lines.append(l)
	set_proven(RuleText.proven_lines(rule, proven_idx))
	_hover = TextureRect.new()
	_hover.texture = load(SPRITES + "durak.png")
	_hover.position = Vector2(SIZE.x - 10, -18)
	_hover.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hover.visible = false
	add_child(_hover)
	mouse_entered.connect(func() -> void: _hover.visible = not dragging and not locked)
	mouse_exited.connect(func() -> void: _hover.visible = false)


## Ink in the proven lines; the rest of the tile stays blank glaze.
func set_proven(lines: PackedStringArray) -> void:
	for i in _lines.size():
		_lines[i].text = lines[i] if i < lines.size() else ""


func _gui_input(event: InputEvent) -> void:
	if locked:
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			dragging = true
			_grab = get_global_mouse_position() - global_position
			_hover.visible = false
			_lift(true)
			picked.emit(self)
		elif dragging:
			dragging = false
			_lift(false)
			dropped.emit(self)
		accept_event()
	elif event is InputEventMouseMotion and dragging:
		global_position = get_global_mouse_position() - _grab
		accept_event()


## Slide to a resting place in a few hard steps, as a cut-out is moved.
func slide_to(pos: Vector2, rot_deg: float, duration: float = 0.16) -> void:
	var from_pos := position
	var from_rot := rotation_degrees
	if _tween and _tween.is_valid():
		_tween.kill()
	var tw := create_tween()
	_tween = tw
	tw.tween_method(func(t: float) -> void:
		var k := floorf(t * STEPS) / STEPS
		position = from_pos.lerp(pos, k)
		rotation_degrees = lerpf(from_rot, rot_deg, k), 0.0, 1.0, duration)


func center() -> Vector2:
	return global_position + SIZE / 2


func _lift(up: bool) -> void:
	scale = Vector2.ONE * (1.05 if up else 1.0)
	if up:
		rotation_degrees -= 2.0
		move_to_front()


## Break a name at the space nearest its middle when it is wider than `width`.
## The reed-pen strokes overhang their advance, so this measures, then breaks.
func _two_lines(text: String, font_size: int, width: float) -> String:
	if _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x <= width:
		return text
	var best := -1
	for i in text.length():
		if text[i] == " " and (best < 0 or absi(i - text.length() / 2) < absi(best - text.length() / 2)):
			best = i
	return text if best < 0 else text.substr(0, best) + "\n" + text.substr(best + 1)


func _add_texture(file: String) -> void:
	var t := TextureRect.new()
	t.texture = load(SPRITES + file)
	t.position = Vector2(-PAD, -PAD)
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(t)


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.add_theme_font_override("font", _font)
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	add_child(l)
	return l
