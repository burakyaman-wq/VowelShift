class_name Art
extends RefCounted
## Which picture to draw with. Every era is painted by its own school
## (assets/art/STYLE.md). Second-era sprites carry the plain names the game
## started with; the others add _cagN. A sprite an era does not have falls
## back on the plain one.

const SPRITES := "res://assets/art/sprites/"
## The colour a tile's name is glazed in, by the era that made the tile.
const TILE_INK := {1: Color("5a2116"), 2: Color("1e3171"), 3: Color("2a3a61"), 4: Color("46669e")}
## Where a cast shadow falls, from the fourth era on.
const SHADOW_OFFSET := Vector2(7, 9)
const SHADOW := Color(0.12, 0.06, 0.04, 0.3)


static func tex(file: String, era: int = 2) -> Texture2D:
	var base := file.get_basename()
	if base == "masa":
		var plate := "%smasa_cag%d.png" % [SPRITES, era]
		return load(plate if ResourceLoader.exists(plate) else SPRITES + "masa_cag2.png")
	if era != 2:
		var own := "%s%s_cag%d.png" % [SPRITES, base, era]
		if ResourceLoader.exists(own):
			return load(own)
	return load(SPRITES + file)


## A document was written before the desk it lies on: it wears the school of
## the era before (the first era has nothing older to show).
static func document_era(desk_era: int) -> int:
	return maxi(1, desk_era - 1)


static func casts_shadow(era: int) -> bool:
	return era >= 4


## The shadow of a sprite: the same picture, dark, moved down and right.
static func shadow_of(texture: Texture2D, at: Vector2) -> TextureRect:
	var s := TextureRect.new()
	s.texture = texture
	s.position = at + SHADOW_OFFSET
	s.modulate = SHADOW
	s.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return s
