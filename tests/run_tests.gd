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

	print("%d checks, %d failures" % [checks, failures])
	quit(1 if failures > 0 else 0)


func _expect(ok: bool, msg: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		printerr("FAIL: " + msg)
