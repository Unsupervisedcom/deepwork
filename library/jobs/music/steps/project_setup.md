# Project setup

## Objective

Initialize the track's project directory, configure git LFS for audio files, and write a concise project brief that all subsequent steps will use as their north star.

## Task

Ask structured questions to gather the four required inputs, then create the project directory, write the project brief, and configure git LFS.

### Process

1. **Gather inputs** — Ask structured questions using the AskUserQuestion tool to collect:
   - `track_name`: directory-safe name (e.g., `dark_wave_001`)
   - `genre_style`: genre, mood, and texture (e.g., "dark techno, industrial, hypnotic")
   - `reference_tracks`: 2–5 reference songs in "Artist - Title" format
   - `bpm_key`: target tempo and scale (e.g., "132 BPM, A minor")

2. **Choose DAW** — Ask the user which DAW they will use: Ableton Live or Ardour/open-source. Document the choice in the project brief and note any DAW-specific tooling (AbletonOSC, Ardour OSC port, etc.).

3. **Create project directory** — Create the directory `music/[track_name]/` and the `stems/` subdirectory inside it.

4. **Configure git LFS** — Write or update `.gitattributes` at the repository root with LFS tracking patterns for all audio file types. Run `git lfs install` if LFS is not already initialized.

5. **Write project brief** — Create `music/[track_name]/project_brief.md` with all inputs, DAW choice, and reference track notes.

## Output format

### project_brief.md

**Path**: `music/[track_name]/project_brief.md`

```markdown
# [Track name]

## Project inputs

| Field | Value |
|-------|-------|
| Genre / style | [genre_style] |
| BPM / key | [bpm_key] |
| DAW | [Ableton Live / Ardour / LMMS] |

## Reference tracks

| Track | Sonic inspiration |
|-------|-------------------|
| Artist - Title | [What element to draw from: texture, groove, energy, arrangement, etc.] |
| Artist - Title | ... |

## Goals

[2-3 sentences describing what a successful finished track sounds like.]
```

### .gitattributes

**Path**: `.gitattributes` (repository root)

```gitattributes
# Audio files — tracked via Git LFS
*.wav filter=lfs diff=lfs merge=lfs -text
*.aif filter=lfs diff=lfs merge=lfs -text
*.aiff filter=lfs diff=lfs merge=lfs -text
*.flac filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.ogg filter=lfs diff=lfs merge=lfs -text
```

If `.gitattributes` already exists, merge the new patterns — do not overwrite existing rules.

## Quality criteria

- All four user inputs (track name, genre/style, reference tracks, BPM/key) are documented.
- A specific DAW is chosen and noted.
- `.gitattributes` includes LFS patterns for all six audio extensions.
- The project directory `music/[track_name]/stems/` exists.
