extends SceneTree
## Headless test runner:
##   godot --headless --script res://tests/run_tests.gd
## Compares the GDScript rule engine with the Python simulator's fixtures.

const FIXTURES := "res://tests/fixtures/rule_fixtures.json"

var failures := 0
var checks := 0


func _init() -> void:
	var engine := RuleEngine.new()
	var fx: Dictionary = RuleEngine._read_json(FIXTURES)

	for item in fx["forms"]:
		for era_str in item["eras"]:
			var got := engine.apply_word(item["form"], engine.era_ids(int(era_str)))
			_expect(got == item["eras"][era_str], "%s @era%s: got %s, want %s" % [item["form"], era_str, got, item["eras"][era_str]])

	for s in fx["swaps"]:
		var got := engine.apply_word(s["word"], s["order"])
		_expect(got == s["expect"], "swap %s %s: got %s, want %s" % [s["word"], s["order"], got, s["expect"]])

	# Partial cards: only the proven sub-rules apply.
	_expect(engine.apply_word("ghrebheti", ["R1"], {"R1": [2]}) == "khrebheti", "partial R1 (gh only)")
	_expect(engine.apply_word("domos", ["R5"], {"R5": [0]}) == "domo", "partial R5 (-s only)")
	_expect(engine.apply_word("domom", ["R5"], {"R5": [0]}) == "domom", "partial R5 leaves -m")

	# Validation by "real word": the key-word trap passes, other errors don't.
	_expect(engine.is_real("nīkos", 2), "nīkos is a real era-2 word (ölü)")
	_expect(not engine.is_real("grīnom", 2), "grīnom is not a real era-2 word")
	_expect(engine.apply_text("Mīros Mērom ageti. Mēros nākos.", ["R4", "R3"]) == "Mīros Mīrom ageti. Mīros nīkos.", "doc 2 wrong order")

	# Manuscripts load, are ordered and pass content validation.
	var lib := ManuscriptLibrary.new()
	_expect(lib.docs.size() >= 4, "at least 4 manuscripts load")
	_expect(lib.get_doc(0).id == "doc_01", "manuscripts sorted by order")
	for e in lib.validate(engine):
		_expect(false, "content: " + e)
	_expect(lib.get_doc(1).says_bbcode().begins_with("[i]Rīgos[/i]"), "italics become BBCode")
	_expect(lib.get_doc(3).allow_reorder, "doc 4 allows reordering")

	_play_through(engine, lib)


## The desk scene needs a running tree, so its tests wait for the first frame.
func _initialize() -> void:
	_finish()


func _finish() -> void:
	await process_frame
	_desk_tests()
	print("%d checks, %d failures" % [checks, failures])
	quit(1 if failures > 0 else 0)


func _desk_tests() -> void:
	var engine := RuleEngine.new()
	_expect(RuleText.sub_text(engine.by_id["R1"], 0) == "bh → ph", "tile text R1")
	_expect(RuleText.sub_text(engine.by_id["R5"], 1) == "-m → ∅", "tile text R5 (word-final, deleted)")
	_expect(RuleText.sub_text(engine.by_id["R6"], 0) == "kh → ş", "tile text R6 (condition left to the pictogram)")
	_expect(RuleText.sub_text(engine.by_id["R8"], 0) == "-o/-e → ∅", "tile text R8 (character class)")
	_expect(",".join(RuleText.proven_lines(engine.by_id["R1"], [2])) == "gh → kh", "only proven lines are inked")

	var m := TrayModel.new(5)
	m.place("R3", 0)
	m.place("R4", 1)
	_expect(",".join(m.order()) == "R3,R4", "tray reads left to right")
	_expect(m.place("R4", 0) == "", "moving within the tray swaps")
	_expect(",".join(m.order()) == "R4,R3", "swap reverses the order")
	_expect(m.place("R1", 1) == "R3", "a tile from the desk pushes the occupant out")
	m.remove("R4")
	_expect(",".join(m.order()) == "R1", "removing leaves the rest")

	var desk: Node = load("res://scenes/desk.tscn").instantiate()
	root.add_child(desk)
	_expect(desk.tiles.size() == 4, "doc 2 desk lays out R1-R4")
	_expect(desk.copy_text() == "Mīros Mērom ageti. Mēros nākos.", "empty tray copies letter for letter")
	desk.place_rule("R3", 0)
	desk.place_rule("R4", 1)
	_expect(desk.copy_text() == "Mīros Mīrom ageti. Mīros nēkos.", "R3 then R4 gives the right copy")
	desk.place_rule("R4", 0)
	_expect(desk.copy_text() == "Mīros Mīrom ageti. Mīros nīkos.", "swapping the tiles changes the copy (the trap)")
	desk.take_out("R4")
	_expect(desk.copy_text() == "Mīros Mīrom ageti. Mīros nākos.", "a tile taken out stops applying")
	desk.queue_free()


