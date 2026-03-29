# Select and Document OTS Part

## Objective

Choose the best option from the researched candidates and produce a selection record ready for BOM inclusion or purchase order.

## Task

Read the requirements and options documents, apply selection criteria, choose one part, and justify the decision.

### Process

1. **Apply a weighted decision** — Score candidates against:
   - Requirements compliance (pass/fail gate — any failure disqualifies)
   - Unit cost vs. target
   - Lead time vs. project schedule
   - Availability (in stock vs. lead time vs. MOQ risk)
   - Supplier reliability (established distributor preferred over marketplace sellers for structural parts)

2. **Select the best candidate** — Choose the option with the best overall profile. If two candidates are close, prefer the one with lower risk (shorter lead time, established supplier, in-stock).

3. **Write integration notes** — Describe how the selected part installs into the assembly: fastener pattern, adhesive, press fit, clearance hole size, torque spec, wiring, etc.

4. **Save output** to `.deepwork/tmp/ots_selection.md`.

## Output Format

### .deepwork/tmp/ots_selection.md

```markdown
# OTS Part Selection: [part_function]

**Date**: [ISO 8601 date]
**Selected part**: [Part name]
**Supplier**: [Name]
**Part number**: [number or URL]

## Selection Justification

[2–4 sentences explaining why this part was chosen over the alternatives. Reference cost, lead time, compliance, or supplier reliability as appropriate.]

## Rejected Alternatives

| Option         | Reason rejected                              |
|----------------|----------------------------------------------|
| [Option 2 name]| [e.g., Lead time 6 weeks exceeds schedule]   |
| [Option 3 name]| [e.g., Unit cost 3× target at required MOQ]  |

## BOM Entry

| Field         | Value                                        |
|---------------|----------------------------------------------|
| Part name     | [descriptive name]                           |
| Part number   | [supplier part number]                       |
| Supplier      | [supplier name]                              |
| Unit cost     | $[price]                                     |
| MOQ           | [quantity]                                   |
| Lead time     | [days/weeks]                                 |
| Qty per assy  | [quantity needed in assembly]                |

## Integration Notes

- **Installation method**: [press fit / bolted / soldered / clipped / adhesive]
- **Mating feature**: [clearance hole Ø[X] mm / slot / pad size / etc.]
- **Torque spec**: [N·m if bolted]
- **Additional parts needed**: [e.g., "M3×6 SHCS × 2 to mount"]
- **Datasheet**: [link if applicable]
```

## Quality Criteria

- The chosen part is preferred over alternatives with clear reasoning.
- Output contains all fields needed to add the part to a BOM.
- Notes on how to integrate the part into the assembly are included.

## Context

This is the final output of the `source_ots_parts` workflow. The BOM Entry table is designed to drop directly into a BOM. Integration notes prevent assembly errors downstream.
