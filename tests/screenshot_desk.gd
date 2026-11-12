extends SceneTree
## Screens of the slice for looking at.
##   SHOTS=/tmp/shots godot --rendering-driver opengl3 --resolution 1920x1080 --script res://tests/screenshot_desk.gd
##   DOC=n   only document n;  ERA=n  paint it as era n

var out := ""


func _initialize() -> void:
	out = OS.get_environment("SHOTS") if OS.get_environment("SHOTS") != "" else "/tmp/shots"
	DirAccess.make_dir_recursive_absolute(out)
	_shoot()


func _save(name: String) -> void:
	await process_frame
	await process_frame
	root.get_texture().get_image().save_png("%s/desk_%s.png" % [out, name])


func _desk(order: int) -> Node:
	var desk: Node = load("res://scenes/desk.tscn").instantiate()
	desk.doc_order = order
	desk.era_look = int(OS.get_environment("ERA")) if OS.get_environment("ERA") != "" else 0
	root.add_child(desk)
	return desk


func _shoot() -> void:
	await process_frame
	var only := OS.get_environment("DOC")
	if only == "" or only == "1":
		var d := _desk(1)
		await create_timer(0.4).timeout
		await _save("masa")
		d.add_rule("R2")
		d._on_tile_hovered(d.tiles["R1"], true)
		d._on_word_hovered(d.words["ghewom"], true)
		await create_timer(0.4).timeout
		await _save("ogretici_1")
		d._on_tile_hovered(d.tiles["R1"], false)
		d.add_rule("R1")
		d.open_reading()
		await create_timer(0.3).timeout
		await _save("okuma")
		d.close_reading()
		d.write_copy()
		await create_timer(2.0).timeout
		await _save("soru")
		d.queue_free()
	if only == "" or only == "2":
		var d := _desk(2)
		await create_timer(0.4).timeout
		d.place_rule("R3", 0)
		d.place_rule("R4", 1)
		d._on_word_hovered(d.words["mēros"], true)
		await create_timer(0.4).timeout
		await _save("belge2")
		d.mark_word("mēros", "not")
		d.mark_word("mērom", "eski")
		await create_timer(0.3).timeout
		await _save("belge2_not")
		d.write_copy()
		await create_timer(1.5).timeout
		d.deliver()
		d.next_document()
		await create_timer(0.3).timeout
		await _save("belge3_ara")
		d.queue_free()
	if only == "" or only == "4":
		var d := _desk(4)
		await create_timer(0.3).timeout
		await _save("belge4_ara")
		d.dismiss_interlude()
		await create_timer(0.8).timeout
		d.place_rule("R5", 0)
		d.place_rule("R6", 1)
		d.move_word(2, 0)
		d.move_word(3, 1)
		await create_timer(0.4).timeout
		await _save("belge4_sirali")
		d.write_copy()
		await create_timer(1.5).timeout
		d.deliver()
		d.next_document()
		await create_timer(0.3).timeout
		await _save("son")
		d.queue_free()
	quit()
