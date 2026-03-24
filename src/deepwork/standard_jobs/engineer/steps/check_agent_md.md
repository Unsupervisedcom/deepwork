# Check Agent Context File

## Objective

Verify that agent.md (or equivalent domain documentation) exists at the repository root,
declares the engineering domain, and provides build/test/parse instructions for automated agents.

## Task

Audit the repository for the presence and completeness of its agent context file. This is the
foundational check — without a valid agent.md, the `implement` workflow cannot adapt to the
project's domain.

### Process

1. **Locate the agent context file**
   - Check for common names at the repository root:
     - `agent.md`, `AGENT.md`
     - `AGENTS.md`
     - `CLAUDE.md` (if it contains agent-relevant content, not just a symlink)
     - `.claude/CLAUDE.md` (Claude Code project instructions)
   - Check if any of these are symlinks and resolve them
   - Record which file(s) were found and their paths

2. **Check domain declaration**
   - The file MUST explicitly define the project's engineering domain
   - Valid domains include but are not limited to: web application, API service, mobile app,
     CAD/mechanical, PCB/electronics, firmware/embedded, documentation site, data pipeline,
     infrastructure/IaC, monorepo (with sub-domains)
   - Record whether the domain is declared and what it is

3. **Check agent instructions**
   - The file MUST contain instructions for automated agents on how to:
     - **Parse**: How to read/navigate the codebase (project structure, key files)
     - **Build**: How to build or compile the project
     - **Test**: How to run the test suite
   - Record which instruction categories are present and which are missing

4. **Check for CODEOWNERS**
   - Check for a CODEOWNERS file in standard locations:
     - `CODEOWNERS`, `.github/CODEOWNERS`, `docs/CODEOWNERS` (GitHub)
     - Forgejo/Gitea equivalents if applicable
   - If present, verify it contains at least one rule
   - CODEOWNERS is REQUIRED for automatic reviewer assignment when PRs are undrafted
     (Req 6) — its absence is a failure

5. **Check for common issues**
   - Empty or stub file (exists but has no real content)
   - Circular symlinks
   - References to files that don't exist
   - Outdated information (e.g., references to deleted directories)

## Output Format

### .deepwork/tmp/agent_md_audit.md

**Structure**:
```markdown
# Agent Context File Audit

## File Discovery
- File found: yes/no
- Path: [path or "not found"]
- Is symlink: yes/no → [target]
- Format: [markdown/yaml/other]

## Domain Declaration
- Domain declared: yes/no
- Domain: [declared domain or "not declared"]
- Specificity: [specific/vague/missing]

## Agent Instructions
| Category | Present | Details |
|----------|---------|---------|
| Parse/Navigate | yes/no | [brief description or "missing"] |
| Build | yes/no | [brief description or "missing"] |
| Test | yes/no | [brief description or "missing"] |

## CODEOWNERS
- File found: yes/no
- Path: [path or "not found"]
- Rules defined: [N rules or "empty"]

## Issues Found
- [Issue 1: description]
- [Issue 2: description]
- [none]

## Overall Status: [PASS/FAIL]
- Failures: [list of failed checks or "none"]

## Referenced Files
[List of files referenced by agent.md that will be checked in the next step]
```

## Quality Criteria

- All common agent file locations are checked
- Symlinks are resolved and validated
- Domain declaration is checked for specificity (not just presence)
- Build, test, and parse instructions are each independently verified
- Issues are specific and actionable
