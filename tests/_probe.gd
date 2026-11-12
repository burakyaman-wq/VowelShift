extends SceneTree
func _initialize():
	var engine := RuleEngine.new()
	var lib := ManuscriptLibrary.new()
	for i in lib.docs.size():
		var doc: Manuscript = lib.get_doc(i)
		var hand := Copyist.hand(doc, engine)
		var proven := {}
		for rid in hand: proven[rid] = range(engine.by_id[rid].sub_count())
		var order := []
		for rid in engine.era_ids(doc.era):
			if rid in hand: order.append(rid)
		var ev := Copyist.evaluate(doc, engine, order, proven, {})
		print("DOC ", doc.order, " era ", doc.era, " hand ", hand, " order ", order, " F", ev["fidelity"], " C", ev["clarity"], " ", ev["copy"])
		for r in ev["rows"]:
			var elder := Copyist.meanings(engine, r["new"], doc.era - 1)
			print("   ", r["old"], " -> ", r["new"], " was=", r["was"], " now=", r["now"], " elder=", elder, " col=", r["collision"], " sh=", r["shifted"])
	for r in engine.rules:
		print(r.id, " era", r.era, " ", r.name_tr)
	quit()
