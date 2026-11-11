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
	var only := OS.get_environment("DOC")
	if only != "":
		await _one(int(only))
		quit()
		return
	var desk: Node = load("res://scenes/desk.tscn").instantiate()
	root.add_child(desk)
	await process_frame
	await _save("masa")
	for p in [["ghewom", "khewos"], ["ghrebheti", "khrepheti"], ["bhāgom", "phāgos"], ["Meiros", "Mīros"], ["deiwosyo", "dīwos"], ["nākos", "khewos"]]:
		desk.try_pair(p[0], p[1])
	desk.place_rule("R1", 0)
	desk.place_rule("R2", 1)
	await create_timer(0.6).timeout
	await _save("eslesme")
	desk.open_reading()
	await create_timer(0.4).timeout
	await _save("okuma")
	desk.close_reading()
	desk.write_copy()
	await create_timer(1.6).timeout
	await _save("murekkep")
	await create_timer(4.0).timeout
	await _save("soru")
	quit()


## DOC=n: document n as it arrives, with every rule tile on the desk.
func _one(order: int) -> void:
	var desk: Node = load("res://scenes/desk.tscn").instantiate()
	desk.doc_order = order
	desk.dev_cards = true
	desk.era_look = int(OS.get_environment("ERA")) if OS.get_environment("ERA") != "" else 0
	root.add_child(desk)
	await create_timer(0.3).timeout
	await _save("belge%d" % order)
	desk.open_reading()
	await create_timer(0.4).timeout
	await _save("belge%d_okuma" % order)
