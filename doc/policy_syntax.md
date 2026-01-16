# Policy Configuration Syntax

This document describes the syntax for policy files in the `.deepwork/policies/` directory.

## Directory Structure

Policies are stored as individual markdown files with YAML frontmatter:

```
.deepwork/
└── policies/
    ├── readme-accuracy.md
    ├── source-test-pairing.md
    ├── api-documentation.md
    └── python-formatting.md
```

Each file has:
- **Frontmatter**: YAML configuration between `---` delimiters
- **Body**: Instructions (for prompt policies) or description (for command policies)

This structure enables code files to reference policies:
```python
# Read the policy `.deepwork/policies/source-test-pairing.md` before editing
class AuthService:
    ...
```

## Quick Reference

### Instruction Policy

`.deepwork/policies/readme-accuracy.md`:
```markdown
---
trigger: src/**/*
safety: README.md
---
Source code changed. Please verify README.md is accurate. Note that this is called only once even if there are many changes, so verify all changes.

Check that:
- All public APIs are documented
- Examples are up to date
- Installation instructions are correct
```

### Correspondence Set (bidirectional)

`.deepwork/policies/source-test-pairing.md`:
```markdown
---
set:
  - src/{path}.py
  - tests/{path}_test.py
---
Source and test files should change together.

When modifying source code, ensure corresponding tests are updated.
When adding tests, ensure they test actual source code.
```

### Correspondence Pair (directional)

`.deepwork/policies/api-documentation.md`:
```markdown
---
pair:
  trigger: api/{path}.py
  expects: docs/api/{path}.md
---
API changes require documentation updates.

When modifying an API endpoint, update its documentation to reflect:
- Parameter changes
- Response format changes
- New error conditions
```

### Command Policy

`.deepwork/policies/python-formatting.md`:
```markdown
---
trigger: "**/*.py"
action:
  command: ruff format {file}
---
Automatically formats Python files using ruff.

This policy runs `ruff format` on any changed Python files to ensure
consistent code style across the codebase.
```

## Policy Types

### Instruction Policies

Instruction policies prompt the AI agent with guidance when certain files change.

**Frontmatter fields:**
```yaml
---
trigger: pattern              # Required: file pattern(s) that trigger
safety: pattern               # Optional: file pattern(s) that suppress
compare_to: base              # Optional: comparison baseline
priority: normal              # Optional: output priority
---
```

The markdown body contains the instructions shown to the agent.

**Example:** `.deepwork/policies/security-review.md`

```markdown
---
trigger:
  - src/auth/**/*
  - src/crypto/**/*
safety: SECURITY.md
compare_to: base
priority: critical
---
Security-sensitive code has been modified.

Please verify:
1. No credentials are hardcoded
2. Input validation is present
3. Authentication checks are correct
```

### Correspondence Sets

Sets define bidirectional relationships between files. When any file in a correspondence group changes, all related files should also change.

**Frontmatter fields:**
```yaml
---
set:                            # Required: list of corresponding patterns
  - pattern1/{path}.ext1
  - pattern2/{path}.ext2
---
```

The markdown body contains instructions for when correspondence is incomplete.

**How it works:**

1. A file changes that matches one pattern in the set
2. System extracts the variable portions (e.g., `{path}`)
3. System generates expected files by substituting into other patterns
4. If ALL expected files also changed: policy is satisfied (no trigger)
5. If ANY expected file is missing: policy triggers with instructions

**Example:** `.deepwork/policies/source-test-pairing.md`

```markdown
---
set:
  - src/{path}.py
  - tests/{path}_test.py
---
Source and test files should change together.

Changed: {trigger_file}
Expected: {expected_files}

Please ensure both source and test are updated.
```

If `src/auth/login.py` changes:
- Extracts `{path}` = `auth/login`
- Expects `tests/auth/login_test.py` to also change
- If test didn't change, shows instructions

