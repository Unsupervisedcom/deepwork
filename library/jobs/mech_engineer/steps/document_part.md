# Document Part

## Objective

Produce a single-page part datasheet that a fabricator or procurement engineer can act on without needing any additional context.

## Task

Merge the part spec and manufacturing specification into a clean datasheet, verify completeness, and save it as the final deliverable for this part.

### Process

1. **Read both inputs** — `part_spec.md` and `manufacturing_spec.md`.

2. **Compose the datasheet** — Combine key fields:
   - Part identity (name, revision, date)
   - Function summary (one paragraph)
   - Critical dimensions and tolerances (table)
   - Manufacturing method and material (prototype and production)
   - DFM notes
   - Model/STL reference or creation instructions
   - Cost estimate

3. **Verify fabricator-readiness** — Ask: could a fabricator produce this part from the datasheet alone? If any critical dimension, tolerance, or material is missing, fill it in or flag it as an open question.

4. **Save output** to `.deepwork/tmp/part_datasheet.md` and `mech_design/{project_name}/parts/{part_name}/datasheet.md`.

## Output Format

### .deepwork/tmp/part_datasheet.md

```markdown
# Part Datasheet: [part_name]

**Revision**: 1.0
**Date**: [ISO 8601 date]
**Parent assembly**: [assembly name or "standalone"]

---

## Function

[One-paragraph description of what the part does.]

## Critical Dimensions

| Feature               | Nominal | Tolerance | Notes                    |
|-----------------------|---------|-----------|--------------------------|
| [e.g., Bore diameter] | 8.00 mm | ±0.05 mm  | Press fit — bearing ID   |
| [e.g., Overall length]| 45.0 mm | ±0.5 mm   | Non-critical             |

## Manufacturing

| Parameter         | Prototype              | Production                |
|-------------------|------------------------|---------------------------|
| Process           | [e.g., FDM 3D print]   | [e.g., Injection molding] |
| Material          | [e.g., PETG]           | [e.g., ABS-PC blend]      |
| Est. unit cost    | $[cost]                | $[cost]                   |
| Lead time         | [e.g., 2 hours]        | [e.g., 2 weeks + tooling] |

## DFM Notes

- [Key fabrication guidance for the chosen process]

## 3D Model

- **Status**: [Exists / To be created]
- **Source file**: `[path/to/source_file]` (toolchain-appropriate format per agent.md) or *needs modeling*
- **Build command**: `[command to generate STL from source]`

## Open Issues

- [Any unresolved items before fabrication can begin]
```

## Quality Criteria

- Datasheet includes all fields needed to order fabrication or add the part to a BOM.
- A model source file path (toolchain-appropriate format per agent.md) or model creation instructions are included.
- A fabricator could produce the part from this datasheet without additional information.

## Context

This is the final output of the `design_part` workflow. The datasheet can be attached to a purchase order, included in a BOM, or handed to a fabricator directly. Keep it concise — one page is the target. Move long derivations or analysis to appendices if needed.
