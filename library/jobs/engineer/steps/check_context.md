# Check Supporting Context Files

Verify that files referenced by agent.md are present, correctly linked, and syntactically
valid. If agent.md was not found, report that context files cannot be checked.

## Process

1. Read `agent_md_audit.md` from the previous step and collect the list of referenced files
2. For each reference: verify it exists, resolve symlinks, check it is non-empty
3. Validate syntax by extension: `.yml`/`.yaml` (valid YAML), `.json` (valid JSON),
   `.md` (no broken internal links), `.toml` (valid TOML), `.nix` (balanced braces)
4. Note any unreferenced context files near agent.md (`CONTRIBUTING.md`, `ARCHITECTURE.md`,
   `.editorconfig`, `flake.nix`, etc.) as informational — not failures

## Output Format

### .deepwork/tmp/context_audit.md

```markdown
# Context File Audit

## Source
- Agent context file: [path]
- Agent context status: [PASS/FAIL]

## Referenced Files

| # | Path | Exists | Symlink | Syntax | Status |
|---|------|--------|---------|--------|--------|
| 1 | [path] | yes/no | yes→[target]/no | valid/invalid/skipped | PASS/FAIL |

## Issues
- [list or "none"]

## Unreferenced Context Files
- [path] — [description]

## Overall Status: [PASS/FAIL]
- Checked: [N], Passed: [N], Failed: [N]
```
