# Generate Bill of Materials

## Objective

Compile every OTS component and custom part into a single structured BOM with quantities, unit costs, extended costs, suppliers, and lead times.

## Task

Read the OTS components list and custom parts plan, then produce a complete BOM. The BOM is the primary handoff artifact for procurement and fabrication.

### Process

1. **Merge inputs** — Pull every line item from `ots_components.md` (OTS parts) and `custom_parts_plan.md` (fabricated parts) into a single table.

2. **Fill in missing fields** — For any line missing cost or lead time, estimate based on:
   - OTS parts: supplier catalog pricing or online estimate
   - Custom parts: material cost + machining/printing time estimate at the target scale tier

3. **Calculate totals** — Compute extended cost (unit cost × quantity) for every line. Sum all extended costs for a total assembly cost.

4. **Note procurement paths** — For custom parts, note the fabrication method in the "Supplier" column (e.g., "FDM in-house," "CNC vendor").

5. **Save output** to `.deepwork/tmp/bom.md` (and to the project's `mech_design/` directory as described in the job context).

## Output Format

### .deepwork/tmp/bom.md

```markdown
# Bill of Materials: [project_name]

**Revision**: 1.0
**Date**: [ISO 8601 date]
**Target quantity**: [number] ([scale tier])

## BOM

| # | Part name               | Description                    | Qty | Unit cost | Ext. cost | Supplier / Fab method | Lead time   |
|---|-------------------------|--------------------------------|-----|-----------|-----------|-----------------------|-------------|
| 1 | M3×8 SHCS               | Socket head cap screw, stainless | 20 | $0.04     | $0.80     | McMaster 92196A112    | 1–3 days    |
| 2 | 20×20 aluminum extrusion| 200 mm length, T-slot          | 2   | $3.50     | $7.00     | Misumi HFS5-2020-200  | 3–5 days    |
| 3 | motor_plate             | Custom PETG bracket            | 1   | $0.80     | $0.80     | FDM in-house          | 1 day       |
| … | …                       | …                              | …   | …         | …         | …                     | …           |

**Total assembly cost**: $[sum]

## Notes

- [Any sourcing caveats, substitution options, or procurement dependencies]
```

## Quality Criteria

- BOM includes every OTS component and custom part from the assembly.
- Each line item has a unit cost and extended cost; a total assembly cost is summed.
- Each OTS part has a supplier; custom parts note fabrication method in the supplier column.
- Lead time or fabrication time estimate is provided for each line item.

## Context

The BOM is used directly by `evaluate_manufacturability` to calculate per-unit cost across scale tiers and identify high-cost or long-lead items. Accuracy here is critical — gaps in cost or lead time will degrade the quality of scale recommendations.
