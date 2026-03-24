# Project Context for engineer

## Location

This job lives in the DeepWork package source at `src/deepwork/standard_jobs/engineer/`.
It is loaded directly at runtime by the multi-folder job discovery system.

## File Organization

```
engineer/
├── AGENTS.md              # This file
├── CLAUDE.md -> AGENTS.md # Symlink for Claude Code
├── job.yml                # Job definition
├── requirements.md        # RFC 2119 requirements specification
└── steps/
    ├── translate_issue.md
    ├── initialize_branch.md
    ├── red_tests.md
    ├── green_implementation.md
    ├── finalize_pr.md
    ├── product_sync.md
    ├── check_agent_md.md
    ├── check_context.md
    └── doctor_report.md
```

## Workflows

- **implement**: 6-step workflow executing engineering work from product issue through PR merge and product sync
- **doctor**: 3-step workflow validating agent.md and domain context files

## Design Decisions

1. **Domain-agnostic**: Step instructions include domain adaptation tables (software, hardware, CAD, firmware, docs)
2. **Six implement steps**: Preserves TDD discipline boundary (red tests committed before green implementation)
3. **product_sync is separate**: Workflow can pause at finalize_pr while PR undergoes human review
4. **Doctor focuses on agent.md**: Recommends `repo` library job for labels/branch protection/milestones
5. **Requirements bundled**: RFC 2119 spec lives alongside job definition as `requirements.md`

## Last Updated
- Date: 2026-03-24
- From conversation about: Initial creation of the engineer standard job
