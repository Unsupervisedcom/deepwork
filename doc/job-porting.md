# Job Porting: Global and Project Scope

Design document for `/deepwork_jobs.port` — a skill that ports DeepWork jobs between project-local and global (`~/.deepwork/`) scope.

## Problem

All DeepWork jobs are project-scoped today. Every path, hook, doc spec, and output reference assumes a project root. A global job needs to work in any project, which means it cannot assume any specific project structure exists.

## Scope Mapping

The global directory structure mirrors the project-local one:

| Scope   | Jobs                 | Doc Specs                 | Skills              | Config                 |
|---------|----------------------|---------------------------|---------------------|------------------------|
| Project | `.deepwork/jobs/`    | `.deepwork/doc_specs/`    | `.claude/skills/`   | `.deepwork/config.yml` |
| Global  | `~/.deepwork/jobs/`  | `~/.deepwork/doc_specs/`  | `~/.claude/skills/` | `~/.deepwork/config.yml` |

This mirrors the existing convention where `.claude/CLAUDE.md` (project) and `~/.claude/CLAUDE.md` (global) coexist.

## Portability Tensions

### 1. Output Paths

Project-local jobs have concrete output paths:

```yaml
outputs:
  - competitive_research/competitors_list.md
  - competitive_research/[competitor_name]/research.md
```

These assume the project wants a `competitive_research/` directory. A global job cannot assume that. The recommended approach is to parameterize the output root:

```yaml
inputs:
  - name: output_dir
    description: "Directory for job outputs"
outputs:
  - "{output_dir}/competitors_list.md"
  - "{output_dir}/[competitor_name]/research.md"
```

This aligns with how inputs already work in `job.yml` and avoids imposing structure on the target project.

### 2. Doc Specs

Doc specs define quality criteria, not project structure, so they are generally portable. The port operation must:

- Copy referenced doc specs from `.deepwork/doc_specs/` to `~/.deepwork/doc_specs/`.
- Rewrite `doc_spec:` references in `job.yml` from `.deepwork/doc_specs/X.md` to `~/.deepwork/doc_specs/X.md`.
- Handle name collisions when a global doc spec with the same name already exists.

### 3. Step Instructions

Step instruction files (`steps/*.md`) may contain:

- **Hardcoded project paths** (`src/components/`, `db/migrate/`) — not portable.
- **References to project tools** ("run `npm test`", "use the Rails console") — not portable.
- **Generic workflow guidance** ("ask the user for requirements", "validate against doc spec") — fully portable.

The port operation must audit instructions for project-specific references and flag them for the user to resolve.

### 4. Hook Scripts

Hook scripts (`.sh` files in `hooks/`) are the most fragile:

- They may reference project-specific binaries, paths, or environment.
- Their paths in generated skills resolve as absolute from project root.
- Global hooks must live at `~/.deepwork/jobs/{name}/hooks/`.

Prompt-based hooks (`prompt:` and `prompt_file:`) are inherently more portable than `script:` hooks. The port operation should warn or block on script hooks that are not obviously portable.

### 5. AGENTS.md

`AGENTS.md` files contain project-specific context by definition (bespoke learnings from `/deepwork_jobs.learn`). When porting to global, the operation should either strip the file entirely or extract only generalizable content and flag the rest for review.

When porting from global to project, the `AGENTS.md` starts empty and accumulates project-specific learnings via `/deepwork_jobs.learn` as normal.

## Precedence and Override Model

Following the pattern established by standard jobs and `CLAUDE.md`:

```
Global job (baseline) -> Project-local job (override)
```

- If a project has a local job with the same name as a global job, local wins.
- `deepwork sync` generates skills from both scopes, with local taking precedence.
- This allows users to install a global job and then customize it per-project.

## The `scope` Field

Rather than retrofitting portability onto existing jobs, add a `scope` field to `job.yml`:

```yaml
name: code_review
scope: portable  # or "local" (default)
version: "1.0.0"
```

When `scope: portable`:

- `/deepwork_jobs.define` enforces parameterized output paths.
- `/deepwork_jobs.review_job_spec` adds portability criteria to its validation.
- `/deepwork_jobs.implement` generates instructions without project-specific references.
- `/deepwork_jobs.learn` separates generalizable learnings from bespoke ones more aggressively.

This makes portability a design-time decision rather than a post-hoc transformation.

## Port Operations

### Project to Global

1. **Select job** — ask which local job to port.
2. **Portability audit** — scan for:
   - Hardcoded project paths in step instructions (patterns like `src/`, `app/`, stack-specific file extensions).
   - Script hooks (warn, suggest converting to prompt hooks).
   - `AGENTS.md` content (strip or flag).
   - Output paths without parameterization.
3. **Transform** —
   - Rewrite output paths to use `{output_dir}` parameter or ask the user for a strategy.
   - Add `output_dir` as an input to the first step if not already present.
   - Rewrite `doc_spec:` paths from `.deepwork/` to `~/.deepwork/`.
   - Remove or generalize `AGENTS.md`.
4. **Copy** — write to `~/.deepwork/jobs/{name}/` and `~/.deepwork/doc_specs/`.
5. **Sync global** — run `deepwork sync --global` to generate skills in `~/.claude/skills/`.

### Global to Project

1. **Select job** — list available global jobs.
2. **Copy** — inject from `~/.deepwork/jobs/{name}/` to `.deepwork/jobs/{name}/`.
3. **Localize** — rewrite `doc_spec:` paths to `.deepwork/doc_specs/`, copy doc specs into the project.
4. **Optionally concretize** — ask if the user wants to replace `{output_dir}` with a concrete project path.
5. **Sync** — run normal `deepwork sync`.

## Infrastructure Changes

The port skill depends on changes to the DeepWork CLI and sync pipeline:

1. **`~/.deepwork/` directory convention** — the CLI must recognize this as the global job store.
2. **`deepwork sync --global`** — sync must be scope-aware, generating skills to `~/.claude/skills/` from `~/.deepwork/jobs/`.
3. **Precedence in sync** — when both global and local jobs exist with the same name, local wins. The merged set gets synced.
4. **`deepwork install` awareness** — optionally inject global user jobs into projects, or let sync handle the merge at skill generation time.
