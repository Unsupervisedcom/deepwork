# Rules Configuration Syntax

This document describes the syntax for rule files in the `.deepwork/rules/` directory.

## Directory Structure

Rules are stored as individual markdown files with YAML frontmatter:

```
.deepwork/
└── rules/
    ├── readme-accuracy.md
    ├── source-test-pairing.md
    ├── api-documentation.md
    └── python-formatting.md
```

Each file has:
- **Frontmatter**: YAML configuration between `---` delimiters
- **Body**: Instructions (for prompt actions) or description (for command actions)

This structure enables code files to reference rules:
```python
# Read the rule `.deepwork/rules/source-test-pairing.md` before editing
class AuthService:
    ...
```

## Quick Reference

### Simple Trigger with Prompt

`.deepwork/rules/readme-accuracy.md`:
```markdown
---
name: README Accuracy
trigger: src/**/*
safety: README.md
---
Source code changed. Please verify README.md is accurate.

Check that:
- All public APIs are documented
- Examples are up to date
- Installation instructions are correct
```

### Correspondence Set (bidirectional)

`.deepwork/rules/source-test-pairing.md`:
```markdown
---
name: Source/Test Pairing
set:
  - src/{path}.py
  - tests/{path}_test.py
---
Source and test files should change together.

When modifying source code, ensure corresponding tests are updated.
When adding tests, ensure they test actual source code.
```

### Correspondence Pair (directional)

`.deepwork/rules/api-documentation.md`:
```markdown
---
name: API Documentation
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

### Command Action

`.deepwork/rules/python-formatting.md`:
```markdown
---
name: Python Formatting
trigger: "**/*.py"
action:
  command: ruff format {file}
---
Automatically formats Python files using ruff.

This rule runs `ruff format` on any changed Python files to ensure
consistent code style across the codebase.
```

## Rule Structure

Every rule has two orthogonal aspects:

### Detection Mode

How the rule decides when to fire:

| Mode | Field | Description |
|------|-------|-------------|
| **Trigger/Safety** | `trigger`, `safety` | Fire when trigger matches and safety doesn't |
| **Set** | `set` | Fire when file correspondence is incomplete (bidirectional) |
| **Pair** | `pair` | Fire when file correspondence is incomplete (directional) |

### Action Type

What happens when the rule fires:

| Type | Field | Description |
|------|-------|-------------|
| **Prompt** (default) | (markdown body) | Show instructions to the agent |
| **Command** | `action.command` | Run an idempotent command |

## Detection Modes

### Trigger/Safety Mode

The simplest detection mode. Fires when changed files match `trigger` patterns and no changed files match `safety` patterns.

```yaml
---
name: Security Review
trigger:
  - src/auth/**/*
  - src/crypto/**/*
safety: SECURITY.md
compare_to: base
---
```

### Set Mode (Bidirectional Correspondence)

Defines files that should change together. If ANY file in a correspondence group changes, ALL related files should also change.

```yaml
---
name: Source/Test Pairing
set:
  - src/{path}.py
  - tests/{path}_test.py
---
```

**How it works:**

1. A file changes that matches one pattern in the set
2. System extracts the variable portions (e.g., `{path}`)
3. System generates expected files by substituting into other patterns
4. If ALL expected files also changed: rule is satisfied (no trigger)
5. If ANY expected file is missing: rule fires

If `src/auth/login.py` changes:
- Extracts `{path}` = `auth/login`
- Expects `tests/auth/login_test.py` to also change
- If test didn't change, fires with instructions

If `tests/auth/login_test.py` changes:
- Extracts `{path}` = `auth/login`
- Expects `src/auth/login.py` to also change
- If source didn't change, fires with instructions

### Pair Mode (Directional Correspondence)

Defines directional relationships. Changes to trigger files require corresponding expected files to change, but not vice versa.

```yaml
---
name: API Documentation
pair:
  trigger: api/{module}/{name}.py
  expects: docs/api/{module}/{name}.md
---
```

Can specify multiple expected patterns:

```yaml
---
pair:
  trigger: api/{path}.py
  expects:
    - docs/api/{path}.md
    - schemas/{path}.json
---
```

If `api/users/create.py` changes:
- Expects `docs/api/users/create.md` to also change
- If doc didn't change, fires with instructions

If `docs/api/users/create.md` changes alone:
- No trigger (documentation can be updated independently)

## Action Types

### Prompt Action (Default)

The markdown body after frontmatter serves as instructions shown to the agent. This is the default when no `action` field is specified.

**Template Variables in Instructions:**

| Variable | Description |
|----------|-------------|
| `{trigger_file}` | The file that triggered the rule |
| `{trigger_files}` | All files that matched trigger patterns |
| `{expected_files}` | Expected corresponding files (for sets/pairs) |

### Command Action

Runs an idempotent command instead of prompting the agent.

```yaml
---
name: Python Formatting
trigger: "**/*.py"
safety: "*.pyi"
action:
  command: ruff format {file}
  run_for: each_match
