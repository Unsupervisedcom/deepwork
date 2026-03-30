# Project Context for engineer

## Location

This job lives in `library/jobs/engineer/`.
It is a library job — available for users to adopt but not auto-installed by the DeepWork runtime.

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
    ├── discover_requirements.md
    ├── draft_requirements.md
    ├── validate_requirements.md
    ├── check_agent_md.md
    ├── check_context.md
    └── doctor_report.md
```

## Workflows

- **implement**: 6-step workflow executing engineering work from product issue through PR merge and product sync
- **requirements**: 3-step workflow to create or amend RFC 2119 requirements in the project's requirements directory
- **doctor**: 3-step workflow validating AGENTS.md and domain context files

## Requirements directory

The `requirements` workflow stores requirement files in `./requirements/` by
default (relative to the repository root). Each file follows the `REQ-NNN-slug.md`
naming convention with RFC 2119 keywords.

To use a custom path, add a `## Requirements` section to the project's AGENTS.md:

```markdown
## Requirements

Requirements are stored in `docs/specs/requirements/`.
```

The workflow reads this section at discovery time. If no override is found, it
falls back to `./requirements/`.

## Design Decisions

1. **Domain-agnostic**: Domain adaptation tables (software, hardware, CAD, firmware, docs) live in `job.yml` `common_job_info`; step instructions are written to be domain-agnostic and rely on those tables
2. **Six implement steps**: Preserves TDD discipline boundary (red tests committed before green implementation)
3. **product_sync is separate**: Workflow can pause at finalize_pr while PR undergoes human review
4. **Doctor focuses on AGENTS.md**: Recommends `repo` library job for labels/branch protection/milestones
5. **Requirements bundled**: RFC 2119 spec lives alongside job definition as `requirements.md`
6. **Self-documenting via requirements.md**: Library jobs are exempt from the DeepWork `specs/` traceability chain. Each library job carries its own RFC 2119 spec as `requirements.md`. This is the authoritative behavioral contract for the job — no corresponding entry in `specs/` is required.

## Last Updated
- Date: 2026-03-30
- From conversation about: Added requirements workflow (discover, draft, validate), updated requirements.md with Req 9-12
