extends SceneTree
## Every visible piece of text on the desk, at every step of the slice:
## does it fit its box and its sheet, and does it sit on top of other text?
##   godot --headless --script res://tests/layout_audit.gd
## Prints one line per problem and a count; exits 1 if there are any.

var problems := PackedStringArray()


func _initialize() -> void:
	_go()


func _go() -> void:
	await process_frame
	for order in [1, 2, 3, 4]:
		var desk: Node = load("res://scenes/desk.tscn").instantiate()
		desk.doc_order = order
		desk.dev_cards = order > 1
		root.add_child(desk)
		await process_frame
		if desk.interlude_text() != "":
			await _check(desk, "belge %d ara sayfa" % order)
			desk.dismiss_interlude()
			await create_timer(0.6).timeout
		await _check(desk, "belge %d başta" % order)
		var cards: Array = Pairing.era_rules(desk.doc, desk.engine)
		if order == 2 or order == 3:
			cards = ["R3", "R4"]
		for i in cards.size():
			desk.place_rule(cards[i], i)
			await create_timer(0.4).timeout
			await _check(desk, "belge %d, %d kart" % [order, i + 1])
		if desk.doc.allow_reorder:
			desk.move_word(2, 0)
			desk.move_word(3, 1)
			await _check(desk, "belge %d sıralı" % order)
		desk.open_reading()
		await create_timer(0.3).timeout
		await _check(desk, "belge %d okuma" % order)
		desk.close_reading()
		desk.write_copy()
		await create_timer(4.0).timeout
		desk.add_note("Sırayı ben değiştirdim; anlam aynı.")
		await _check(desk, "belge %d soru" % order)
		desk.answer_question(0)
		if order == 4:
			desk.next_document()
			await create_timer(0.3).timeout
			await _check(desk, "son")
		desk.queue_free()
		await process_frame
	for p in problems:
		print(p)
	print("%d problems" % problems.size())
	quit(1 if problems.size() > 0 else 0)


func _check(desk: Node, when: String) -> void:
	await process_frame
	var texts: Array = []
	for n in desk.find_children("*", "Control", true, false):
		if not (n is Label or n is RichTextLabel or n is LineEdit) or not n.is_visible_in_tree():
			continue
		var t: String = n.text if not (n is RichTextLabel) else n.get_parsed_text()
		if t.strip_edges() == "" and not (n is LineEdit):
			continue
		var need := _content(n)
		var box: Rect2 = n.get_global_rect()
		var shown := Rect2(box.position, need)
		var tag := "[%s] %s «%s»" % [when, _path(desk, n), t.left(28).replace("\n", " ")]
		if n is Label and (n.clip_text or n.text_overrun_behavior != TextServer.OVERRUN_NO_TRIMMING) and need.x > box.size.x + 1:
			problems.append("%s kesiliyor (%d > %d)" % [tag, need.x, box.size.x])
		var sheet := _sheet(desk, n)
		if sheet:
			var r: Rect2 = sheet.get_global_rect().grow(-4)
			if not r.encloses(shown.grow(-2)):
				problems.append("%s kâğıttan taşıyor (%s)" % [tag, sheet.name])
		if not Rect2(Vector2.ZERO, Vector2(1920, 1080)).encloses(shown):
			problems.append("%s ekrandan taşıyor" % tag)
		var px := _font_px(n)
		if px > 0 and px < 16:
			problems.append("%s yazı çok küçük (%d px; 1280×720'de %d)" % [tag, px, roundi(px * 2.0 / 3.0)])
		texts.append([n, shown, tag])
	for i in texts.size():
		for j in range(i + 1, texts.size()):
			var a: Rect2 = texts[i][1].grow(-3)
			var b: Rect2 = texts[j][1].grow(-3)
			if a.intersects(b) and _layer(desk, texts[i][0]) == _layer(desk, texts[j][0]):
				problems.append("%s üstüne biniyor: %s" % [texts[i][2], texts[j][2]])


func _font_px(n: Control) -> int:
	if n is RichTextLabel:
		return n.get_theme_font_size("normal_font_size")
	return n.get_theme_font_size("font_size")


func _content(n: Control) -> Vector2:
	if n is RichTextLabel:
		return Vector2(maxf(n.get_content_width(), 1), maxf(n.get_content_height(), 1))
	if n is LineEdit:
		return n.size
	var l := n as Label
	var font: Font = l.get_theme_font("font")
	var fs: int = l.get_theme_font_size("font_size")
	if l.autowrap_mode != TextServer.AUTOWRAP_OFF:
		var h := l.get_line_count() * font.get_height(fs)
		return Vector2(l.size.x, h)
	var sz := font.get_multiline_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs)
	return sz


## The sheet of paper (or card, tray, note) a text is written on.
func _sheet(desk: Node, n: Node) -> Control:
	var p := n.get_parent()
	while p and p != desk:
		if p is Control and p.name in ["Belge", "Kopya", "Pusula", "Ara", "Son", "Okuma"]:
			return p
		if p is RuleTile or p is WordSlip:
			return p
		if p.get_parent() is Tutor:
			return p
		p = p.get_parent()
	return null


## Text on a page laid over the desk does not collide with the desk under it.
func _layer(desk: Node, n: Node) -> String:
	var p := n.get_parent()
	while p and p != desk:
		if p.name in ["Ara", "Son", "Okuma"]:
			return p.name
		p = p.get_parent()
	return "masa"


func _path(desk: Node, n: Node) -> String:
	return str(desk.get_path_to(n)).replace("@", "").left(48)
