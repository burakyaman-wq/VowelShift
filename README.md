# VowelShift — *Ses Kayması*

A puzzle game for **GitHub Game Off 2026** (theme: **SHIFT**), made with Godot.

You are a scribe in an Anatolian scriptorium. Centuries pass, the language drifts,
and the manuscripts on your desk stop making sense. Work out the sound changes,
put them in the right order, and read what the past is trying to say. Your
readings are copied forward, so your mistakes become the next century's
"old text".

## Design decisions

- **Setting:** an Anatolian / Eastern scriptorium — reed pen, ink, lamp light.
- **Script:** Latin letters in a decorative typeface; the puzzle is the sound changes, not the alphabet.
- **Errors persist:** the player's readings of key words carry into later eras.

## Project layout

```
scenes/            Godot scenes
scripts/core/      rule engine, game state
scripts/ui/        desk, rule cards, manuscript view
data/words/        proto-language lexicon (JSON)
data/rules/        sound-change rules per era (JSON)
data/manuscripts/  puzzles and requests (JSON)
assets/            art, fonts, audio, pictograms
tools/             Python helpers (lexicon, rule simulator)
tests/             GUT unit tests
```

## Running

Open `project.godot` in Godot 4.7+ (GL Compatibility renderer).
The **Web** export preset is single-threaded, so the build runs on itch.io
without SharedArrayBuffer settings.
