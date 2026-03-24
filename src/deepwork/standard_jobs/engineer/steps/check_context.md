# Check Supporting Context Files

## Objective

Verify that supporting context files referenced by agent.md are present, correctly linked,
and syntactically valid.

## Task

Follow every reference from the agent context file and verify the referenced files exist
and are well-formed. This catches broken links, missing files, and syntax errors that would
cause the `implement` workflow to fail or produce incorrect results.

### Process

1. **Extract references from agent.md audit**
   - Read the `agent_md_audit.md` from the previous step
   - Collect the list of referenced files identified there
   - If agent.md was not found, report that no context files can be checked and note
     that agent.md must be created first

2. **Check each referenced file**
   - For each file reference:
     - Verify the file exists at the referenced path
     - If it's a symlink, verify the target exists
     - If it's a relative path, resolve it relative to agent.md's location
     - Check that the file is not empty (zero bytes)

3. **Validate syntax**
   - For each file that exists, validate based on its extension:
     - `.yml` / `.yaml`: Valid YAML (parseable without errors)
     - `.json`: Valid JSON
     - `.md`: Valid Markdown (no broken internal links within the file)
     - `.toml`: Valid TOML
     - `.nix`: Basic syntax check (balanced braces/brackets)
   - For files with no recognized extension, skip syntax validation

4. **Check for orphaned context files**
   - Look for common context file patterns near agent.md that are NOT referenced:
     - `CONTRIBUTING.md`, `ARCHITECTURE.md`, `DEVELOPMENT.md`
     - `.editorconfig`, `.tool-versions`, `flake.nix`
   - These are informational — report them as "available but unreferenced" (not failures)

## Output Format

### .deepwork/tmp/context_audit.md

**Structure**:
```markdown
# Context File Audit

## Source
- Agent context file: [path from audit]
- Agent context status: [PASS/FAIL from previous step]

## Referenced Files

| # | Path | Exists | Symlink | Syntax | Status |
|---|------|--------|---------|--------|--------|
| 1 | [path] | yes/no | yes→[target]/no | valid/invalid/skipped | PASS/FAIL |
| 2 | [path] | yes/no | no | valid | PASS |

## Issues Found
- [Issue 1: description and remediation]
- [none]

## Unreferenced Context Files
- [path] — [brief description of what it contains]
- [none found]

## Overall Status: [PASS/FAIL]
- Referenced files checked: [N]
- Passed: [N]
- Failed: [N]
```

## Quality Criteria

- Every file reference from agent.md is checked
- Symlinks are fully resolved
- Syntax validation matches the file format
- Broken references include specific paths for remediation
- Unreferenced context files are noted as informational, not failures
