# Sound design

## Objective

Select samples and design sounds using VSTs for every major role in the track. Document all decisions so the arrangement and mix steps have a clear sonic palette to work with.

## Task

Read the project brief, then methodically assign a sound source to every major role the track needs, documenting VST choice, patch settings, and the reasoning behind each decision.

### Process

1. **Read project brief** — Load `music/[track_name]/project_brief.md`. Extract genre, style, BPM/key, DAW, and reference tracks.

2. **Identify sound roles** — List every sound role the track requires based on the genre. For dark techno the list typically includes: kick, sub bass, percussion layer, pad/texture, lead/melodic, FX/transition, and atmospheric. Adapt as needed.

3. **Confirm VST availability** — Before assigning any VST, ask structured questions to verify which plugins are actually installed. Do not assign a VST the user doesn't have. Offer free/built-in alternatives (e.g., Vital, Surge, Dexed, DAW stock synths) when a named plugin isn't available.

4. **Assign sound sources** — For each role, choose one of:
   - A specific VST preset (note plugin name and preset)
   - A sample file (note sample pack and filename if known)
   - A synthesis patch to be built (note synth type and key parameters)

5. **Document lead MIDI motif** — For any melodic lead sound (vocoder, synth lead, hook), document a specific 2–4 bar MIDI note sequence. Even a sketch (e.g., "F2 – G2 – Ab2 – C3, repeated") is enough for the arrange step to work with. Do not leave the lead motif open-ended.

6. **Reference tracks check** — For each reference track in the project brief, identify which sound role it informs and note the connection explicitly.

5. **Document stems** — Note which sounds will be bounced to `music/[track_name]/stems/` as `.wav` files and their approximate format (e.g., 24-bit 44.1 kHz).

7. **Write `sound_design_notes.md`**.

## Output format

### sound_design_notes.md

**Path**: `music/[track_name]/sound_design_notes.md`

```markdown
# Sound design — [track_name]

## Sound palette

| Role | Source (VST / sample) | Patch / settings | Notes |
|------|----------------------|------------------|-------|
| Kick | [Plugin or sample] | [Preset or key params] | [Rationale, inspired by ref track if applicable] |
| Sub bass | ... | ... | ... |
| Percussion layer | ... | ... | ... |
| Pad / texture | ... | ... | ... |
| Lead / melodic | ... | ... | ... |
| FX / transition | ... | ... | ... |
| Atmospheric | ... | ... | ... |

## Reference track connections

| Reference | Sound role informed | Specific element to capture |
|-----------|--------------------|-----------------------------|
| Artist - Title | Kick | [e.g., punchy transient with minimal tail] |

## Stems to bounce

| Filename | Source | Format |
|----------|--------|--------|
| stems/kick.wav | [plugin/sample] | 24-bit 44.1 kHz |
| stems/bass.wav | ... | ... |

## VST notes

[Any VST-specific setup, routing, or MIDI notes relevant to this session.]
```

## Quality criteria

- Every major sound role has an assigned VST or sample with patch or settings notes.
- The sound palette is appropriate for the genre and style from the project brief.
- At least one note per reference track connects it to a specific sound decision.
- The stems table lists all sounds that will be bounced, with filenames under `music/[track_name]/stems/`.
- Any melodic lead has a specific 2–4 bar MIDI note sequence documented.
- Only VSTs confirmed as installed are assigned; free/built-in alternatives are noted where applicable.

## Context

Be precise. Vague entries like "some pad" make the mix step harder — prefer specifics like "Serum wavetable pad, Castlevania preset, cutoff at 40%, heavy reverb send."
