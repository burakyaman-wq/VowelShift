class_name RuleTray
extends Control
## The wooden rule tray: five slots, applied left to right.

const SPRITES := "res://assets/art/sprites/"
const SLOTS := 5
const SLOT_W := 162.0
const SLOT_H := 212.0
const PAD := 8.0

var model := TrayModel.new(SLOTS)


func _ready() -> void:
	name = "Tepsi"
	size = Vector2(SLOTS * SLOT_W + 24, SLOT_H + 24)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := TextureRect.new()
	bg.texture = load(SPRITES + "tepsi.png")
	bg.position = Vector2(-PAD, -PAD)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)


func slot_rect(i: int) -> Rect2:
	return Rect2(global_position + Vector2(12 + i * SLOT_W + 3, 12), Vector2(SLOT_W - 6, SLOT_H))


## The slot under a point, or -1. A little slack so a near miss still lands.
func slot_at(global_point: Vector2) -> int:
	for i in SLOTS:
		if slot_rect(i).grow(14).has_point(global_point):
			return i
	return -1


## Where a tile's top-left corner goes when it lies in slot i.
func tile_spot(i: int) -> Vector2:
	var r := slot_rect(i)
	return r.position + (r.size - RuleTile.SIZE) / 2
