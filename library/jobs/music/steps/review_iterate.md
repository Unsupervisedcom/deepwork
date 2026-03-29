# Review and iterate

## Objective

Critically evaluate the current state of the track against the project goals and reference tracks, then decide whether to finalize or loop back to an earlier step for revision.

## Task

Read all prior outputs, apply structured listening criteria, document findings, and make a clear loop decision: finalize or call `go_to_step` with the target step.

### Process

1. **Read all prior outputs** — Load:
   - `music/[track_name]/project_brief.md` (goals, genre, references)
   - `music/[track_name]/sound_design_notes.md` (intended sound palette)
   - `music/[track_name]/arrangement_notes.md` (intended structure)
   - `music/[track_name]/mix_notes.md` (intended mix decisions)

2. **Evaluate against goals** — Assess the track on these axes:
   - **Genre fit**: Does the track sound like the stated genre and style?
   - **Reference alignment**: Does it draw from the reference tracks in the ways noted in sound_design_notes?
   - **Energy arc**: Does the arrangement build and release tension as planned?
   - **Mix balance**: Do the documented level relationships hold? Is there any masking or muddiness?
   - **Sonic cohesion**: Do all sounds belong to the same sonic world?

3. **Identify the most critical issue** — Rank findings by severity. Only one thing is the most critical issue; fix it first.

4. **Make the loop decision** (see decision tree below).

5. **Write `iteration_notes.md`**.

### Loop decision tree

**If fundamentals are wrong** (sounds don't fit genre, palette incoherent, reference tracks not reflected):
Call `go_to_step` with `step_id: "sound_design"`. This resets progress from sound_design onward — sound_design, arrange, mix, and review_iterate will all re-execute with the revised sounds.

**If structure is wrong** (energy arc missing, sections too long/short, key moments not landing):
Call `go_to_step` with `step_id: "arrange"`. This resets progress from arrange onward — arrange, mix, and review_iterate will re-execute.

**If only mix balance is wrong** (levels, EQ, compression — sounds and structure are solid):
Call `go_to_step` with `step_id: "mix"`. This resets mix and review_iterate only.

**If the track meets the project goals**:
Proceed by calling `finished_step` with `iteration_notes.md` as the output.

**Maximum iterations**: Once the iteration cap is reached, proceed to finalize and document remaining issues under "Deferred items."

## Output format

### iteration_notes.md

**Path**: `music/[track_name]/iteration_notes.md`

```markdown
# Iteration notes — [track_name] — Review [N]

## Evaluation

| Axis | Rating (1–5) | Notes |
|------|-------------|-------|
| Genre fit | | |
| Reference alignment | | |
| Energy arc | | |
| Mix balance | | |
| Sonic cohesion | | |

## Strengths

- [What is working well]

## Issues found

| Issue | Severity (high/med/low) | Target step |
|-------|------------------------|-------------|
| [Issue description] | high | sound_design |
| [Issue description] | med | mix |

## Most critical issue

[One sentence: what is the single most important thing to fix.]

## Decision

**[Loop back to: sound_design / arrange / mix] OR [Finalize]**

Reason: [One sentence justifying the decision.]

### Changes required (if looping)

- [ ] [Specific change to make in the target step]
- [ ] [Specific change to make in the target step]

### Deferred items (if finalizing)

- [Any issues that will not be addressed in this session]
```

## Quality criteria

- A clear loop or finalize decision is documented.
- If looping back, specific changes are listed for the target step.
- The evaluation explicitly references the genre, style, and reference tracks from the project brief.
- The most critical issue is identified and is what drives the loop decision.

