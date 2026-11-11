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
	desk.try_pair("Meiros", "khewos")
	await _save("ogretici_hata")
	desk.try_pair("ghewom", "khewos")
	await _save("ogretici_1")
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
	if desk.interlude_text() != "":
		await _save("belge%d_ara" % order)
		desk.dismiss_interlude()
		await create_timer(0.8).timeout
	await _save("belge%d" % order)
	desk.open_reading()
	await create_timer(0.4).timeout
	await _save("belge%d_okuma" % order)
	desk.close_reading()
	if order == 2:          # shelve the copy, leave a note, answer: the next document opens on the rumour
		desk.place_rule("R3", 0)
		desk.place_rule("R4", 1)
		desk.write_copy()
		await create_timer(3.5).timeout
		desk.get_node("Kopya/KenarNotu").text = "nēkos: sürgün, ölü değil"
		desk.add_note("nēkos: sürgün, ölü değil")
		await _save("belge2_not")
		desk.answer_question(1)
		desk.next_document()
		await create_timer(0.3).timeout
		await _save("belge3_ara")
	if order == 4:          # the words on loose slips, then carried into a new order
		desk.place_rule("R5", 0)
		desk.place_rule("R6", 1)
		await create_timer(0.5).timeout
		await _save("belge4_fisler")
		desk.move_word(2, 0)
		desk.move_word(3, 1)
		await _save("belge4_sirali")
		desk.write_copy()
		await create_timer(3.0).timeout
		desk.add_note("Sırayı ben değiştirdim; anlam aynı.")
		desk.answer_question(0)
		desk.next_document()
		await create_timer(0.3).timeout
		await _save("son")
