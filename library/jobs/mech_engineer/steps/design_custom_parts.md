# Design Custom Parts

## Objective

Produce a design brief for each custom-fabricated part, covering geometry, material, tolerances, manufacturing method, and a reference to an existing or planned 3D model.

## Task

Read the assembly requirements and OTS component list to identify every sub-function flagged for custom design, then write a design brief for each part.

### Process

1. **List parts to design** — Extract the "Flagged for Custom Design" list from `ots_components.md`. Each entry becomes one custom part.

2. **For each part, define:**
   - **Geometry** — Describe the shape in plain language (e.g., "L-bracket, 40×30×3 mm, two M3 clearance holes on each face"). If a model source file already exists in the repo, reference its path.
   - **Material** — Select based on loads and scale tier (see manufacturing methods in job context).
   - **Critical dimensions and tolerances** — Identify the features that must hit tight tolerances vs. those that can be loose.
   - **Manufacturing method** — Choose from the scale-tier guidance in the job context. Justify the choice.
   - **Model file reference** — Check `agent.md` for the project's CAD toolchain (see Toolchain Adaptation table in job context). Reference the toolchain-appropriate source file (e.g., Python `.py` for AnchorSCAD, `.scad` for OpenSCAD, `.FCStd` for FreeCAD) — not the STL build artifact.
   - **Design-for-manufacture notes** — Flag any features that complicate fabrication (deep holes, undercuts, thin walls, complex curves).

3. **Check for redundancy** — Confirm no designed part duplicates an available OTS component from the prior step.

4. **Save output** to `.deepwork/tmp/custom_parts_plan.md` (and to the project's `mech_design/` directory as described in the job context).

## Output Format

### .deepwork/tmp/custom_parts_plan.md

```markdown
# Custom Parts Plan: [project_name]

## Parts Overview

| # | Part name           | Manufacturing method | Material          | Est. unit cost |
|---|---------------------|----------------------|-------------------|----------------|
| 1 | [e.g., motor_plate] | FDM 3D print         | PETG              | $0.80          |
| 2 | [e.g., shaft_collar]| CNC turning          | Aluminum 6061-T6  | $4.50          |

---

## Part 1: [part_name]

**Function**: [What this part does in the assembly]
**Manufacturing method**: [Process] — [1–2 sentence justification]
**Material**: [Material and grade] — [Key reason: strength, heat resistance, cost, etc.]

### Geometry

[Plain-language description of the shape. Reference an existing model file if one exists.]

- Model source: `[path/to/source_file]` (use toolchain-appropriate format — see agent.md) or *to be created*
- Build command: `[command to generate STL from source, per toolchain table]`
- Key dimensions: [list critical dimensions]

### Tolerances

| Feature               | Tolerance      | Reason                          |
|-----------------------|----------------|---------------------------------|
| [e.g., bore diameter] | ±0.05 mm       | Press fit with bearing OD       |
| [e.g., overall length]| ±0.5 mm        | Non-critical, clearance fit     |

### DFM Notes

- [Any feature that complicates fabrication and how to mitigate it]

---

[Repeat for each custom part]
```

## Quality Criteria

- Each custom part has a manufacturing method matched to the target production scale.
- Each part has a recommended material with justification.
- No custom part duplicates an available OTS option from the prior step.
- Each part references an existing model source file (toolchain-appropriate format per agent.md) or includes notes on what geometry to create.

## Context

This step determines the core fabrication workload and cost of the assembly. Under-specifying parts here leads to fabrication errors and rework. The output feeds directly into BOM cost estimation and scale evaluation.
