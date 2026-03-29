# Project Context for mech_engineer

## Location

This job lives in `library/jobs/mech_engineer/`.
It is a library job — available for users to adopt but not auto-installed by the DeepWork runtime.

## File Organization

```
mech_engineer/
├── AGENTS.md              # This file
├── CLAUDE.md -> AGENTS.md # Symlink for Claude Code
├── job.yml                # Job definition
└── steps/
    ├── define_assembly_requirements.md
    ├── source_ots_components.md
    ├── design_custom_parts.md
    ├── generate_bom.md
    ├── evaluate_manufacturability.md
    ├── define_part_spec.md
    ├── select_manufacturing_method.md
    ├── document_part.md
    ├── define_ots_requirements.md
    ├── research_ots_options.md
    ├── select_ots_part.md
    ├── load_assembly_bom.md
    └── run_scale_analysis.md
```

## Workflows

- **design_assembly**: Full assembly design from requirements through scale evaluation (5 steps)
- **design_part**: Single custom part spec, manufacturing method selection, and datasheet (3 steps)
- **source_ots_parts**: OTS component requirements, research, and selection (3 steps)
- **evaluate_at_scale**: Load an existing BOM and run multi-scale production analysis (2 steps)

## Design Decisions

1. **Manufacturing method table in common_job_info**: All process/scale tradeoff context lives in `job.yml` so steps don't duplicate it
2. **OTS-first**: `source_ots_components` runs before `design_custom_parts` to minimize unnecessary custom fabrication
3. **Shared scale tiers**: Prototype / small batch / production definitions are canonical across all workflows
4. **`.deepwork/tmp/` for tracking files**: Final deliverables are written to `mech_design/{project_name}/` by step instructions; `.deepwork/tmp/` files are workflow tracking artifacts
5. **`evaluate_at_scale` is standalone**: Allows re-evaluating any existing BOM without re-running the full design workflow
6. **CAD Toolchain Adaptation table**: Like the `engineer` job's domain adaptation table, a Toolchain Adaptation table in `common_job_info` maps generic concepts (model source file, build command, model registry) to tool-specific equivalents (AnchorSCAD, OpenSCAD, FreeCAD, etc.). Steps reference `agent.md` for the project's toolchain; they do NOT hardcode STL/STEP paths. STL is a build artifact, not a source file.

## Known Project Contexts

### ncrmro/plant-caravan (AnchorSCAD)

The `plant-caravan` project uses AnchorSCAD — a Python-based parametric CAD framework:
- Model source files: Python `.py` in `hardware/cad/src/` using `anchorscad-core`
- Build command: `./bin/render` (generates `.scad` → OpenSCAD headless → `.stl`)
- Model registry: `hardware/cad/cadeng.yaml`
- Nix flake provides OpenSCAD with EGL headless support (no X11 needed)

When running `mech_engineer` workflows in plant-caravan, model references should point to Python source files and `cadeng.yaml` entries, not raw STL files.
