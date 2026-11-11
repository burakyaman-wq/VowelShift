#!/usr/bin/env bash
# Export the single-threaded web build and zip it for itch.io.
#   tools/web_build.sh            -> build/web/ and build/ses-kaymasi-web.zip
#   GODOT=/path/to/godot tools/web_build.sh
# Needs Godot 4.7.2 with the web_nothreads export templates installed.
set -euo pipefail
cd "$(dirname "$0")/.."
GODOT="${GODOT:-godot}"
rm -rf build/web && mkdir -p build/web
touch build/.gdignore
"$GODOT" --headless --import >/dev/null 2>&1 || true
"$GODOT" --headless --export-release "Web" build/web/index.html >/dev/null
rm -f build/ses-kaymasi-web.zip
(cd build/web && zip -q -9 ../ses-kaymasi-web.zip ./*)
ls -la build/web build/ses-kaymasi-web.zip
