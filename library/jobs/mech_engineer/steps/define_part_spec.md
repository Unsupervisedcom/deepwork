# Define Part Specification

## Objective

Capture everything a designer or fabricator needs to know about a custom part before choosing how to manufacture it.

## Task

Ask structured questions to understand the part's function, load conditions, interface geometry, and constraints, then produce a structured specification document.

### Process

1. **Gather inputs** — Ask structured questions using the AskUserQuestion tool. Cover:
   - Primary function of the part
   - Forces and moments the part must withstand (direction, magnitude, dynamic vs. static)
   - Temperature range and environmental exposure
   - Mating interfaces: fastener patterns, press-fit features, toleranced bores or shafts
   - Overall dimensional envelope (max length, width, height)
   - Preferred or required materials (or exclusions)
   - Whether an existing model file (STL, STEP, DXF) already exists

2. **Define acceptance criteria** — For each functional requirement, write a measurable pass/fail condition (e.g., "must not yield under 50 N axial load at 80 °C").

3. **Save output** to `.deepwork/tmp/part_spec.md`.

## Output Format

### .deepwork/tmp/part_spec.md

```markdown
# Part Specification: [part_name]

- **Part name**: [part_name]
- **Parent assembly**: [assembly name or "standalone"]
- **Date**: [ISO 8601 date]

## Function

[One-paragraph description of what this part does.]

## Functional Requirements

| ID  | Requirement                              | Acceptance Criterion                     |
|-----|------------------------------------------|------------------------------------------|
| FR1 | [e.g., Transmit motor torque to shaft]   | [e.g., No slip under 0.5 N·m at 3000 RPM] |

## Interface Geometry

- **Mating features**: [fastener holes, press-fit bore, rail slot, snap latch, etc.]
- **Critical dimensions**: [list with values]
- **Reference coordinate system**: [describe origin and axes if relevant]

## Load Conditions

| Load type   | Magnitude       | Direction      | Nature          |
|-------------|-----------------|----------------|-----------------|
| [e.g., Axial] | [e.g., 200 N] | [e.g., +Z]     | [Static / cyclic] |

## Environmental Conditions

- **Temperature range**: [min to max °C]
- **Exposure**: [UV, moisture, chemicals, food contact, etc.]

## Material Constraints

- Preferred: [material or family]
- Excluded: [anything to avoid]

## Existing Model

- [ ] No model exists — must be created
- [ ] Model exists at: `[path/to/file.stl or .step]`

## Open Questions

- [Any unclear requirements to resolve before manufacturing method selection]
```