If `tests/auth/login_test.py` changes:
- Extracts `{path}` = `auth/login`
- Expects `src/auth/login.py` to also change
- If source didn't change, shows instructions

**Example:** `.deepwork/policies/model-schema-migration.md`

```markdown
---
set:
  - models/{name}.py
  - schemas/{name}.py
  - migrations/{name}.sql
---
Models, schemas, and migrations should stay in sync.

When modifying database models, ensure:
- Schema definitions are updated
- Migration files are created or updated
```

### Correspondence Pairs

Pairs define directional relationships. Changes to trigger files require corresponding expected files to change, but not vice versa.

**Frontmatter fields:**
```yaml
---
pair:
  trigger: pattern/{path}.ext     # Required: pattern that triggers
  expects: pattern/{path}.ext     # Required: expected to also change
---
```

Can also specify multiple expected patterns:

```yaml
---
pair:
  trigger: pattern/{path}.ext
  expects:
    - pattern1/{path}.ext
    - pattern2/{path}.ext
---
```

**Example:** `.deepwork/policies/api-documentation.md`

```markdown
---
pair:
  trigger: api/{module}/{name}.py
  expects: docs/api/{module}/{name}.md
---
API endpoint changed without documentation update.

Changed: {trigger_file}
Please update: {expected_files}

Ensure the documentation covers:
- Endpoint URL and method
- Request parameters
- Response format
- Error cases
```

If `api/users/create.py` changes:
- Expects `docs/api/users/create.md` to also change
- If doc didn't change, shows instructions

If `docs/api/users/create.md` changes alone:
- No trigger (documentation can be updated independently)

### Command Policies

Command policies run idempotent commands instead of prompting the agent.

**Frontmatter fields:**
```yaml
---
trigger: pattern                  # Required: files that trigger
safety: pattern                   # Optional: files that suppress
action:
  command: command {file}         # Required: command to run
  run_for: each_match             # Optional: each_match (default) or all_matches
---
```

The markdown body serves as a description of what the command does (shown in logs, not to agent).

**Template Variables in Commands:**

| Variable | Description | Available When |
|----------|-------------|----------------|
| `{file}` | Single file path | `run_for: each_match` |
| `{files}` | Space-separated file paths | `run_for: all_matches` |
| `{repo_root}` | Repository root directory | Always |

**Example:** `.deepwork/policies/python-formatting.md`

```markdown
---
trigger: "**/*.py"
safety: "*.pyi"
action:
  command: ruff format {file}
  run_for: each_match
---
Automatically formats Python files using ruff.

This ensures consistent code style without requiring manual formatting.
Stub files (*.pyi) are excluded as they have different formatting rules.
```

**Example:** `.deepwork/policies/eslint-check.md`

```markdown
---
trigger: "**/*.{js,ts,tsx}"
action:
  command: eslint --fix {files}
  run_for: all_matches
---
Runs ESLint with auto-fix on all changed JavaScript/TypeScript files.
```

**Idempotency Requirement:**

Commands MUST be idempotent. The system verifies this by:
1. Running the command
2. Checking for changes
3. If changes occurred, running again
4. If more changes occur, marking as failed

## Pattern Syntax

### Basic Glob Patterns

Standard glob patterns work in `trigger` and `safety` fields:

| Pattern | Matches |
|---------|---------|
| `*.py` | Python files in current directory |
| `**/*.py` | Python files in any directory |
| `src/**/*` | All files under src/ |
| `test_*.py` | Files starting with `test_` |
| `*.{js,ts}` | JavaScript and TypeScript files |

### Variable Patterns

Variable patterns use `{name}` syntax to capture path segments:

| Pattern | Captures | Example Match |
|---------|----------|---------------|
| `src/{path}.py` | `{path}` = multi-segment path | `src/foo/bar.py` → `path=foo/bar` |
| `src/{name}.py` | `{name}` = single segment | `src/utils.py` → `name=utils` |
| `{module}/{name}.py` | Both variables | `auth/login.py` → `module=auth, name=login` |