---
```

**Template Variables in Commands:**

| Variable | Description | Available When |
|----------|-------------|----------------|
| `{file}` | Single file path | `run_for: each_match` |
| `{files}` | Space-separated file paths | `run_for: all_matches` |
| `{repo_root}` | Repository root directory | Always |

**Idempotency Requirement:**

Commands should be idempotent--running them multiple times produces the same result. Lint formatters like `black`, `ruff format`, and `prettier` are good examples: they produce consistent output regardless of how many times they run.

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
| `src/{path}.py` | `{path}` = multi-segment path | `src/foo/bar.py` -> `path=foo/bar` |
| `src/{name}.py` | `{name}` = single segment | `src/utils.py` -> `name=utils` |
| `{module}/{name}.py` | Both variables | `auth/login.py` -> `module=auth, name=login` |

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
- "src/{**module}/index.py"   # src/foo/bar/index.py -> module=foo/bar
- "src/{*component}.py"       # src/Button.py -> component=Button
```

## Field Reference

### name (required)

Human-friendly name for the rule. Displayed in promise tags and output.

```yaml
---
name: Source/Test Pairing
---
```

### File Naming

Rule files are named using kebab-case with `.md` extension:
- `readme-accuracy.md`
- `source-test-pairing.md`
- `api-documentation.md`

The filename serves as the rule's identifier in the queue system.

### trigger

File patterns that cause the rule to fire (trigger/safety mode). Can be string or array.

```yaml
---
trigger: src/**/*.py
---

---
trigger:
  - src/**/*.py
  - lib/**/*.py
---
```

### safety (optional)

File patterns that suppress the rule. If ANY changed file matches a safety pattern, the rule does not fire.

```yaml
---
safety: CHANGELOG.md
---

---
safety:
  - CHANGELOG.md
  - docs/**/*
---
```

### set

List of patterns defining bidirectional file relationships (set mode).

```yaml
---
set:
  - src/{path}.py
  - tests/{path}_test.py
---
```

### pair

Object with `trigger` and `expects` patterns for directional relationships (pair mode).

```yaml
---
pair:
  trigger: api/{path}.py
  expects: docs/api/{path}.md
---

---
pair:
  trigger: api/{path}.py
  expects:
    - docs/api/{path}.md
    - schemas/{path}.json
---
```

### action (optional)

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

## Complete Examples

### Example 1: Test Coverage Rule

`.deepwork/rules/test-coverage.md`:
```markdown
---
name: Test Coverage
set:
  - src/{path}.py
  - tests/{path}_test.py
---
Source code was modified without corresponding test updates.

Modified source: {trigger_file}
Expected test: {expected_files}

Please either:
1. Add/update tests for the changed code
2. Explain why tests are not needed
```

### Example 2: Documentation Sync

`.deepwork/rules/api-documentation-sync.md`:
```markdown
---
name: API Documentation Sync
pair:
  trigger: src/api/{module}/{endpoint}.py
  expects:
    - docs/api/{module}/{endpoint}.md
    - openapi/{module}.yaml
---
API endpoint changed. Please update:
- Documentation: {expected_files}
- Ensure OpenAPI spec is current
```

### Example 3: Auto-formatting Pipeline

`.deepwork/rules/python-black-formatting.md`:
```markdown
---
name: Python Black Formatting
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

### Example 4: Multi-file Correspondence

`.deepwork/rules/full-stack-feature-sync.md`:
```markdown
---
name: Full Stack Feature Sync
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
```

### Example 5: Conditional Safety

`.deepwork/rules/version-bump-required.md`:
```markdown
---
name: Version Bump Required
trigger:
  - src/**/*.py
  - pyproject.toml
safety:
  - pyproject.toml
  - CHANGELOG.md
---
Code changes detected. Before merging, ensure:
- Version is bumped in pyproject.toml (if needed)
- CHANGELOG.md is updated

This rule is suppressed if you've already modified pyproject.toml
or CHANGELOG.md, as that indicates you're handling versioning.
```

## Promise Tags

When a rule fires but should be dismissed, use promise tags in the conversation. The tag content should be human-readable, using the rule's `name` field:

```
<promise>Source/Test Pairing</promise>
<promise>API Documentation Sync</promise>
```

The friendly name makes promise tags easy to read when displayed in the conversation. The system matches promise tags to rules using case-insensitive comparison of the `name` field.

## Validation

Rule files are validated on load. Common errors:

**Invalid frontmatter:**
```
Error: .deepwork/rules/my-rule.md - invalid YAML frontmatter
```

**Missing required field:**
```
Error: .deepwork/rules/my-rule.md - must have 'trigger', 'set', or 'pair'
```

**Invalid pattern:**
```
Error: .deepwork/rules/test-coverage.md - invalid pattern "src/{path" - unclosed brace
```

**Conflicting fields:**
```
Error: .deepwork/rules/my-rule.md - has both 'trigger' and 'set' - use one or the other
```

**Empty body:**
```
Error: .deepwork/rules/my-rule.md - instruction rules require markdown body
```

## Referencing Rules in Code

A key benefit of the `.deepwork/rules/` folder structure is that code files can reference rules directly:

```python
# Read `.deepwork/rules/source-test-pairing.md` before editing this file

class UserService:
    """Service for user management."""
    pass
```

```typescript
// This file is governed by `.deepwork/rules/api-documentation.md`
// Any changes here require corresponding documentation updates

export async function createUser(data: UserInput): Promise<User> {
    // ...
}
```

This helps AI agents and human developers understand which rules apply to specific files.
