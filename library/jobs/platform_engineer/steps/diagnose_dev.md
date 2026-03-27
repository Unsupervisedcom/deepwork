# Diagnose Dev Environment

## Objective

Debug a local development environment issue by systematically checking common failure modes, attempting safe fixes, and either resolving the problem or creating a GitHub issue with full diagnostic context so the developer is unblocked.

## Task

Read the project's platform context, understand the symptom the developer is experiencing, check common failure modes for the detected tech stack, attempt safe remediations, and verify the fix. If the issue cannot be resolved, create a GitHub issue with all diagnostic information gathered during the session.

### Process

1. **Read context.md to understand the project's tech stack and tooling**
   - Identify the infrastructure type (Nix/direnv, Docker Compose, cloud-managed, hybrid)
   - Note which tools are available (nix, docker, kubectl, database CLIs, etc.)
   - Note the language/framework stack (Node, Python, Rust, Go, etc.)
   - Note the package manager (pnpm, uv, cargo, etc.)
   - Note any CI/CD, database, or service dependencies documented in the context

2. **Ask the user about the symptom**
   - Use the AskUserQuestion tool to ask the user to describe the problem:
     - What command fails or what behavior is broken?
     - What is the exact error message (if any)?
     - When did this last work? Did anything change recently (OS update, dependency change, branch switch)?
   - If the user provides a command, attempt to reproduce it by running the command and capturing the output
   - Record the symptom verbatim for the diagnostic report

