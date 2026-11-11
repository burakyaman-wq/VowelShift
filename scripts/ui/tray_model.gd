class_name TrayModel
extends RefCounted
## Which rule tile lies in which tray slot. The desk applies the rules in slot
## order, left to right; empty slots are skipped.

var slots: Array[String] = []


func _init(n: int = 5) -> void:
	slots.resize(n)
	slots.fill("")


func slot_of(rule_id: String) -> int:
	return slots.find(rule_id)


## Put a rule into a slot. A tile moved from another slot swaps places with
## whatever was there. A tile brought in from the desk pushes the occupant
## out; that rule id is returned so the desk can put its tile back.
func place(rule_id: String, slot: int) -> String:
	if slot < 0 or slot >= slots.size():
		return ""
	var from := slot_of(rule_id)
	if from == slot:
		return ""
	var occupant := slots[slot]
	slots[slot] = rule_id
	if from >= 0:
		slots[from] = occupant
		return ""
	return occupant


func remove(rule_id: String) -> void:
	var i := slot_of(rule_id)
	if i >= 0:
		slots[i] = ""


func order() -> Array[String]:
	var out: Array[String] = []
	for r in slots:
		if r != "":
			out.append(r)
	return out