func _expect(ok: bool, msg: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		printerr("FAIL: " + msg)


## Scripted playthroughs: A = careful (correct order, reorder doc 4, notes),
## B = hasty (wrong order in doc 2, literal doc 4). Texts must match the prototype.
func _play_through(engine: RuleEngine, lib: ManuscriptLibrary) -> void:
	var story: Dictionary = RuleEngine._read_json("res://tests/fixtures/story_fixtures.json")
	var narr := Narrative.new()
	for name in ["A", "B"]:
		var careful: bool = name == "A"
		var g := GameState.new()
		# Doc 1
		var d := lib.get_doc(0)
		g.begin_doc(d, engine)
		_expect(g.prove_rule(d, lib, engine, "gh", "kh", ["ghewom:khewom", "ghrebheti:khrepheti"]).ok, name + " prove gh")
		_expect(not g.prove_rule(d, lib, engine, "gh", "kh", ["ghewom:khewos", "ghos:khos"]).ok, name + " fake/affix pairs rejected")
		_expect(g.make_copy(d, engine, ["R1"]).shelved == false, name + " copy needs bh and ei")
		_expect(g.prove_rule(d, lib, engine, "bh", "ph", ["bhāgom:phāgom", "ghrebheti:khrepheti"]).updated, name + " card updated")
		_expect(g.prove_rule(d, lib, engine, "ei", "ii", ["Meiros:Miiros", "deiwosyo:diiwosyo"]).ok, name + " aa-style input")
		_expect(g.make_copy(d, engine, ["R1", "R2"]).shelved, name + " doc1 shelved")
		g.answer(d, 0)
		# Doc 2
		d = lib.get_doc(1)
		g.begin_doc(d, engine)
		_expect(g.prove_rule(d, lib, engine, "ē", "ī", ["rēgos:rīgos", "thētos:thītos"]).ok, name + " prove ē→ī")
		_expect(g.prove_rule(d, lib, engine, "ā", "ē", ["grānos:grēnos", "āgros:ēgros"]).ok, name + " prove ā→ē")
		var r := g.make_copy(d, engine, ["R3", "R4"] if careful else ["R4", "R3"])
		_expect(r.shelved and r.copy == story[name]["copy2"], name + " doc2 copy: " + r.copy)
		if careful:
			g.add_note(d, story[name]["notes"]["2"])
		g.answer(d, 0)
		# Doc 3
		d = lib.get_doc(2)
		g.begin_doc(d, engine)
		_expect(narr.rumour_doc3(g) == story[name]["rumour"], name + " rumour: " + narr.rumour_doc3(g))
		_expect(not g.make_copy(d, engine, ["R4", "R3"]).shelved, name + " doc3 rejects wrong order")
		_expect(g.make_copy(d, engine, ["R3", "R4"]).shelved, name + " doc3 shelved")
		g.answer(d, 0)
		# Doc 4
		d = lib.get_doc(3)
		g.begin_doc(d, engine)
		_expect("R6" in g.cards, name + " inherited damak")
		_expect(g.prove_rule(d, lib, engine, "-s", "∅", ["rīgos:rīgo", "ēgros:ēgro"]).ok, name + " prove -s")
		_expect(g.prove_rule(d, lib, engine, "-m", "∅", ["nēkom:nēko", "Mīrom:Mīro"]).ok, name + " prove -m")
		r = g.make_copy(d, engine, ["R5", "R6"], [3, 4, 1, 2, 5] if careful else [])
		_expect(r.shelved and r.copy == story[name]["copy4"], name + " doc4 copy: " + r.copy)
		if careful:
			g.add_note(d, story[name]["notes"]["4"])
		g.answer(d, 0 if careful else 2)
		_expect(narr.epilogue(g) == story[name]["epilogue"], name + " epilogue matches prototype")
		# Save round-trip
		var path := "user://test_save.json"
		g.save(path)
		var g2 := GameState.load_or_new(path)
		_expect(narr.epilogue(g2) == narr.epilogue(g), name + " save/load keeps the story")
