# Run Scale Analysis

## Objective

Evaluate the normalized BOM at each requested scale tier and produce actionable recommendations for cost reduction, lead-time improvement, and manufacturing method transitions.

## Task

Read `bom_context.md`, apply scale-tier logic, and produce a structured report covering unit cost, lead time, method transitions, and bottlenecks per tier.

### Process

1. **Identify the scale tiers to analyze** — Read the "Target scales" field from `bom_context.md`.

2. **For each BOM line item, evaluate each tier** using the Manufacturing Methods and Scale Tiers guidance from the job context:
   - Does the manufacturing method change at this scale?
   - Are volume discounts available for OTS parts?
   - Is tooling investment required? Amortize its cost over the tier volume.

3. **Calculate total unit cost per tier** — Sum per-tier unit costs across all lines.

4. **Identify bottlenecks** — Flag any line item that:
   - Represents >20% of total assembly cost at any tier
   - Has lead time >10 business days
   - Requires significant tooling investment to scale

5. **Write recommendations** — 1–3 specific, actionable suggestions per tier:
   - Process substitutions that would reduce cost (cite the break-even quantity)
   - OTS alternatives to custom parts
   - Supplier consolidation opportunities
   - Tooling investments worth making before a specific scale threshold

6. **Save output** to `.deepwork/tmp/scale_report.md` and (if a project directory is known) `mech_design/{project_name}/scale_evaluation.md`.

## Output Format

### .deepwork/tmp/scale_report.md

```markdown
# Scale Analysis Report

**Assembly**: [name from bom_context.md]
**Date**: [ISO 8601 date]
**Tiers analyzed**: [prototype / small_batch / production]

## Unit Cost Summary

| Scale tier  | Qty range  | Unit cost | Change vs. prior tier |
|-------------|------------|-----------|----------------------|
| Prototype   | [qty range]| $[cost]   | —                    |
| Small batch | [qty range]| $[cost]   | −[X]% ($[delta])     |
| Production  | [qty range]| $[cost]   | −[X]% ($[delta])     |

---

## Prototype Tier

**Unit cost**: $[cost]

### Bottlenecks
- **[Part name]**: $[cost] ([X]% of total) — [reason it dominates]

### Recommendations
1. [Specific, actionable suggestion with rationale]

---

## Small Batch Tier

**Unit cost**: $[cost]

### Method transitions from prototype
- **[Part name]**: [prior method] → [new method] at [qty] units — saves $[amount]/unit

### Bottlenecks
- ...

### Recommendations
1. ...

---

## Production Tier

**Unit cost**: $[cost]

### Method transitions from small batch
- **[Part name]**: [prior method] → [new method] — tooling cost ~$[X], break-even at [qty] units

### Bottlenecks
- ...

### Recommendations
1. ...

---

## Manufacturing Method Transition Table

| Part name       | Prototype      | Small batch    | Production         |
|-----------------|----------------|----------------|--------------------|
| [part]          | [method]       | [method]       | [method]           |
```

## Quality Criteria

- Every requested scale tier is analyzed.
- Total unit cost is calculated for each tier.
- Parts that should change manufacturing method between tiers are explicitly called out with the break-even quantity.
- Each tier includes 1–3 concrete recommendations to reduce cost or lead time.

## Context

This is the final step of the `evaluate_at_scale` workflow and mirrors the analysis in `evaluate_manufacturability` at the end of `design_assembly`. The output is intended for engineering and business stakeholders deciding when to invest in tooling, volume purchasing, or process transitions.
