# Project Context for deepwork_jobs

This is the source of truth for the `deepwork_jobs` standard job.

## Codebase Structure

- Source location: `src/deepwork/standard_jobs/deepwork_jobs/`
- Templates: `templates/` directory within the job directory
- Loaded at runtime directly from the package (no copy into `.deepwork/jobs/`)

## Location

This job lives in the DeepWork package source at `src/deepwork/standard_jobs/deepwork_jobs/`.
It is loaded directly at runtime by the multi-folder job discovery system — there is no
separate "working copy" in `.deepwork/jobs/`. The MCP server returns the job directory path
as `job_dir` in workflow responses so agents can find templates and scripts.

## File Organization

```
deepwork_jobs/
├── AGENTS.md              # This file
├── job.yml                # Job definition
├── make_new_job.sh        # Script to create new job structure
├── steps/
│   ├── define.md          # Define step instructions
│   ├── implement.md       # Implement step instructions
│   ├── test.md            # Test step instructions
│   ├── iterate.md         # Iterate step instructions
│   ├── learn.md           # Learn step instructions
│   └── supplemental_file_references.md  # Reference documentation
└── templates/
    ├── job.yml.template              # Job spec structure
    ├── step_instruction.md.template  # Step instruction structure
    ├── agents.md.template            # AGENTS.md structure
    ├── job.yml.example               # Complete job example
    └── step_instruction.md.example   # Complete step example
```

## Quality Review Learnings

These learnings come from running the `new_job` workflow to create the `github_outreach` job (2026-02-06).

### Review Criteria Must Be Pragmatic

The implement step's review criteria caused 6+ review iterations during the github_outreach job creation. Key problems and fixes:

1. **"Ask Structured Questions" was applied to ALL steps** — even pure analysis/generation steps with no user input. Fixed in v1.4.0: criterion now auto-passes for steps that only have file inputs from prior steps (no name/description user inputs).

2. **"Output Examples" was too strict** — demanded concrete filled-in examples in every step file, even when a template structure with `[bracket placeholders]` was sufficient. Fixed in v1.4.0: renamed to "Output Format Examples" and accepts templates. Concrete examples are encouraged but not required.

3. **Contradictory review results** — In one case, all 6 individual criteria passed but the overall review still returned `needs_work`. This appears to be a reviewer model issue where the summary contradicts the per-criterion assessments. Added `additional_review_guidance` to clarify when criteria should auto-pass.

### Quality Review Timeouts on Large Outputs

Steps producing many files (25 analysis files) or very long files (700+ line playbook) exceeded the 120-second MCP timeout during quality review. The `quality_review_override_reason` parameter was needed to bypass these.

Mitigation strategies documented in `define.md`:
- Use `run_each: step` instead of `run_each: <files_output>` for steps with many files
- Keep review criteria efficient to evaluate
- Note expected output volume in step descriptions

### Dependency Validation Gaps

The github_outreach `final_report` step had `analyze_repos` as a file input but was missing it from the `dependencies` list. This was caught at workflow start time but could have been caught earlier during the `implement` step. The define step's validation rules already mention this (`from_step must be in dependencies`) but it was missed during creation.

## Version Management

- Version is tracked in `job.yml`
- Bump patch version (0.0.x) for instruction improvements
- Bump minor version (0.x.0) for new features or structural changes

## Last Updated

- Date: 2026-02-06
- From conversation about: Learn workflow analyzing severe quality review issues in the new_job execution
