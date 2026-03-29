# Load Existing Assembly BOM

## Objective

Ingest a user-provided BOM and requirements context, normalize them to the standard format, and prepare the data for scale analysis.

## Task

Ask structured questions to locate the BOM and requirements files, then normalize the data so `run_scale_analysis` can operate on it consistently.

### Process

1. **Locate inputs** — Ask structured questions using the AskUserQuestion tool if the paths are unclear:
   - Path to the BOM file (Markdown table, CSV, or plain text)
   - Path to requirements file, or ask the user to describe requirements inline
   - Which scale tiers to evaluate (default: all three — prototype, small batch, production)

2. **Read and normalize the BOM** — Parse every line item and map fields to the standard schema:
   - Part name, description, quantity, unit cost, supplier / fabrication method, manufacturing method, lead time
   - If a field is missing (e.g., no manufacturing method listed), infer it from context or flag it as unknown

3. **Capture requirements context** — Extract or record:
   - Assembly function
   - Target production quantity (to confirm the primary scale tier)
   - Any constraints that affect manufacturing method selection

4. **Flag gaps** — Note any BOM lines with missing cost, method, or supplier. These will reduce analysis accuracy; flag them prominently.

5. **Save output** to `.deepwork/tmp/bom_context.md`.

## Output Format

### .deepwork/tmp/bom_context.md

```markdown
# BOM Context for Scale Analysis

**Source BOM**: [file path]
**Date**: [ISO 8601 date]
**Target scales**: [prototype / small_batch / production — list which are requested]

## Assembly Requirements Summary

- **Function**: [brief description]
- **Target quantity**: [number] → Scale tier: [Prototype / Small batch / Production]
- **Key constraints**: [size, weight, environment, etc.]

## Normalized BOM

| # | Part name               | Qty | Unit cost | Supplier / Fab method  | Mfg method     | Lead time   |
|---|-------------------------|-----|-----------|------------------------|----------------|-------------|
| 1 | [part name]             | [n] | $[cost]   | [supplier / CNC / FDM] | [method]       | [days]      |

**Total current unit cost**: $[sum]

## Data Quality Notes

- Lines with missing cost: [list part names or "none"]
- Lines with unknown manufacturing method: [list or "none"]
- Lines with missing lead time: [list or "none"]
```

## Quality Criteria

- Normalized BOM includes part name, quantity, unit cost, supplier, and manufacturing method for every line item.
- Design requirements (function, constraints, quantity target) are present as context for the analysis.
- The tiers to evaluate are explicitly listed.

## Context

This step is the entry point for the `evaluate_at_scale` workflow when applied to an existing assembly. The normalized context file is the sole input to `run_scale_analysis` — accuracy here directly determines the quality of scale recommendations.
