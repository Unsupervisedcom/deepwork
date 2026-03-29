# Mix

## Objective

Balance the levels of all sounds in the arrangement, apply EQ and compression to each element, and configure send/return effects and master bus processing.

## Task

Read the arrangement notes and project brief, then document all mix decisions: relative levels, EQ moves, compression settings, FX routing, and master bus chain. Write the result to `mix_notes.md`.

### Process

1. **Read inputs** — Load `music/[track_name]/arrangement_notes.md` and `music/[track_name]/project_brief.md`. Identify the full sound roster and the drop section as the primary mixing reference.

2. **Set relative levels** — Establish a rough level hierarchy for the drop section (where all elements are present). Typical starting point for dark techno/electronic:
   - Kick: reference level (0 dB VU or -18 dBFS)
   - Sub bass: sits just below kick energy
   - Percussion: 4–8 dB below kick
   - Pads: 10–14 dB below kick
   - Lead: 6–10 dB below kick
   - FX/atmospheres: background, sidechain ducking often applied

3. **Apply EQ** — Note 1–3 key EQ moves per element. Prioritize subtractive EQ (removing clashes) over additive. Document frequency and dB values.

4. **Apply compression** — Note compression settings for transient elements (kick, percussion) and sustain elements (pads, bass) separately. Document attack, release, ratio, threshold where relevant.

5. **Set up FX sends** — Document the send/return chain: reverb bus, delay bus, saturation parallel bus if used. Note send levels per element.

6. **Master bus** — Document the master bus processing chain (e.g., light glue compression, limiter, reference level target).

7. **Write `mix_notes.md`**.

## Output format

### mix_notes.md

**Path**: `music/[track_name]/mix_notes.md`

```markdown
# Mix notes — [track_name]

## Level hierarchy (drop section reference)

| Element | Relative level | Notes |
|---------|---------------|-------|
| Kick | 0 dB (reference) | |
| Sub bass | −3 dB | Sidechain from kick |
| Percussion layer | −8 dB | |
| Pad / texture | −12 dB | Heavy reverb send |
| Lead | −7 dB | |
| Atmospheric | −18 dB | Always-on background |

## EQ moves

| Element | Band | Frequency | Cut/Boost | Reason |
|---------|------|-----------|-----------|--------|
| Kick | HP | 30 Hz | Cut | Remove sub below sub bass |
| Sub bass | Notch | 250 Hz | −3 dB | Reduce mud |
| ... | | | | |

## Compression settings

| Element | Attack | Release | Ratio | Threshold | Notes |
|---------|--------|---------|-------|-----------|-------|
| Kick | 1 ms | 80 ms | 4:1 | −6 dBFS | Preserve transient |
| Sub bass | 20 ms | 200 ms | 3:1 | −12 dBFS | Tighten sustain |
| ... | | | | | |

## FX send / return chain

| Bus | Plugin | Settings | Who sends |
|-----|--------|----------|-----------|
| Reverb A | [Reverb plugin] | 2.4 s, dark | Pad, atmospheric |
| Delay | [Delay plugin] | 1/8 dotted, filtered | Lead |
| Parallel sat | [Saturation] | Light drive | Percussion, kick |

## Master bus

[Plugin chain in order, target loudness, limiter ceiling.]
```

## Quality criteria

- Relative levels for all major elements are documented.
- At least one EQ move per sound role.
- Compression settings are noted for at least kick and bass.
- Send/return FX chain is fully documented.
- Master bus processing chain is listed.

## Context

Mix notes serve two purposes: they document intent (so the review_iterate step can evaluate whether the mix matches the project goals) and they make the session resumable (another agent or human can re-create the mix decisions from this document). Be precise — "a bit of reverb" is not useful; "Valhalla Room, pre-delay 20 ms, size 60%, wet 25%" is.
