extends SceneTree
## Renders the desk for looking at it without the editor:
##   xvfb-run -s "-screen 0 1920x1080x24" godot --rendering-driver opengl3 --resolution 1920x1080 --script res://tests/screenshot_desk.gd
## Plays document 1 and writes desk_<n>.png into the folder named by SHOTS (default user://).

func _initialize() -> void:
	_shoot()


func _save(name: String) -> void:
	await process_frame
	var dir := OS.get_environment("SHOTS")
	root.get_texture().get_image().save_png((dir if dir != "" else "user://") + "/desk_%s.png" % name)


func _shoot() -> void:
	await process_frame
	var desk: Node = load("res://scenes/desk.tscn").instantiate()
	root.add_child(desk)
	await process_frame
	for p in [["ghewom", "khewos"], ["ghrebheti", "khrepheti"], ["bhāgom", "phāgos"], ["Meiros", "Mīros"], ["deiwosyo", "dīwos"], ["nākos", "khewos"]]:
		desk.try_pair(p[0], p[1])
	desk.place_rule("R1", 0)
	desk.place_rule("R2", 1)
	await create_timer(0.6).timeout
	await _save("eslesme")
	desk.write_copy()
	await create_timer(5.5).timeout
	await _save("soru")
	quit()