**Variable Naming Conventions:**

- `{path}` - Conventional name for multi-segment captures (`**/*`)
- `{name}` - Conventional name for single-segment captures (`*`)
- Custom names allowed: `{module}`, `{component}`, etc.

**Multi-Segment vs Single-Segment:**

By default, `{path}` matches multiple path segments and `{name}` matches one:

```yaml
# {path} matches: foo, foo/bar, foo/bar/baz
- "src/{path}.py"  # src/foo.py, src/foo/bar.py, src/a/b/c.py

# {name} matches only single segment
- "src/{name}.py"  # src/foo.py (NOT src/foo/bar.py)
```

To explicitly control this, use `{**name}` for multi-segment or `{*name}` for single:

```yaml
- "src/{**module}/index.py"   # src/foo/bar/index.py → module=foo/bar
- "src/{*component}.py"       # src/Button.py → component=Button
```

## Field Reference

### File Naming

Policy files are named using kebab-case with `.md` extension:
- `readme-accuracy.md`
- `source-test-pairing.md`
- `api-documentation.md`

The filename (without extension) serves as the policy's unique identifier for logging and promise tags.

### trigger (instruction/command policies)

File patterns that cause the policy to fire. Can be string or array.

```yaml
---
# Single pattern
trigger: src/**/*.py
---

---
# Multiple patterns
trigger:
  - src/**/*.py
  - lib/**/*.py
---
```

### safety (optional)

File patterns that suppress the policy. If ANY changed file matches a safety pattern, the policy does not fire.

```yaml
---
# Single pattern
safety: CHANGELOG.md
---

---
# Multiple patterns
safety:
  - CHANGELOG.md
  - docs/**/*
---
```

### set (correspondence sets)

List of patterns defining bidirectional file relationships.

```yaml
---
set:
  - src/{path}.py
  - tests/{path}_test.py
---
```

### pair (correspondence pairs)

Object with `trigger` and `expects` patterns for directional relationships.

```yaml
---
pair:
  trigger: api/{path}.py
  expects: docs/api/{path}.md
---

---
# Or with multiple expects
pair:
  trigger: api/{path}.py
  expects:
    - docs/api/{path}.md
    - schemas/{path}.json
---
```

### Markdown Body (instructions)

The markdown content after the frontmatter serves as instructions shown to the agent when the policy fires.

**Template Variables in Instructions:**

| Variable | Description |
|----------|-------------|
| `{trigger_file}` | The file that triggered the policy |
| `{trigger_files}` | All files that matched trigger patterns |
| `{expected_files}` | Expected corresponding files (for sets/pairs) |
| `{safety_files}` | Files that would suppress the policy |

### action (command policies)

Specifies a command to run instead of prompting.

```yaml
---
action:
  command: ruff format {file}
  run_for: each_match  # or all_matches
---
```

### compare_to (optional)

Determines the baseline for detecting file changes.

| Value | Description |
|-------|-------------|
| `base` (default) | Compare to merge-base with default branch |
| `default_tip` | Compare to current tip of default branch |
| `prompt` | Compare to state at last prompt submission |

```yaml
---
compare_to: prompt
---
```

### priority (optional)

Controls output ordering and visibility.

| Value | Behavior |
|-------|----------|
| `critical` | Always shown first, blocks progress |
| `high` | Shown prominently |
| `normal` (default) | Standard display |
| `low` | Shown in summary, may be collapsed |

```yaml
---
priority: critical
---
```

### defer (optional)

When `true`, policy output is deferred to end of session.

```yaml
---
defer: true
---
```

## Complete Examples

### Example 1: Test Coverage Policy

