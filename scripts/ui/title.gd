extends Control
## The title page: start a new run or pick up the saved one.

const FONT := preload("res://assets/fonts/Katip-Regular.ttf")
const GAME := "res://scenes/oyun.tscn"
const INK := Color("2a1b14")
const RED := Color("b33a29")


func _ready() -> void:
	Loc.load_choice()
	var bg := TextureRect.new()
	bg.texture = Art.tex("masa.png", 1)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	add_child(bg)
	var sheet := TextureRect.new()
	sheet.texture = Art.tex("belge_okuma.png", 1)
	sheet.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	sheet.stretch_mode = TextureRect.STRETCH_SCALE
	add_child(sheet)
	sheet.position = Vector2(420, 150)
	sheet.size = Vector2(1080, 700)
	_text(Loc.t("Ses Kayması"), 92, RED, Vector2(460, 250), 1000)
	_text(Loc.t("Bir şehrin yalanı, üç kâtibin elinde"), 30, INK, Vector2(460, 380), 1000)
	var y := 470.0
	var saved := FileAccess.file_exists(GameState.SAVE_PATH)
	if saved:
		var st := GameState.load_or_new()
		var lib := ManuscriptLibrary.new()
		var at := mini(st.doc_index + 1, lib.docs.size())
		_button(Loc.t("Devam et  ·  iş %d / %d") % [at, lib.docs.size()], Vector2(460, y), _continue)
		y += 80
	_button(Loc.t("Yeni oyun"), Vector2(460, y), _new_game)
	var other := "English" if Loc.lang == "tr" else "Türkçe"
	var lang := _text("Türkçe · English", 26, RED, Vector2(560, 650), 380)
	lang.text = ("[ Türkçe ] · English" if Loc.lang == "tr" else "Türkçe · [ English ]")
	lang.mouse_filter = Control.MOUSE_FILTER_STOP
	lang.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	lang.tooltip_text = other
	lang.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			Loc.set_lang("en" if Loc.lang == "tr" else "tr")
			get_tree().reload_current_scene())
	var snd := get_node_or_null("/root/Ses")
	if snd:
		var sl := _text("", 26, RED, Vector2(980, 650), 380)
		sl.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		var show := func() -> void: sl.text = Loc.t("Ses: kapalı (M)") if snd.muted else Loc.t("Ses: açık (M)")
		show.call()
		sl.mouse_filter = Control.MOUSE_FILTER_STOP
		sl.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		sl.gui_input.connect(func(e: InputEvent) -> void:
			if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
				snd.toggle()
				show.call())
	_text(Loc.t("Çizimler kodla çizildi; tasarımda, kodda ve metinlerde yapay zekâ kullanıldı. Ayrıntılar oyunun sayfasında."), 18, Color(INK, 0.8), Vector2(460, 742), 1000)


func _text(t: String, size: int, color: Color, at: Vector2, width: float) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.position = at
	l.size = Vector2(width, size * 1.4)
	add_child(l)
	return l


func _button(t: String, at: Vector2, action: Callable) -> void:
	var l := _text(t, 40, INK, at, 1000)
	l.mouse_filter = Control.MOUSE_FILTER_STOP
	l.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	l.mouse_entered.connect(func() -> void: l.add_theme_color_override("font_color", RED))
	l.mouse_exited.connect(func() -> void: l.add_theme_color_override("font_color", INK))
	l.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			action.call())


func _continue() -> void:
	get_tree().change_scene_to_file(GAME)


func _new_game() -> void:
	if FileAccess.file_exists(GameState.SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(GameState.SAVE_PATH))
	get_tree().change_scene_to_file(GAME)
