# Arrange

## Objective

Define the full song structure by arranging the sounds from the sound design step into a timeline with named sections, clear energy arc, and automation notes.

## Task

Read the sound design notes and project brief, then design the song structure: section names, bar lengths, clip/scene layout, and key automation moments. Write the result to `arrangement_notes.md`.

### Process

1. **Read inputs** — Load `music/[track_name]/sound_design_notes.md` and `music/[track_name]/project_brief.md`. Note the sound palette, BPM, key, and genre.

2. **Define sections** — Decide on section names and lengths in bars. Typical electronic track sections:
   - Intro (8–16 bars): sparse, builds context
   - Build (8–16 bars): layers accumulate, tension rises
   - Drop / main (16–32 bars): full energy, core groove
   - Break (8–16 bars): tension release, re-strips elements
   - Second build / drop (16–32 bars): escalation or variation
   - Outro (8–16 bars): wind-down

   Adapt freely — not every track needs every section. Genre dictates conventions.

3. **Map sounds to sections** — For each section, note which sounds from the sound palette are active. Use a presence table (sound role vs. section, with ✓ for active).

4. **Define automation moments** — Note 3–5 key automation moves: filter opens, reverb swells, volume rides, FX send spikes. These carry emotional energy.

5. **DAW-specific notes** — Note section start times in bars and any named scenes or markers in the DAW of choice.

6. **Write `arrangement_notes.md`**.

## Output format

### arrangement_notes.md

**Path**: `music/[track_name]/arrangement_notes.md`

```markdown
# Arrangement — [track_name]

## Section map

| Section | Bars | Description |
|---------|------|-------------|
| Intro | 1–16 | [What's present, energy level] |
| Build | 17–32 | [What's added, tension driver] |
| Drop | 33–64 | [Full palette, groove note] |
| Break | 65–80 | [What's stripped, contrast element] |
| Outro | 81–96 | [Wind-down approach] |

## Sound presence per section

| Sound role | Intro | Build | Drop | Break | Outro |
|-----------|-------|-------|------|-------|-------|
| Kick | — | ✓ | ✓ | — | ✓ |
| Sub bass | ✓ | ✓ | ✓ | ✓ | — |
| ... | | | | | |

## Key automation moments

| Bar | Track | Parameter | Movement |
|-----|-------|-----------|----------|
| 24 | Pad | Filter cutoff | Sweeps open over 4 bars |
| 32 | FX send | Reverb return | Spikes at drop |

## DAW notes

[Ableton: scene names / Arrangement View bar markers. Ardour: region positions and markers.]
```

## Quality criteria

- All major sections are named and sequenced with bar markers.
- The arrangement shows a clear energy arc (build, peak, release).
- Every sound role from sound_design_notes.md appears in at least one section.
- At least 3 key automation moments are documented.

