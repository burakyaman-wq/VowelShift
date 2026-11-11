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
	var lib := ManuscriptLibrary.new()
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

	# Pairing: affixes follow the old word, and a pair names the changes it shows.
	_expect(Pairing.match_affix("ghewom", "khewos") == "khewom", "the new word takes the old word's ending")
	var st := GameState.new()
	var d1 := lib.get_doc(0)
	var good := Pairing.make(d1, lib, engine, st, "ghrebheti", "khrepheti")
	_expect(good["ok"] and good["subs"].size() == 2, "ghrebheti → khrepheti shows two changes (gh, bh)")
	_expect(not Pairing.make(d1, lib, engine, st, "Meiros", "khewos")["ok"], "unrelated words do not pair")
	var marks: Array = Pairing.diff_marks("ghewom", "khewom")
	_expect(marks[0][0] == 1 and marks[0][1] == 0 and marks[1][0] == 1, "only the changed letter is marked")

	# Document 1 from the first click to the answer.
	var desk1: Node = load("res://scenes/desk.tscn").instantiate()
	root.add_child(desk1)
	_expect(desk1.tiles.is_empty(), "doc 1 starts with no tiles")
	_expect(desk1.tutor.step_text().contains("belgede bir kelimeye"), "the master's note starts by pointing at the document")
	desk1._on_pick("ghewom", "old", Label.new())
	_expect(desk1.tutor.step_text().contains("sözlükte"), "after a word is picked it points at the dictionary")
	desk1._pick = {}
	_expect(not desk1.try_pair("Meiros", "khewos")["ok"] and desk1.tutor.feedback_text().contains("aynı kelime değil"), "a bad pair is explained")
	desk1.try_pair("ghewom", "khewos")
	_expect(desk1.tutor.feedback_text().contains("gh → kh") and desk1.tutor.step_text().contains("ikinci bir eşleşme"), "one pair shows the change and asks for a second")
	desk1.try_pair("ghrebheti", "khrepheti")
	_expect(desk1.tiles.has("R1") and desk1.state.proven["R1"] == [2], "two pairs with gh → kh ink that line on a new R1 tile")
	_expect(desk1.tutor.feedback_text().contains("Kanıtlandı") and desk1.tutor.step_text().contains("tepsiye sürükle"), "a proven rule is announced and the note asks for the tray")
	desk1.try_pair("bhāgom", "phāgos")
	_expect(desk1.state.proven["R1"].has(0), "bhāgom and ghrebheti prove bh → ph")
	desk1.try_pair("Meiros", "Mīros")
	desk1.try_pair("deiwosyo", "dīwos")
	_expect(desk1.tiles.has("R2") and desk1.state.proven["R2"] == [0], "Meiros and deiwosyo prove ei → ī")
	_expect(not desk1.try_pair("nākos", "khewos")["ok"], "a bad pair is refused")
	desk1.place_rule("R1", 0)
	desk1.place_rule("R2", 1)
	_expect(desk1.tutor.step_text().contains("Kalemi tıkla"), "with every word right the note points at the pen")
	var w1: Dictionary = desk1.write_copy()
	_expect(desk1.tutor.step_text().contains("soruyu"), "after shelving it points at the question")
	_expect(w1["shelved"] and w1["copy"] == "Mīros dīwosyo khewom dōneti. Mīros phāgom khrepheti. Mēros nākos.", "doc 1 is copied right and shelved")
	_expect(desk1.answer_question(0), "the answer is sealed")
	_expect(desk1.state.answers.get("1", "") == "Büyük kardeş Mīros", "the answer is kept")
	desk1.next_document()
	_expect(desk1.doc.order == 2 and desk1.tiles.has("R1"), "doc 2 arrives and the tiles stay on the desk")
	desk1.queue_free()

	# Document 2 with every era-2 rule handed over: order changes the copy.
	var desk: Node = load("res://scenes/desk.tscn").instantiate()
	desk.doc_order = 2
	desk.dev_cards = true
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
	desk.open_reading()
	_expect(desk.reading_word_count() == 5, "the reading view shows the five words of doc 2")
	desk.close_reading()
	desk.place_rule("R4", 2)
	var res: Dictionary = desk.write_copy()
	_expect(res.get("shelved", false) and res["copy"] == "Mīros Mīrom ageti. Mīros nēkos.", "the pen writes and shelves the right copy")
	_expect(desk.state.phase == "answer", "a shelved copy moves on to the question")
	_expect(desk.tiles["R3"].locked, "tiles are put away once the copy is shelved")
	_expect(desk.write_copy().is_empty(), "nothing more is written after shelving")
	_expect(not desk.move_word(0, 1), "words stay where they are in a document that does not let them move")
	_expect(not desk.add_note("  "), "an empty margin note is not kept")
	_expect(desk.add_note("nēkos: sürgün, ölü değil") and desk.state.notes.get("2", "") == "nēkos: sürgün, ölü değil", "a margin note is kept with the shelved copy")
	_expect(desk.answer_question(0), "doc 2 is answered")
	desk.next_document()
	_expect(desk.doc.order == 3 and desk.interlude_text().contains("Sarayda senin kopyanı okudular"), "doc 3 opens on what the palace made of the copy")
	_expect(not desk.get_node("Belge").visible, "the new document waits behind the page")
	desk.dismiss_interlude()
	_expect(desk.get_node("Belge").visible and desk.get_node_or_null("Ara") == null or desk.get_node("Ara").is_queued_for_deletion(), "a click puts the page away and the document arrives")
	desk.queue_free()

	var desk3: Node = load("res://scenes/desk.tscn").instantiate()
	desk3.doc_order = 3
	desk3.dev_cards = true
	root.add_child(desk3)
	desk3.place_rule("R4", 0)
	desk3.place_rule("R3", 1)
	var bad: Dictionary = desk3.write_copy()
	_expect(not bad["shelved"] and "grīnom" in bad["rejected"], "wrong order in doc 3: grīnom is scraped")
	_expect(desk3.state.phase == "read", "a scraped copy can be written again")
	desk3.place_rule("R3", 0)
	var good3: Dictionary = desk3.write_copy()
	_expect(good3["shelved"] and good3["copy"] == "Mētīros Mīrosyo grēnom emeti.", "the right order shelves doc 3")
	desk3.queue_free()

	# Document 4: the endings have worn off, so the order of the words now says who did it.
	var desk4: Node = load("res://scenes/desk.tscn").instantiate()
	desk4.doc_order = 4
	desk4.dev_cards = true
	root.add_child(desk4)
	_expect(desk4.interlude_text().contains("Önce gelen yapandır"), "doc 4 opens on the master's note about word order")
	desk4.dismiss_interlude()
	desk4.place_rule("R5", 0)
	desk4.place_rule("R6", 1)
	_expect(desk4.copy_text() == "Mīro nēko Mīro rīgo şeneti.", "doc 4 copies word for word at first")
	var loose := desk4.get_node("Kopya/Fisler").get_children().filter(func(c: Node) -> bool: return c is WordSlip)
	_expect(loose.size() == 5, "the draft lies on five loose slips")
	_expect(desk4.move_word(2, 0) and desk4.move_word(3, 1), "two words are carried to the front")
	_expect(desk4.copy_text() == "Mīro rīgo Mīro nēko şeneti.", "the draft reads in the new order")
	_expect(not desk4.move_word(0, 9), "a word cannot be carried off the line")
	var slips: Node = desk4.get_node("Kopya/Fisler")
	var first: WordSlip = slips.get_child(0)
	first.position += Vector2(2000, 1000)
	desk4._on_slip_dropped(first)
	_expect(desk4.copy_text() == "rīgo Mīro nēko şeneti Mīro.", "a slip dropped past all the others goes to the end")
	desk4.move_word(4, 0)
	_expect(desk4.copy_text() == "Mīro rīgo Mīro nēko şeneti.", "and can be carried back")
	var res4: Dictionary = desk4.write_copy()
	_expect(res4.get("shelved", false) and res4["copy"] == "Mīro rīgo Mīro nēko şeneti.", "the reordered copy is written and shelved")
	_expect(desk4.narrative.city_reading_doc4(desk4.state) == desk4.narrative.t["doc4"]["subject_first"], "the city reads the first noun as the doer")
	_expect(desk4.get_node("Kopya/Fisler").get_child_count() == 0, "the slips are gone once the copy is in ink")
	_expect(desk4.add_note("Sırayı ben değiştirdim; anlam aynı."), "the scribe can say why in the margin")
	_expect(desk4.narrative.epilogue(desk4.state).contains("çevirmenlikle"), "and the epilogue remembers the note")
	desk4.queue_free()


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
