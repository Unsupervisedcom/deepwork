# Research OTS Options

## Objective

Find at least three off-the-shelf candidates that meet the requirements, documented with enough detail to support a selection decision.

## Task

Read the OTS requirements document, search supplier catalogs, and record candidate parts with specs, pricing, and availability.

### Process

1. **Extract search parameters** from `ots_requirements.md`:
   - Key function and dimensional constraints
   - Interface standards (use these as search keywords)
   - Cost and MOQ limits

2. **Search suppliers** — Use at least two distinct sources:
   - **Mechanical hardware**: McMaster-Carr, Misumi, Grainger, Fastenal
   - **Electronics / motors / sensors**: Digi-Key, Mouser, SparkFun, Adafruit, LCSC
   - **General / low-cost**: Amazon, AliExpress, eBay industrial
   - **CAD model libraries**: GrabCAD, TraceParts, Thingiverse (for printable equivalents)

3. **Verify each candidate** — Confirm the part meets every requirement in `ots_requirements.md` before recording it. Note any requirement it fails to meet.

4. **Capture data** — For each candidate: supplier, part number or URL, key specs, unit price, MOQ, lead time, and availability.

5. **Save output** to `.deepwork/tmp/ots_options.md`.

## Output Format

### .deepwork/tmp/ots_options.md

```markdown
# OTS Options: [part_function]

**Requirements reference**: `.deepwork/tmp/ots_requirements.md`
**Date**: [ISO 8601 date]

## Candidates

### Option 1: [Part name / description]

- **Supplier**: [Name]
- **Part number / URL**: [part number or direct link]
- **Key specs**: [dimensions, rating, material — the fields from requirements]
- **Unit cost**: $[price] (MOQ: [number])
- **Lead time**: [days or weeks]
- **Requirements check**:
  - FR1 [function]: ✓ / ✗ [note]
  - FR2 [dimension]: ✓ / ✗ [note]
- **Notes**: [any caveats, datasheet link, review count if marketplace]

---

### Option 2: [Part name / description]

[Same structure]

---

### Option 3: [Part name / description]

[Same structure]

---

## Summary Comparison

| Criterion         | Option 1 | Option 2 | Option 3 |
|-------------------|----------|----------|----------|
| Meets all reqs    | ✓ / ✗    | ✓ / ✗    | ✓ / ✗    |
| Unit cost         | $[price] | $[price] | $[price] |
| Lead time         | [time]   | [time]   | [time]   |
| MOQ               | [qty]    | [qty]    | [qty]    |
```

## Quality Criteria

- At least three distinct candidate parts are documented (or all available options if fewer exist in the market).
- Each candidate's specifications are verified against the requirements document.
- Unit cost and minimum order quantity are recorded for each candidate.

## Context

The quality of this research directly determines whether the selected part will work. Do not include candidates that fail a functional or dimensional requirement — note their failure and exclude them. If fewer than three options exist that meet all requirements, document all available options and note the constraint.
