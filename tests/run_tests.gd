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

	# Copyist: the copy, the scales and the scribe cards, without the desk.
	var d2 := lib.get_doc(1)
	_expect(Copyist.hand(lib.get_doc(0), engine) == ["R1", "R2", "R3"], "doc 1 deals its era's two cards and one stranger")
	var ok2 := Copyist.evaluate(d2, engine, ["R3", "R4"], {}, {})
	_expect(ok2["copy"] == "Mīros Mīrom ageti. Mīros nēkos." and ok2["blocked"].is_empty(), "doc 2 in the right order")
	_expect(ok2["fidelity"] == 1 and ok2["clarity"] == 5, "three words fallen together and one the elders misread cost four fidelity")
	_expect(ok2["rows"][4]["elder"] == ["ölü"], "nēkos is what the elders read as 'dead'")
	var bad2 := Copyist.evaluate(d2, engine, ["R4", "R3"], {}, {})
	_expect(bad2["copy"].contains("nīkos") and bad2["fidelity"] == 0, "the wrong order says 'dead', and fidelity falls to nothing")
	var noted := Copyist.evaluate(d2, engine, ["R3", "R4"], {}, {"mēros": "not", "mērom": "eski"})
	_expect(noted["fidelity"] == 3 and noted["clarity"] == 4 and noted["copy"] == "Mīros Mērom ageti. Mīros nēkos.", "a note and an old spelling buy back fidelity; the old spelling costs clarity")
	var full2 := Copyist.evaluate(d2, engine, ["R3", "R4"], {}, {"mēros": "not", "mērom": "not", "mīros": "not", "nākos": "eski"})
	_expect(full2["fidelity"] == 5 and full2["clarity"] == 4, "three notes and an old spelling: the best doc 2 can be")
	var d4 := lib.get_doc(3)
	var lit4 := Copyist.evaluate(d4, engine, ["R5", "R6"], {}, {})
	_expect(lit4["order"] == "wrong" and lit4["fidelity"] == 3, "doc 4 copied word for word reads the wrong way round")
	var re4 := Copyist.evaluate(d4, engine, ["R5", "R6"], {}, {}, [3, 4, 1, 2, 5])
	_expect(re4["order"] == "unexplained" and re4["fidelity"] == 4, "reordered without a note costs one")
	var ok4 := Copyist.evaluate(d4, engine, ["R5", "R6"], {}, {"rīgos": "not"}, [3, 4, 1, 2, 5])
	_expect(ok4["order"] == "explained" and ok4["fidelity"] == 5 and Copyist.gloss(ok4).contains("sırayı"), "reordered with a note is whole, and the note says why")
	_expect(Copyist.gloss(noted) == "Mīros: kurucu kardeş (küçük)", "the note carries the old meaning")
	var scraped := Copyist.evaluate(d2, engine, ["R3", "R4"], {}, {"nākos": "kazi"})
	_expect(scraped["copy"] == "Mīros Mīrom ageti. Mīros.", "a scraped word leaves its sentence")
	var raw := Copyist.evaluate(lib.get_doc(0), engine, [], {}, {})
	_expect(raw["blocked"].size() == 5, "with no cards, five words of doc 1 are no words of the first era")
	_expect(raw["clarity"] == 0, "and today's reader can read nothing of it")

	# Document 1 on the desk: click a card, see the words change, write, deliver.
	var desk1: Node = load("res://scenes/desk.tscn").instantiate()
	root.add_child(desk1)
	_expect(desk1.tiles.size() == 3 and desk1.words.size() == 8, "doc 1: three sound cards in hand, eight word cards")
	_expect(desk1.tutor.step_text().contains("ses kartlarından birine tıkla"), "the note starts with the hand")
	desk1.tiles["R2"].clicked.emit(desk1.tiles["R2"])
	_expect(desk1.tray.model.order() == ["R2"], "a click puts a card in the strip")
	_expect(desk1.tutor.feedback_text().contains("2 kelimeyi değiştirdi"), "and says how many words it changed")
	desk1.tiles["R1"].clicked.emit(desk1.tiles["R1"])
	_expect(desk1.tray.model.order() == ["R2", "R1"], "a second click puts its card after the first")
	desk1.add_rule("R1")
	_expect(desk1.tutor.step_text().contains("sözlükte yok"), "words that are no words point at the other cards")
	desk1._on_tile_hovered(desk1.tiles["R1"], true)
	_expect(desk1.words["ghewom"]._ghost.text == "→ khewom", "hovering a card shows what it would do")
	desk1._on_tile_hovered(desk1.tiles["R1"], false)
	desk1.add_rule("R3")
	_expect(desk1.tutor.feedback_text().contains("başka bir anlam"), "the stranger card is caught by its meaning")
	desk1.add_rule("R3")
	_expect(not desk1.tray.model.order().has("R3"), "clicking a card in the strip takes it back")
	desk1._on_word_hovered(desk1.words["meiros"], true)
	_expect(desk1._book_right.get_child_count() > 2, "hovering a word opens the dictionary at it")
	desk1.add_rule("R1")
	_expect(desk1.tutor.step_text().contains("Kopya hazır"), "with every word right the note points at the pen")
	var w1: Dictionary = desk1.write_copy()
	_expect(w1["shelved"] and w1["copy"] == "Mīros dīwosyo khewom dōneti. Mīros phāgom khrepheti. Mēros nākos.", "doc 1 is copied right and shelved")
	_expect(desk1.state.scores["1"] == {"fidelity": 5, "clarity": 5}, "and weighed in full")
	_expect(desk1.tutor.step_text().contains("istek notuna tıkla"), "after shelving it points at the slip")
	_expect(desk1.tutor.step_text().contains("doğru, onu kullanmadın"), "and says which card was the stranger")
	_expect(desk1._page_words.size() > 16, "the copy is written on the document under the old text")
	_expect(desk1.deliver(), "the copy is delivered")
	desk1.next_document()
	_expect(desk1.doc.order == 2 and desk1.tiles.size() == 3 and desk1.tiles.has("R5"), "doc 2 deals R3, R4 and a stranger")
	desk1.dismiss_interlude()
	_expect(desk1.tutor.step_text().contains("Biri bu çağa ait değil"), "the note warns of the stranger")
	desk1.queue_free()

	# Document 2: order, collisions and the scribe cards.
	var desk: Node = load("res://scenes/desk.tscn").instantiate()
	desk.doc_order = 2
	root.add_child(desk)
	_expect(desk.interlude_text().contains("Elli yıl"), "doc 2 opens with the years that passed")
	desk.dismiss_interlude()
	desk.place_rule("R4", 0)
	desk.place_rule("R3", 1)
	_expect(desk.copy_text() == "Mīros Mīrom ageti. Mīros nīkos.", "R4 before R3 writes the trap")
	desk.place_rule("R3", 0)
	_expect(desk.copy_text() == "Mīros Mīrom ageti. Mīros nēkos.", "swapping the cards mends it")
	_expect(desk.tutor.step_text().contains("iki kelimenin biçimi"), "a word fallen into another's form is pointed out")
	_expect(desk.words["mēros"]._foot.text == "iki anlam", "and marked on its card")
	_expect(desk.mark_word("mēros", "not") and desk.evaluation()["fidelity"] == 2, "a margin note buys back fidelity")
	desk.unmark("mēros")
	_expect(desk.evaluation()["fidelity"] == 1, "taking the note off gives it back")
	desk.mark_word("mēros", "not")
	desk.mark_word("mīros", "not")
	desk.mark_word("mērom", "not")
	_expect(not desk.mark_word("nākos", "not") and desk.tools_left("not") == 0, "three notes, and no fourth")
	desk.open_reading()
	_expect(desk.reading_word_count() == 5, "the reading view shows the five words of doc 2")
	desk.close_reading()
	var res: Dictionary = desk.write_copy()
	_expect(res["shelved"] and desk.state.tools["not"] == 0, "writing spends the notes")
	_expect(desk.state.notes["2"].contains("kurucu kardeş (küçük)"), "the glosses become the copy's margin note")
	_expect(desk.state.phase == "answer" and desk.tiles["R3"].locked, "a shelved copy locks the strip")
	_expect(desk.write_copy().is_empty(), "nothing more is written after shelving")
	_expect(not desk.move_word(0, 1), "words stay where they are in a document that does not let them move")
	desk.deliver()
	desk.next_document()
	_expect(desk.doc.order == 3 and desk.interlude_text().contains("Sarayda senin kopyanı okudular"), "doc 3 opens on what the palace made of the copy")
	_expect(desk.interlude_text().contains("Belge 2 teslim edildi"), "and on how the delivered copy was weighed")
	_expect(not desk.get_node("Belge").visible, "the new document waits behind the page")
	_expect(desk.state.tools["not"] == 3 and desk.tools_left("not") == 3, "a fresh set of scribe cards comes with every document")
	desk.dismiss_interlude()
	_expect(desk.get_node("Belge").visible, "a click puts the page away and the document arrives")
	desk.place_rule("R4", 0)
	desk.place_rule("R3", 1)
	var bad3: Dictionary = desk.write_copy()
	_expect(not bad3["shelved"] and "grīnom" in bad3["blocked"], "wrong order in doc 3: grīnom is no word")
	_expect(desk.tutor.feedback_text().contains("Yazılamaz"), "and the pen says why")
	desk.place_rule("R3", 0)
	_expect(desk.write_copy()["shelved"], "the right order shelves doc 3")
	desk.queue_free()

	# Document 4: the endings have worn off, so the order of the words now says who did it.
	var desk4: Node = load("res://scenes/desk.tscn").instantiate()
	desk4.doc_order = 4
	root.add_child(desk4)
	_expect(desk4.interlude_text().contains("Önce gelen yapandır"), "doc 4 opens on the master's note about word order")
	desk4.dismiss_interlude()
	desk4.place_rule("R5", 0)
	desk4.place_rule("R6", 1)
	_expect(desk4.copy_text() == "Mīro nēko Mīro rīgo şeneti.", "doc 4 copies word for word at first")
	_expect(desk4.move_word(2, 0) and desk4.move_word(3, 1), "two words are carried to the front")
	_expect(desk4.copy_text() == "Mīro rīgo Mīro nēko şeneti.", "the copy reads in the new order")
	_expect(not desk4.move_word(0, 9), "a word cannot be carried off the line")
	var first: WordCard = desk4.words["kheneti"]
	first.position = Vector2(-50, -50)
	desk4._on_word_dropped(first)
	_expect(desk4.copy_text().begins_with("şeneti"), "a word card dropped first comes first")
	desk4._word_order = [3, 4, 1, 2, 5]
	desk4._refresh()
	var res4: Dictionary = desk4.write_copy()
	_expect(res4.get("shelved", false) and res4["copy"] == "Mīro rīgo Mīro nēko şeneti.", "the reordered copy is written and shelved")
	_expect(desk4.narrative.city_reading_doc4(desk4.state) == desk4.narrative.t["doc4"]["subject_first"], "the city reads the first noun as the doer")
	desk4.deliver()
	desk4.next_document()
	_expect(desk4.get_node_or_null("Son") != null, "after the last document the epilogue opens")
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
		var g_old := GameState.new()
		g_old.copies["2"] = "Mīros Mīrom ageti. Mīros nākos."
		_expect(narr.rumour_doc3(g_old).contains("sürgün edildiği konuşuluyor") and narr.epilogue(g_old).contains("hiç doğmadı"), name + " the old spelling keeps the rumour from being born")
		# Save round-trip
		var path := "user://test_save.json"
		g.save(path)
		var g2 := GameState.load_or_new(path)
		_expect(narr.epilogue(g2) == narr.epilogue(g), name + " save/load keeps the story")
