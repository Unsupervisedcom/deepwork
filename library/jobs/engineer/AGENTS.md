# Project Context for engineer

## Location

This job lives in `library/jobs/engineer/`.
It is a library job — available for users to adopt but not auto-installed by the DeepWork runtime.

## File Organization

```
engineer/
├── AGENTS.md              # This file
├── CLAUDE.md -> AGENTS.md # Symlink for Claude Code
├── job.yml                # Job definition (all step instructions inlined)
└── requirements.md        # RFC 2119 requirements specification
```

## Workflows

- **implement**: 6-step workflow executing engineering work from product issue through PR merge and product sync
- **doctor**: 3-step workflow validating agent.md and domain context files

## Design Decisions

1. **Domain-agnostic**: Domain adaptation tables (software, hardware, CAD, firmware, docs) live in `job.yml` `common_job_info`; step instructions are written to be domain-agnostic and rely on those tables
2. **Six implement steps**: Preserves TDD discipline boundary (red tests committed before green implementation)
3. **product_sync is separate**: Workflow can pause at finalize_pr while PR undergoes human review
4. **Doctor focuses on agent.md**: Recommends `repo` library job for labels/branch protection/milestones
5. **Requirements bundled**: RFC 2119 spec lives alongside job definition as `requirements.md`

## Last Updated
- Date: 2026-03-25
- From conversation about: Moved from standard_jobs to library/jobs
