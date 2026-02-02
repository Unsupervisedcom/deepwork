# Spec-Driven Development

A structured workflow for building features through executable specifications rather than ad-hoc coding.

## Overview

This job implements "spec-driven development" - a methodology where detailed specifications directly generate working implementations. Instead of jumping straight to code, you first create specifications that serve as executable blueprints.

The workflow progresses through six steps:

1. **Constitution** - Establish project governance principles, technology standards, and quality guidelines
2. **Specify** - Define functional requirements as user stories with acceptance criteria (what and why, not how)
3. **Clarify** - Resolve ambiguities and gaps through systematic questioning
4. **Plan** - Design architecture, select technologies, define data models and API contracts; update project architecture document
5. **Tasks** - Break the plan into ordered, actionable development tasks
6. **Implement** - Execute tasks to deliver the complete feature

## When to Use

This workflow is ideal for:
- New feature development requiring upfront design
- Complex features with multiple stakeholders
- Projects where specification quality directly impacts implementation success
- Teams wanting to capture design decisions for future reference

## Artifacts Produced

- `[docs_folder]/constitution.md` - Project-wide governance principles (created once)
- `[docs_folder]/architecture.md` - Project architecture document (updated with each feature)
- `specs/[feature-name]/spec.md` - Feature requirements and user stories
- `specs/[feature-name]/plan.md` - Technical architecture and implementation strategy
- `specs/[feature-name]/data-model.md` - Database schema and relationships
- `specs/[feature-name]/api-spec.json` - OpenAPI specification (if applicable)
- `specs/[feature-name]/tasks.md` - Ordered task breakdown with dependencies

## Credits

This job is inspired by [spec-kit](https://github.com/github/spec-kit), GitHub's open-source toolkit for spec-driven development. The workflow structure, step progression, and core concepts are adapted from spec-kit's methodology.

## IMPT: REQUIRED CUSTOMIZATION

When installing this job to a new project, you must customize the following:

### Replace `[docs_folder]`

The placeholder `[docs_folder]` appears throughout this job and must be replaced with your project's actual documentation directory path. This can be done with find / sed commands.

**Examples:**
- If your docs are in `docs/`: replace `[docs_folder]` with `docs`
- If your docs are in `documentation/`: replace `[docs_folder]` with `documentation`
- If your docs are at the root: replace `[docs_folder]/constitution.md` with `constitution.md`

## Schema Compatibility Fixes (v0.5.0)

This job has been updated to be compatible with DeepWork v0.5.0 schema validation. The following fixes were applied:

1. **exposed vs hidden**: Changed `hidden: true` to `exposed: false` on all steps (v0.5.0 uses `exposed` property)
2. **Output file paths**: Changed `directory:` property to simple string paths in implement step (only `file` and `doc_spec` are valid output properties)
3. **Output descriptions**: Removed `description` fields from output objects (outputs only accept `{file}` or `{file, doc_spec}`)
4. **Input validation**: Changed plan step's architecture.md input from `{file, description}` to `{name, description}` (inputs must be either `{name, description}` for user parameters or `{file, from_step}` for file references)
5. **Explicit dependencies**: Added all transitive dependencies to steps' `dependencies` arrays (DeepWork requires every `from_step` reference to be explicitly listed in dependencies)
