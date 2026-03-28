# Check Agent Context File

Verify that agent.md (or equivalent) exists, declares the engineering domain, provides
build/test/parse instructions, and that CODEOWNERS is configured.

## Process

1. **Locate the agent context file** — check common locations at the repository root:
   `agent.md`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md`.
   Resolve any symlinks. Record which file(s) were found and which candidate paths were checked.
2. **Check domain declaration** — the file MUST explicitly define the project's engineering
   domain (e.g., web application, CAD/mechanical, firmware/embedded, documentation site)
3. **Check agent instructions** — verify the file contains instructions for:
   - **Parse**: How to navigate the codebase (project structure, key files)
   - **Build**: How to build or compile the project
   - **Test**: How to run the test suite
   - If the file only mentions build verification, treat test guidance as missing unless it
     explicitly says that the build command is also the required validation path.
4. **Check CODEOWNERS** — look in `CODEOWNERS`, `.github/CODEOWNERS`, `docs/CODEOWNERS`.
   CODEOWNERS is REQUIRED for automatic reviewer assignment when PRs are undrafted (Req 6).
   Record every CODEOWNERS location checked, even when none exist.
5. **Check for issues** — empty/stub files, circular symlinks, references to nonexistent files

## Output Format

### .deepwork/tmp/agent_md_audit.md

```markdown
# Agent Context File Audit

## File Discovery
- File found: yes/no
- Path: [path or "not found"]
- Is symlink: yes/no → [target]
- Root candidates checked: [`agent.md`, ...]

## Domain Declaration
- Declared: yes/no
- Domain: [domain or "not declared"]

## Agent Instructions
| Category | Present | Details |
|----------|---------|---------|
| Parse/Navigate | yes/no | [brief or "missing"] |
| Build | yes/no | [brief or "missing"] |
| Test | yes/no | [brief or "missing"] |

## CODEOWNERS
- File found: yes/no
- Path: [path or "not found"]
- Rules defined: [N or "empty"]
- Locations checked: [`CODEOWNERS`, ...]

## Issues
- [list or "none"]

## Overall Status: [PASS/FAIL]

## Referenced Files
[list of files to check in next step]
```
