# Define Assembly Requirements

## Objective

Translate the user's project inputs into a structured requirements document that drives all subsequent design decisions in the assembly workflow.

## Task

Ask structured questions to gather the project name, design goal, and target quantity from the user, then produce a requirements document with functional specs, physical constraints, and a mapped scale tier.

### Process

1. **Gather inputs** — Ask structured questions using the AskUserQuestion tool. Cover:
   - What the assembly must do (primary function, environment, loads)
   - Physical constraints (size envelope, weight limit, mounting or interface requirements)
   - Target production quantity and timeline
   - Any materials to avoid or prefer
   - Known integration requirements (mating hardware, standards to comply with)

2. **Map quantity to scale tier** — Using the Scale Tiers table from the job context, map the target quantity to the appropriate tier name and record it.

3. **Write requirements.md** — Structure findings into functional requirements, constraints, and acceptance criteria. Save to `.deepwork/tmp/assembly_requirements.md` (and to the project's `mech_design/` directory as described in the job context).

## Output Format

### .deepwork/tmp/assembly_requirements.md

```markdown
# Assembly Requirements: [project_name]

## Project Overview
- **Project name**: [project_name]
- **Design goal**: [one-sentence summary of what the assembly must do]
- **Target quantity**: [number] → Scale tier: [Prototype / Small batch / Production]
- **Date**: [ISO 8601 date]

## Functional Requirements

| ID  | Requirement                                   | Acceptance Criterion                        |
|-----|-----------------------------------------------|---------------------------------------------|
| FR1 | [Function the assembly must perform]          | [Measurable pass/fail condition]            |
| FR2 | ...                                           | ...                                         |

## Physical Constraints

- **Envelope**: [max dimensions, e.g., 100 × 80 × 50 mm]
- **Weight limit**: [max mass if constrained]
- **Mounting interfaces**: [bolt pattern, rail size, snap fit, etc.]
- **Environment**: [temperature range, IP rating, UV exposure, etc.]
- **Material exclusions**: [anything to avoid, e.g., no food-contact plastics]

## Integration Requirements

- [List of external parts, standards, or systems the assembly must mate with]

## Open Questions

- [List any unresolved items that need clarification before proceeding]
```

## Quality Criteria

- Every function the assembly must perform is listed with a measurable acceptance criterion.
- Size envelope, weight limits, mounting interfaces, and environmental conditions are documented.
- Target production quantity is recorded and mapped to a scale tier.

## Context

This document is the single source of truth for all downstream steps. `source_ots_components` uses it to decide which sub-functions can be bought rather than built. `design_custom_parts` uses it to size and specify each custom part. `evaluate_manufacturability` uses it to determine appropriate manufacturing methods for the target scale.
