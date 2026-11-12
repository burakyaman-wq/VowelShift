extends SceneTree
## Random real clicks on everything clickable; any SCRIPT ERROR in the output is a bug.
##   SEED=n DOC=n godot --script res://tests/fuzz_clicks.gd
var desk: Node
func _initialize() -> void:
	_go()
func click(p: Vector2) -> void:
	for pressed in [true, false]:
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_LEFT
		e.pressed = pressed
		e.position = p
		e.global_position = p
		root.push_input(e)
		await process_frame
func targets() -> Array:
	var out := []
	for n in desk.find_children("*", "Control", true, false):
		if n.is_visible_in_tree() and n.mouse_filter == Control.MOUSE_FILTER_STOP and n.get_global_rect().size.x > 2:
			out.append(n)
	return out
func _go() -> void:
	await process_frame
	seed(int(OS.get_environment("SEED")) if OS.get_environment("SEED") != "" else 1)
	desk = load("res://scenes/desk.tscn").instantiate()
	var dv := OS.get_environment("DOC")
	desk.doc_id = ("doc_0" + dv) if dv.is_valid_int() else (dv if dv != "" else "doc_01")
	root.add_child(desk)
	await create_timer(0.5).timeout
	for i in 300:
		var ts := targets()
		if ts.is_empty():
			break
		var t: Control = ts[randi() % ts.size()]
		var lbl := ""
		if t is Label: lbl = t.text
		print("click ", i, " ", t.name, " '", lbl.left(20), "'")
		await click(t.get_global_rect().get_center())
		await create_timer(0.05).timeout
	print("DONE doc=", desk.doc.order, " phase=", desk.state.phase)
	quit()