3. **Check common failure modes based on the detected stack**

   Work through the relevant categories below based on what context.md reports. For each check, run the diagnostic command, record the result, and note whether it passed or failed.

   **Nix / direnv** (when context.md lists Nix tooling):
   - Check if `.envrc` exists and `direnv allow` has been run (`direnv status`)
   - Check if `flake.lock` is stale relative to `flake.nix` (`git log -1 --format=%ci flake.lock` vs `flake.nix`)
   - Try evaluating the dev shell (`nix develop --command true`) to detect flake evaluation errors
   - Check for Nix store corruption (`nix-store --verify --check-contents 2>&1 | head -20`)
   - Verify expected tools are on PATH (`which <tool>` for tools listed in context.md)

   **Docker / containers** (when context.md lists Docker tooling):
   - Check for stale or stopped containers (`docker ps -a --filter status=exited`)
   - Check for port conflicts (`docker ps --format '{{.Ports}}'` cross-referenced with `ss -tlnp` or `lsof -i`)
   - Check volume permissions (`docker volume ls`, inspect relevant volumes)
   - Check Docker network connectivity (`docker network ls`, `docker network inspect <network>`)
   - Check if Docker Compose services are healthy (`docker compose ps`)
   - Check Docker disk usage (`docker system df`)

   **Database** (when context.md lists database tooling or config):
   - Check database connectivity (attempt to connect using the project's configured DATABASE_URL or equivalent)
   - Check for migration drift (`<migration_tool> status` — e.g., `alembic current`, `prisma migrate status`, `diesel migration list`)
   - Check if the test database exists and is accessible
   - Check if the database is running (for local databases: `docker compose ps db` or `pg_isready`)

   **Dependencies** (always check):
   - Check for lockfile conflicts or staleness (compare lockfile modification time with manifest file)
   - Run the project's install command (`pnpm install`, `uv sync`, `cargo build`, etc.) and check for errors
   - Check for missing native/system dependencies (common: openssl, libpq, pkg-config)
   - Check for version mismatches between the lockfile and the manifest

   **Environment variables** (always check):
   - Check for `.env` or `.env.local` file existence
   - If an `.env.example` or `.env.template` exists, diff it against the actual `.env` to find missing variables
   - Check that required environment variables referenced in error messages are set
   - Do NOT print actual secret values — only check for presence/absence

   **Build artifacts and caches** (when relevant to the error):
   - Check for stale build artifacts (`node_modules/.cache`, `target/`, `__pycache__/`, `.next/`, `dist/`)
   - Check disk space (`df -h .`)
   - Check if build tools can run successfully (`<build_tool> --version`)

4. **For each potential issue found, attempt a safe fix**

   Safe fixes (OK to run without explicit approval):
   - `direnv allow` — re-authorize the environment
   - `nix develop --command true` — rebuild the dev shell
   - `docker compose up -d` — restart containers
   - `docker compose down && docker compose up -d` — full container restart
   - `<package_manager> install` or `<package_manager> sync` — reinstall dependencies
   - `<migration_tool> upgrade` or `<migration_tool> migrate deploy` — run pending migrations
   - Clear build caches (`rm -rf node_modules/.cache`, `cargo clean`, `rm -rf __pycache__`)
   - Create missing `.env` from `.env.example` (without secrets — prompt user for secret values)

   Fixes that MUST NOT be performed:
   - Deleting data directories or database volumes
   - Force-pushing or resetting git state
   - Modifying production configuration files
   - Running commands with `sudo` unless the user explicitly approves
   - Modifying files outside the repository
   - Installing tools globally (per Nix dev shell conventions)

   After attempting each fix, document what was done and whether it succeeded or failed.

5. **Verify the fix worked by re-running the failing command**
   - Run the exact command the user reported as failing
   - If it succeeds, record the resolution
   - If it still fails, check whether the error has changed (partial fix) or is the same
   - If the error changed, return to step 3 to diagnose the new error

6. **If unresolved after checking common issues, create a GitHub issue**
   - Gather all diagnostic information into a structured issue body
   - Create the issue using `gh issue create` with the following structure:
     ```
     Title: [dev-env] <Brief description of the symptom>
     Labels: bug, dev-environment
     ```
   - The issue body MUST include:
     - **Symptom**: Exact error message and failing command
     - **Environment**: OS, shell, relevant tool versions from context.md
     - **Checks Performed**: Table of all diagnostic checks and their results
     - **Fixes Attempted**: What was tried and the outcome of each attempt
     - **Suspected Cause**: Best hypothesis based on the evidence gathered
   - Share the issue URL with the user

## Output Format

### diagnostic_report.md

A structured diagnostic report documenting the full investigation.

**Structure**:
```markdown
# Dev Environment Diagnostic Report

**Date**: [current date]
**Symptom**: [verbatim description of the problem from the user]
**Failing Command**: `[the command that fails]`
**Resolution**: [RESOLVED | UNRESOLVED — see GitHub issue #N]

## Environment

- **OS**: [from context.md or detected]
- **Infrastructure Type**: [from context.md — Nix, Docker, cloud, hybrid]
- **Language/Framework**: [from context.md]
- **Package Manager**: [from context.md]
- **Shell**: [from context.md or detected]
- **Key Tool Versions**: [relevant versions]

## Checks Performed

| # | Check | Status | Details |
|---|-------|--------|---------|
| 1 | [Check name] | PASS/FAIL/SKIP | [Brief finding or "No issues found"] |
| 2 | [Check name] | PASS/FAIL/SKIP | [Brief finding or "No issues found"] |
| ... | ... | ... | ... |

## Fixes Attempted

### Fix 1: [Description]

**Command**: `[command run]`
**Result**: [SUCCESS/FAILED]
**Details**: [What happened]

### Fix 2: [Description]
...

## Resolution

### If resolved:
**Root Cause**: [What was actually wrong]
**Fix Applied**: [What fixed it]
**Prevention**: [How to prevent this in the future, if applicable]

### If unresolved:
**Best Hypothesis**: [Most likely root cause based on evidence]
**GitHub Issue**: [URL of created issue]
**Recommended Next Steps**: [What a human should try next]
```

## Quality Criteria

- **Root Cause Identified**: The root cause of the dev environment issue is identified or clearly stated as unknown with a best hypothesis supported by the diagnostic evidence gathered.
- **Fixes Attempted**: Safe fixes were attempted with their outcomes documented. No destructive actions were taken. Each fix attempt includes the exact command run and its output.
- **Developer Unblocked**: The developer is either unblocked with a working fix (verified by re-running the failing command) or a GitHub issue was created with full diagnostic context to track the blocker.

## Context

This step is part of the `doctor` workflow, which is the first tool a developer should reach for when their local environment is broken (per convention 49). It runs after `gather_context`, which provides the `context.md` file describing the project's tech stack, available tools, and infrastructure type.

The goal is rapid resolution — most dev environment issues fall into a small number of categories (stale caches, missing dependencies, container drift, environment variable gaps). By checking these systematically, the step resolves the majority of problems without requiring deep investigation.

When the issue cannot be resolved automatically, creating a GitHub issue ensures the problem is tracked, the diagnostic work is preserved, and another team member (or a future agent run) can pick up where this one left off. The issue label `dev-environment` (convention 48) makes these discoverable in the project's troubleshooting knowledge base.

Investigation follows the core investigation principles (conventions 1-6): no destructive actions, document what was checked even when no anomalies are found, and assign honest confidence levels to findings.