`.deepwork/policies/test-coverage.md`:
```markdown
---
set:
  - src/{path}.py
  - tests/{path}_test.py
compare_to: base
---
Source code was modified without corresponding test updates.

Modified source: {trigger_file}
Expected test: {expected_files}

Please either:
1. Add/update tests for the changed code
2. Explain why tests are not needed (and mark with <promise>)
```

### Example 2: Documentation Sync

`.deepwork/policies/api-documentation-sync.md`:
```markdown
---
pair:
  trigger: src/api/{module}/{endpoint}.py
  expects:
    - docs/api/{module}/{endpoint}.md
    - openapi/{module}.yaml
priority: high
---
API endpoint changed. Please update:
- Documentation: {expected_files}
- Ensure OpenAPI spec is current

If this is an internal-only change, mark as addressed.
```

### Example 3: Auto-formatting Pipeline

`.deepwork/policies/python-black-formatting.md`:
```markdown
---
trigger: "**/*.py"
safety:
  - "**/*.pyi"
  - "**/migrations/**"
action:
  command: black {file}
  run_for: each_match
---
Formats Python files using Black.

Excludes:
- Type stub files (*.pyi)
- Database migration files
```

`.deepwork/policies/typescript-prettier.md`:
```markdown
---
trigger: "**/*.{ts,tsx}"
action:
  command: prettier --write {file}
  run_for: each_match
---
Formats TypeScript files using Prettier.
```

### Example 4: Multi-file Correspondence

`.deepwork/policies/full-stack-feature-sync.md`:
```markdown
---
set:
  - backend/api/{feature}/routes.py
  - backend/api/{feature}/models.py
  - frontend/src/api/{feature}.ts
  - frontend/src/components/{feature}/**/*
---
Feature files should be updated together across the stack.

When modifying a feature, ensure:
- Backend routes are updated
- Backend models are updated
- Frontend API client is updated
- Frontend components are updated

Changed: {trigger_files}
Expected: {expected_files}
```

### Example 5: Conditional Safety

`.deepwork/policies/version-bump-required.md`:
```markdown
---
trigger:
  - src/**/*.py
  - pyproject.toml
safety:
  - pyproject.toml
  - CHANGELOG.md
compare_to: base
priority: low
defer: true
---
Code changes detected. Before merging, ensure:
- Version is bumped in pyproject.toml (if needed)
- CHANGELOG.md is updated

This policy is suppressed if you've already modified pyproject.toml
or CHANGELOG.md, as that indicates you're handling versioning.
```

## Promise Tags

When a policy fires but should be dismissed, use promise tags in the conversation:

```
<promise>policy-filename</promise>
```

Use the policy filename (without `.md` extension) as the identifier:

```
<promise>test-coverage</promise>
<promise>api-documentation-sync</promise>
```

This tells the system the policy has been addressed (either by action or explicit acknowledgment).

## Validation

Policy files are validated on load. Common errors:

**Invalid frontmatter:**
```
Error: .deepwork/policies/my-policy.md - invalid YAML frontmatter
```

**Missing required field:**
```
Error: .deepwork/policies/my-policy.md - must have 'trigger', 'set', or 'pair'
```

**Invalid pattern:**
```
Error: .deepwork/policies/test-coverage.md - invalid pattern "src/{path" - unclosed brace
```

**Conflicting fields:**
```
Error: .deepwork/policies/my-policy.md - has both 'trigger' and 'set' - use one or the other
```

**Empty body:**
```
Error: .deepwork/policies/my-policy.md - instruction policies require markdown body
```

## Referencing Policies in Code

A key benefit of the `.deepwork/policies/` folder structure is that code files can reference policies directly:

```python
# Read `.deepwork/policies/source-test-pairing.md` before editing this file

class UserService:
    """Service for user management."""
    pass
```

```typescript
// This file is governed by `.deepwork/policies/api-documentation.md`
// Any changes here require corresponding documentation updates

export async function createUser(data: UserInput): Promise<User> {
    // ...
}
```

This helps AI agents and human developers understand which policies apply to specific files.
