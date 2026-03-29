# Evaluate Manufacturability at Scale

## Objective

Analyze the assembly BOM at prototype, small-batch, and production scale tiers, then produce concrete recommendations for method transitions, cost reduction, and lead-time optimization.

## Task

Read the assembly requirements (for the target scale context) and the BOM (for per-part costs and methods), then produce a tiered evaluation covering unit cost, lead time, and manufacturing method changes at each scale.

### Process

1. **Confirm target tiers** — Use the scale tier from `assembly_requirements.md`. Always analyze all three tiers (prototype, small batch, production) unless the requirements explicitly exclude one. Apply the scale tier definitions and manufacturing method guidance from the job context.

2. **For each BOM line item, assess each tier:**
   - Would the manufacturing method change at this scale? (e.g., FDM → injection mold for plastic parts at production scale)
   - Would a different supplier or sourcing strategy be used?
   - How does unit cost change with volume (volume discounts, tooling amortization)?

3. **Calculate total unit cost per tier** — Sum the per-tier unit costs across all BOM lines.

4. **Flag bottlenecks** — Identify parts that:
   - Represent more than 20% of total cost at any tier
   - Have lead times exceeding 2 weeks
   - Require tooling investment to scale (e.g., injection mold tooling)

5. **Write recommendations** — For each tier, provide 1–3 actionable recommendations to reduce cost or lead time.

6. **Save output** to `.deepwork/tmp/scale_evaluation.md` (and to the project's `mech_design/` directory as described in the job context).

## Output Format

### .deepwork/tmp/scale_evaluation.md

```markdown
# Scale Evaluation: [project_name]

**Date**: [ISO 8601 date]
**BOM revision**: [from bom.md]

## Summary

| Scale tier     | Qty range  | Total unit cost | Key constraint            |
|----------------|------------|-----------------|---------------------------|
| Prototype      | 1–10       | $[cost]         | [e.g., print time]        |
| Small batch    | 10–500     | $[cost]         | [e.g., CNC setup cost]    |
| Production     | 500+       | $[cost]         | [e.g., mold tooling $X]   |

---

## Prototype Tier (1–10 units)

**Total unit cost**: $[cost]

### Method recommendations
- [Part name]: [Recommended method] — [Reason]

### Bottlenecks
- [Part or factor limiting speed or driving cost]

### Recommendations
1. [Actionable suggestion]

---

## Small Batch Tier (10–500 units)

**Total unit cost**: $[cost]

### Method transitions from prototype
- [Part name]: FDM → CNC machining — [Reason: tolerance, strength, volume cost]

### Bottlenecks
- ...

### Recommendations
1. ...

---

## Production Tier (500+ units)

**Total unit cost**: $[cost]

### Method transitions from small batch
- [Part name]: CNC → injection molding — [Tooling cost: ~$X, break-even at Y units]

### Bottlenecks
- ...

### Recommendations
1. ...

---

## Manufacturing Method Transition Summary

| Part name       | Prototype      | Small batch    | Production         |
|-----------------|----------------|----------------|--------------------|
| [part_name]     | FDM print      | FDM print      | Injection molding  |
| [part_name]     | OTS            | OTS            | OTS (volume buy)   |
```

