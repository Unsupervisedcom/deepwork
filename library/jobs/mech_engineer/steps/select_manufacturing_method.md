# Select Manufacturing Method

## Objective

Recommend the optimal manufacturing process and material for the part at both prototype and production scale, with design-for-manufacture guidance.

## Task

Read the part specification and apply the manufacturing method guidelines from the job context to produce a justified manufacturing recommendation.

### Process

1. **Assess key drivers** from `part_spec.md`:
   - Geometry complexity (organic curves, undercuts, internal features)
   - Tightest tolerance requirement
   - Load conditions (peak force, fatigue, temperature)
   - Material constraints
   - Target production quantity (from the parent assembly context, or ask the user if running standalone)

2. **Select prototype method** — Choose the fastest iteration path. Prefer FDM or SLA for plastic parts, off-the-shelf stock for metal prototypes. Justify against the spec.

3. **Select production method** — Choose the lowest unit cost at target volume. Apply the scale tier boundaries from the job context (injection molding at 10,000+, CNC for metal at moderate volumes, etc.).

4. **Specify material** — Give grade and key properties. Examples:
   - Plastic prototype: PLA or PETG (FDM), ABS or Nylon (SLS)
   - Metal prototype: 6061-T6 aluminum (CNC or waterjet)
   - Production plastic: ABS, PC, or PA66 (injection molding)

5. **Write DFM notes** — Flag features that will complicate fabrication:
   - FDM: overhangs >45°, walls <1.2 mm, unsupported bridging >30 mm
   - CNC: deep pockets, thin webs, undercuts requiring 5-axis
   - Injection molding: draft angles, wall uniformity, gate locations

6. **Estimate unit cost** — Rough estimate per unit at each scale using:
   - FDM: ~$0.05–0.20/g of material + 10–30 min print time
   - CNC: $15–80/hr machining time
   - Injection molding: tooling $5,000–50,000 + $0.50–5/unit

## Output Format

### .deepwork/tmp/manufacturing_spec.md

```markdown
# Manufacturing Specification: [part_name]

## Recommendation Summary

| Scale       | Method                | Material            | Est. unit cost |
|-------------|----------------------|---------------------|----------------|
| Prototype   | [e.g., FDM 3D print]  | [e.g., PETG]        | $[cost]        |
| Production  | [e.g., Injection mold]| [e.g., ABS]         | $[cost]        |

## Prototype Method: [Method Name]

**Justification**: [Why this process for prototype scale, referencing spec requirements]

### Process parameters
- [Layer height, infill %, supports — for FDM]
- [Turning/milling operations — for CNC]

### Material: [Material and grade]
- Key properties: [tensile strength, heat deflection temp, etc.]

## Production Method: [Method Name]

**Justification**: [Why this process at production scale]

### Tooling requirements
- [Mold, fixture, or jig needed and estimated cost]

### Material: [Material and grade]
- Key properties: [as above]

## Tolerances

| Feature                | Prototype tolerance | Production tolerance | Method                  |
|------------------------|--------------------|-----------------------|-------------------------|
| [e.g., bore diameter]  | ±0.2 mm            | ±0.05 mm              | Reamed post-print / CNC |

## DFM Notes

- [Feature 1]: [Issue and mitigation]
- [Feature 2]: [Issue and mitigation]

## Open Issues

- [Any spec ambiguity that blocks finalizing this recommendation]
```

## Quality Criteria

- The recommended process is justified against the part spec (geometry, loads, volume).
- Prototype and production recommendations are given separately where they differ.
- A specific material is recommended with grade and key properties noted.
- DFM notes cover the critical fabrication risks for the chosen process.

## Context

This step bridges specification and fabrication. The output is used by `document_part` to produce a datasheet ready for fabricator handoff, and by `generate_bom` to estimate unit cost at the assembly level.
