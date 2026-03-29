# Define OTS Part Requirements

## Objective

Capture a precise specification for an off-the-shelf part so that subsequent research can find candidates that actually satisfy the need.

## Task

Ask structured questions to understand what the OTS part must do, then produce a requirements document that research can execute against.

### Process

1. **Gather inputs** — Ask structured questions using the AskUserQuestion tool. Cover:
   - Primary function (what the part must do)
   - Key dimensional constraints (thread size, bore diameter, flange OD, length range, etc.)
   - Load and performance requirements (max force, current, speed, temperature)
   - Interface standard (e.g., ISO metric thread, NEMA 17 flange, DIN rail, M.2)
   - Target unit cost range
   - Minimum order quantity tolerance
   - Any compatibility requirements (e.g., "must fit 20×20 aluminum extrusion T-slot")

2. **Write requirements document** — Structure inputs into functional requirements and constraints.

3. **Save output** to `.deepwork/tmp/ots_requirements.md`.

## Output Format

### .deepwork/tmp/ots_requirements.md

```markdown
# OTS Part Requirements

- **Part function**: [What the part must do in one sentence]
- **Quantity needed**: [number], for: [project context]
- **Date**: [ISO 8601 date]

## Functional Requirements

| ID  | Requirement                                     | Acceptance Criterion                       |
|-----|-------------------------------------------------|--------------------------------------------|
| FR1 | [e.g., Transmit M3 screw torque into PETG part] | [e.g., Min. pull-out force 80 N in PETG]   |
| FR2 | ...                                             | ...                                        |

## Dimensional Constraints

- [Thread/bore/OD/ID/length range, flange diameter, mounting pattern, etc.]

## Performance Constraints

- [Max load, temperature rating, current, speed, etc.]

## Interface Standards

- [Metric thread class, DIN standard, NEMA frame, connector type, etc.]

## Cost and Sourcing

- **Target unit cost**: ≤ $[price]
- **Min order quantity**: ≤ [number]
- **Preferred suppliers**: [any preferences, or "no preference"]

## Compatibility Notes

- [What the part must mate with, fit inside, or mount to]
```

## Quality Criteria

- The part's required function is stated with enough detail to evaluate candidates against it.
- Key dimensional constraints are documented.
- Quantity needed and an acceptable unit cost range are recorded.

## Context

Precise requirements here prevent wasted time researching incompatible options. Over-constraining (specifying exact part numbers rather than requirements) limits the search; under-constraining leads to candidates that fail at integration. Strike the balance: specify the *need*, not the solution.
