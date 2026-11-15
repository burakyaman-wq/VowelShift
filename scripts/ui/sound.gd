extends Node
## Sounds of the desk (autoload "Ses"): short effects and a quiet room loop.
## Muting is remembered between runs; M toggles it anywhere.

const FILES := ["kart", "kart_al", "kalem", "kalem_kisa", "muhur", "sayfa", "kagit", "hata", "can"]
const SETTINGS := "user://ses.json"
var muted := false
var _streams := {}
var _players: Array[AudioStreamPlayer] = []
var _room: AudioStreamPlayer


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for f in FILES:
		var s = load("res://assets/audio/%s.ogg" % f)
		if s:
			_streams[f] = s
	for i in 6:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)
	_room = AudioStreamPlayer.new()
	var room = load("res://assets/audio/oda.ogg")
	if room:
		room.loop = true
		_room.stream = room
		_room.volume_db = -10.0
	add_child(_room)
	var f := FileAccess.open(SETTINGS, FileAccess.READ)
	if f:
		var d = JSON.parse_string(f.get_as_text())
		muted = d is Dictionary and d.get("muted", false)
	_apply()


func play(name: String, volume_db: float = 0.0) -> void:
	if muted or not _streams.has(name) or DisplayServer.get_name() == "headless":
		return
	for p in _players:
		if not p.playing:
			p.stream = _streams[name]
			p.volume_db = volume_db
			p.pitch_scale = randf_range(0.94, 1.06)
			p.play()
			return


func room(on: bool) -> void:
	if on and not muted and _room.stream and not _room.playing and DisplayServer.get_name() != "headless":
		_room.play()
	elif not on:
		_room.stop()


func toggle() -> void:
	muted = not muted
	_apply()
	var f := FileAccess.open(SETTINGS, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify({"muted": muted}))


func _apply() -> void:
	AudioServer.set_bus_mute(0, muted)
	if not muted:
		room(true)


func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventKey and e.pressed and not e.echo and e.keycode == KEY_M:
		toggle()
