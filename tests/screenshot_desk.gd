extends SceneTree
## Renders the desk for looking at it without the editor:
##   xvfb-run -s "-screen 0 1920x1080x24" godot --rendering-driver opengl3 --resolution 1920x1080 --script res://tests/screenshot_desk.gd
## Writes desk_<n>.png into the folder named by the env var SHOTS (default user://).

func _initialize() -> void:
	_shoot()


func _save(name: String) -> void:
	await process_frame
	var dir := OS.get_environment("SHOTS")
	root.get_texture().get_image().save_png((dir if dir != "" else "user://") + "/desk_%s.png" % name)


func _shoot() -> void:
	await process_frame
	var desk: Node = load("res://scenes/desk.tscn").instantiate()
	desk.doc_order = 3
	root.add_child(desk)
	await process_frame
	desk.place_rule("R4", 0)
	desk.place_rule("R3", 1)
	desk.write_copy()
	await create_timer(3.2).timeout
	await _save("murekkep")
	desk.open_reading()
	desk.toggle_word(2)
	await create_timer(0.4).timeout
	await _save("okuma")
	quit()
