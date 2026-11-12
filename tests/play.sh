#!/bin/bash
# Playtest helper: append actions to a session, replay from the start, show the screen.
#   tests/play.sh SESSION_DIR ["click 640 360" "drag 100 600 400 650" ...]
# With no actions it only shows the current screen. "undo" drops the last action.
# Output: SESSION_DIR/screen.png (look at it) and the on-screen texts printed below.
set -e
S="$1"; shift || true
mkdir -p "$S"
touch "$S/actions.txt"
for a in "$@"; do
  if [ "$a" = "undo" ]; then sed -i '$ d' "$S/actions.txt"; else echo "$a" >> "$S/actions.txt"; fi
done
G=${GODOT:-/tmp/godotdl/Godot_v4.7.2-stable_linux.x86_64}
cd "$(dirname "$0")/.."
rm -f "$S/screen.png"
for try in 1 2 3; do
  ACTIONS="$S/actions.txt" OUT="$S/screen" timeout 600 xvfb-run -a -n $((100 + RANDOM % 800)) -s "-screen 0 1280x720x24" \
    "$G" --rendering-driver opengl3 --resolution 1280x720 --script res://tests/play_cli.gd > "$S/log.txt" 2>&1 || true
  [ -f "$S/screen.png" ] && break
  sleep $((RANDOM % 4 + 1))
done
if grep -q "SCRIPT ERROR" "$S/log.txt"; then echo "!! GAME ERROR:"; grep -A2 -m3 "SCRIPT ERROR" "$S/log.txt"; fi
echo "actions so far: $(grep -cv '^\s*$' "$S/actions.txt")"
echo "--- texts on screen (x,y wxh) ---"
cat "$S/screen.txt"
echo "--- screenshot: $S/screen.png"
