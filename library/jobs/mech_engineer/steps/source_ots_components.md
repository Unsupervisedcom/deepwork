# Source Off-the-Shelf Components

## Objective

Identify purchasable standard components that satisfy assembly sub-functions, minimizing the number of custom-fabricated parts.

## Task

Read the assembly requirements, decompose the assembly into sub-functions, and evaluate whether each sub-function can be addressed with an off-the-shelf component before designing anything custom.

### Process

1. **Decompose into sub-functions** — Break the assembly into atomic functions (e.g., "transmit torque," "provide linear travel," "mount to rail," "protect electronics from moisture").

2. **Match OTS candidates** — For each sub-function, search for standard components:
   - Fasteners, inserts, standoffs
   - Linear rails, bearings, bushings
   - Motors, actuators, sensors
   - Extrusion profiles (e.g., 2020 aluminum)
   - Electronic modules, connectors
   - Standard enclosures or panels
   Search common suppliers: McMaster-Carr, Misumi, Digi-Key, Mouser, Amazon, AliExpress.

3. **Make vs. buy decision** — For each sub-function:
   - If an OTS part satisfies the requirement at acceptable cost and lead time → record it
   - If no suitable OTS part exists → flag as "requires custom design" for the next step

4. **Record findings** — Save to `.deepwork/tmp/ots_components.md` (and to the project's `mech_design/` directory as described in the job context).

## Output Format

### .deepwork/tmp/ots_components.md

```markdown
# OTS Components: [project_name]

## Sub-Function Decomposition

| Sub-function             | Approach         | Rationale                              |
|--------------------------|------------------|----------------------------------------|
| [e.g., Mount to 20mm rail] | OTS            | Standard T-nut fits requirement        |
| [e.g., Custom bracket]   | Custom design    | No standard part matches envelope      |

## Off-the-Shelf Components

| # | Sub-function       | Part name          | Supplier     | Part number | Unit cost | Qty | Lead time |
|---|--------------------|--------------------|--------------|-------------|-----------|-----|-----------|
| 1 | [sub-function]     | [e.g., M3×8 SHCS]  | McMaster     | 92196A112   | $0.04     | 20  | 1–3 days  |
| 2 | ...                | ...                | ...          | ...         | ...       | ... | ...       |

## Flagged for Custom Design

- **[sub-function]** — [Reason no OTS option was found or suitable]
- ...
```

