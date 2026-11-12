extends SceneTree
## Replay a player's mouse actions from a fresh game, then save what the player sees.
##   ACTIONS=path OUT=prefix godot --resolution 1280x720 --script res://tests/play_cli.gd
## Action lines (window pixels, 1280x720):
##   click x y | dclick x y | hover x y | drag x1 y1 x2 y2 | key esc|enter|space | wait seconds
## Writes OUT.png (the screen) and OUT.txt (every readable text on screen with its box).
var desk: Node
var mouse := Vector2.ZERO
var held := false


func _initialize() -> void:
	_go()


func _push(e: InputEvent) -> void:
	root.push_input(e, false)


func _move(p: Vector2) -> void:
	var e := InputEventMouseMotion.new()
	e.position = p
	e.global_position = p
	e.relative = p - mouse
	e.button_mask = MOUSE_BUTTON_MASK_LEFT if held else 0
	mouse = p
	Input.warp_mouse(p)
	_push(e)
	await process_frame


func _button(p: Vector2, pressed: bool, double := false) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = pressed
	e.double_click = double
	e.position = p
	e.global_position = p
	e.button_mask = MOUSE_BUTTON_MASK_LEFT if pressed else 0
	held = pressed
	_push(e)
	await process_frame


func _key(name: String) -> void:
	var codes := {"esc": KEY_ESCAPE, "enter": KEY_ENTER, "space": KEY_SPACE}
	for pressed in [true, false]:
		var e := InputEventKey.new()
		e.keycode = codes.get(name, KEY_ESCAPE)
		e.physical_keycode = e.keycode
		e.pressed = pressed
		_push(e)
		await process_frame


func _run(line: String) -> void:
	var p := line.strip_edges().split(" ", false)
	if p.is_empty() or p[0].begins_with("#"):
		return
	var n := []
	for i in range(1, p.size()):
		n.append(float(p[i]) if p[i].is_valid_float() else 0.0)
	match p[0]:
		"hover":
			await _move(Vector2(n[0], n[1]))
		"click", "dclick":
			var at := Vector2(n[0], n[1])
			await _move(at)
			await _button(at, true, p[0] == "dclick")
			await _button(at, false)
		"drag":
			var a := Vector2(n[0], n[1])
			var b := Vector2(n[2], n[3])
			await _move(a)
			await _button(a, true)
			for k in range(1, 13):
				await _move(a.lerp(b, k / 12.0))
			await _button(b, false)
		"key":
			await _key(p[1] if p.size() > 1 else "esc")
		"wait":
			await create_timer(n[0] if n.size() > 0 else 1.0).timeout
	await create_timer(0.12).timeout


func _texts() -> String:
	var out := PackedStringArray()
	var to_window := root.get_final_transform()
	for n in root.find_children("*", "Control", true, false):
		if not n.is_visible_in_tree():
			continue
		var t := ""
		if n is Label:
			t = n.text
			if n.visible_characters >= 0:
				t = t.left(n.visible_characters)
		elif n is RichTextLabel:
			t = n.get_parsed_text()
		elif n is Button:
			t = n.text
		if t.strip_edges() == "" or n.modulate.a < 0.05 or n.self_modulate.a < 0.05:
			continue
		var r: Rect2 = to_window * n.get_global_rect()
		if r.end.x < 0 or r.end.y < 0 or r.position.x > 1280 or r.position.y > 720:
			continue
		out.append("[%d,%d %dx%d] %s" % [r.position.x, r.position.y, r.size.x, r.size.y, t.replace("\n", " / ")])
	return "\n".join(out)


func _go() -> void:
	await process_frame
	desk = load("res://scenes/desk.tscn").instantiate()
	root.add_child(desk)
	await create_timer(0.6).timeout
	var path := OS.get_environment("ACTIONS")
	var lines := FileAccess.get_file_as_string(path).split("\n") if path != "" and FileAccess.file_exists(path) else PackedStringArray()
	for line in lines:
		await _run(line)
	await create_timer(1.3).timeout
	await process_frame
	await process_frame
	var out := OS.get_environment("OUT")
	if out == "":
		out = "/tmp/play"
	root.get_texture().get_image().save_png(out + ".png")
	var f := FileAccess.open(out + ".txt", FileAccess.WRITE)
	f.store_string(_texts() + "\n")
	f.close()
	quit()
