# Project Context for research

This is the source of truth for the `research` standard job.

## Purpose

A multi-workflow research suite supporting deep investigation, quick summaries,
material ingestion into notes, and reproduction planning for engineering handoff.

## Location

This job lives in the DeepWork package source at `src/deepwork/standard_jobs/research/`.
It is loaded directly at runtime by the multi-folder job discovery system — there is no
separate "working copy" in `.deepwork/jobs/`. The MCP server returns the job directory path
as `job_dir` in workflow responses so agents can find templates and scripts.

## File Organization

```
research/
├── AGENTS.md              # This file
├── CLAUDE.md              # Symlink to AGENTS.md
├── job.yml                # Job definition with 4 workflows
└── steps/
    ├── scope.md           # Define research scope (shared: deep + quick)
    ├── choose_platforms.md # Select AI platforms (deep only)
    ├── gather.md          # Gather sources, 8+ (deep)
    ├── gather_quick.md    # Gather sources, 3+ (quick)
    ├── synthesize.md      # Synthesize findings (deep)
    ├── summarize.md       # Synthesize + report in one step (quick)
    ├── report.md          # Write final report (deep)
    ├── parse.md           # Parse external material (ingest)
    ├── file.md            # File to notes directory (ingest)
    ├── ingest_material.md # Nested ingest workflow entry (reproduce)
    ├── analyze.md         # Analyze reproducibility (reproduce)
    └── plan.md            # Create reproduction plan (reproduce)
```

## Editing Guidelines

- Source of truth is ALWAYS in `src/deepwork/standard_jobs/research/`
- NEVER edit installed copies in `.deepwork/jobs/` directly
- After editing, run `deepwork install` to sync
- Step instruction files live in `steps/` and are referenced by `instructions_file` in job.yml

## Workflows

| Workflow    | Steps                                          | Purpose                                      |
|-------------|------------------------------------------------|----------------------------------------------|
| `research`  | scope, choose_platforms, gather, synthesize, report | Full multi-platform research (8+ sources)  |
| `quick`     | scope, gather_quick, summarize                 | Fast local-only research (3+ sources)        |
| `ingest`    | parse, file                                    | Import external material into notes          |
| `reproduce` | ingest_material, analyze, plan                 | Ingest + reproducibility analysis + plan     |

## Quality Review Learnings

(No learnings recorded yet. Add findings here as the job is used.)

## Version Management

- Version is tracked in `job.yml`
- Bump patch version (0.0.x) for instruction improvements
- Bump minor version (0.x.0) for new features or structural changes

## Last Updated

- Date: 2026-03-21
- From conversation about: Initial creation of research standard job
