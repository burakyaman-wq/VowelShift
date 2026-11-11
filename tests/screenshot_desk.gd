extends SceneTree
## Renders the desk once, for looking at it without the editor:
##   xvfb-run -s "-screen 0 1920x1080x24" godot --rendering-driver opengl3 --resolution 1920x1080 --script res://tests/screenshot_desk.gd
## Writes user://desk.png (and copies it to the path in the env var SHOT, if set).

func _initialize() -> void:
	_shoot()


func _shoot() -> void:
	await process_frame
	var desk: Node = load("res://scenes/desk.tscn").instantiate()
	root.add_child(desk)
	await process_frame
	desk.place_rule("R3", 0)
	desk.place_rule("R4", 1)
	desk.place_rule("R1", 3)
	await create_timer(0.6).timeout
	await process_frame
	var img := root.get_texture().get_image()
	var out := OS.get_environment("SHOT")
	img.save_png(out if out != "" else "user://desk.png")
	quit()
