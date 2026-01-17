# Rules System Design

## Overview

The deepwork rules system enables automated enforcement of development standards during AI-assisted coding sessions. This document describes the architecture for the next-generation rules system with support for:

1. **File correspondence matching** (sets and pairs)
2. **Idempotent command execution**
3. **Stateful evaluation with queue-based processing**
4. **Efficient agent output management**

## Core Concepts

### Rule Structure

Every rule has two orthogonal aspects:

**Detection Mode** - How the rule decides when to fire:

| Mode | Field | Description |
|------|-------|-------------|
| **Trigger/Safety** | `trigger`, `safety` | Fire when trigger matches and safety doesn't |
| **Set** | `set` | Fire when file correspondence is incomplete (bidirectional) |
| **Pair** | `pair` | Fire when file correspondence is incomplete (directional) |

**Action Type** - What happens when the rule fires:

| Type | Field | Description |
|------|-------|-------------|
| **Prompt** (default) | (markdown body) | Show instructions to the agent |
| **Command** | `action.command` | Run an idempotent command |

### Detection Modes

**Trigger/Safety Mode**
- Simplest mode: fire when files match `trigger` and none match `safety`
- Good for general checks like "source changed, verify README"

**Set Mode (Bidirectional Correspondence)**
- Define N patterns that share a common variable path
- If ANY file matching one pattern changes, ALL corresponding files should change
- Example: Source files and their tests

**Pair Mode (Directional Correspondence)**
- Define a trigger pattern and one or more expected patterns
- Changes to trigger files require corresponding expected files to also change
- Changes to expected files alone do not trigger the rule
- Example: API code requires documentation updates

### Pattern Variables

Patterns use `{name}` syntax for capturing variable path segments:

```
src/{path}.py          # {path} captures everything between src/ and .py
tests/{path}_test.py   # {path} must match the same value
```

Special variable names:
- `{path}` - Matches any path segments (equivalent to `**/*`)
- `{name}` - Matches a single path segment (equivalent to `*`)
- `{**}` - Explicit multi-segment wildcard
- `{*}` - Explicit single-segment wildcard

### Action Types

**Prompt Action (default)**
The markdown body of the rule file serves as instructions shown to the agent.

**Command Action**
```yaml
action:
  command: "ruff format {file}"
  run_for: each_match
```

Command actions should be idempotent—running them multiple times produces the same result. Lint formatters like `black`, `ruff format`, and `prettier` are good examples.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Rules System                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Detector   │───▶│    Queue     │◀───│  Evaluator   │      │
│  │              │    │              │    │              │      │
│  │ - Watch files│    │ .deepwork/   │    │ - Process    │      │
│  │ - Match rules│    │ tmp/rules/   │    │   queued     │      │
│  │ - Create     │    │ queue/       │    │ - Run action │      │
│  │   entries    │    │              │    │ - Update     │      │
│  └──────────────┘    └──────────────┘    │   status     │      │
│                                          └──────────────┘      │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐                          │
│  │   Matcher    │    │   Resolver   │                          │
│  │              │    │              │                          │
│  │ - Pattern    │    │ - Variable   │                          │
│  │   matching   │    │   extraction │                          │
│  │ - Glob       │    │ - Path       │                          │
│  │   expansion  │    │   generation │                          │
│  └──────────────┘    └──────────────┘                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Detector

The detector identifies when rules should be evaluated:

1. **Trigger Detection**: Monitors for file changes that match rule triggers
2. **Deduplication**: Computes a hash to avoid re-processing identical triggers
3. **Queue Entry Creation**: Creates entries for the evaluator to process

**Trigger Hash Computation**:
```python
hash_input = f"{rule_name}:{sorted(trigger_files)}:{baseline_ref}"
trigger_hash = sha256(hash_input.encode()).hexdigest()[:12]
```

The baseline_ref varies by `compare_to` mode:
- `base`: merge-base commit hash
- `default_tip`: remote tip commit hash
- `prompt`: timestamp of last prompt submission

### Queue

The queue persists rule trigger state in `.deepwork/tmp/rules/queue/`:

```
.deepwork/tmp/rules/queue/
├── {hash}.queued.json      # Detected, awaiting evaluation
├── {hash}.passed.json      # Evaluated, rule satisfied
├── {hash}.failed.json      # Evaluated, rule not satisfied
└── {hash}.skipped.json     # Safety pattern matched, skipped
```

**Queue Entry Schema**:
```json
{
  "rule_name": "string",
  "trigger_hash": "string",
  "status": "queued|passed|failed|skipped",
  "created_at": "ISO8601 timestamp",
  "evaluated_at": "ISO8601 timestamp or null",
  "baseline_ref": "string",
  "trigger_files": ["array", "of", "files"],
  "expected_files": ["array", "of", "files"],
  "matched_files": ["array", "of", "files"],
  "action_result": {
    "type": "prompt|command",
    "output": "string or null",
    "exit_code": "number or null"
  }
}
```

**Queue Cleanup**:
Since `.deepwork/tmp/` is gitignored, queue entries are transient local state. No aggressive cleanup is required—entries can accumulate without causing issues. The directory can be safely deleted at any time to reset state.

### Evaluator

The evaluator processes queued entries:

1. **Load Entry**: Read queued entry from disk
2. **Verify Still Relevant**: Re-check that trigger conditions still apply
3. **Execute Action**:
   - For prompts: Format message and return to hook system
   - For commands: Execute command, verify idempotency
4. **Update Status**: Mark as passed, failed, or skipped
5. **Report Results**: Return appropriate response to caller

### Matcher

Pattern matching with variable extraction:

**Algorithm**:
```python
def match_pattern(pattern: str, filepath: str) -> dict[str, str] | None:
    """
    Match filepath against pattern, extracting variables.

    Returns dict of {variable_name: captured_value} or None if no match.
    """
    # Convert pattern to regex with named groups
    # {path} -> (?P<path>.+)
    # {name} -> (?P<name>[^/]+)
    # Literal parts are escaped
    regex = pattern_to_regex(pattern)
    match = re.fullmatch(regex, filepath)
    if match:
        return match.groupdict()
    return None
```

**Pattern Compilation**:
```python
def pattern_to_regex(pattern: str) -> str:
    """Convert pattern with {var} placeholders to regex."""
    result = []
    for segment in parse_pattern(pattern):
        if segment.is_variable:
            if segment.name in ('path', '**'):
                result.append(f'(?P<{segment.name}>.+)')
            else:
                result.append(f'(?P<{segment.name}>[^/]+)')
        else:
            result.append(re.escape(segment.value))
    return ''.join(result)
```

### Resolver

Generates expected filepaths from patterns and captured variables:

```python
def resolve_pattern(pattern: str, variables: dict[str, str]) -> str:
    """
    Substitute variables into pattern to generate filepath.

    Example:
        resolve_pattern("tests/{path}_test.py", {"path": "foo/bar"})
        -> "tests/foo/bar_test.py"
    """
    result = pattern
    for name, value in variables.items():
        result = result.replace(f'{{{name}}}', value)
    return result
```

## Evaluation Flow

### Standard Instruction Rule

```
1. Detector: File changes detected
2. Detector: Check each rule's trigger patterns
3. Detector: For matching rule, compute trigger hash
4. Detector: If hash not in queue, create .queued entry
5. Evaluator: Process queued entry
6. Evaluator: Check safety patterns against changed files
7. Evaluator: If safety matches, mark .skipped
8. Evaluator: If no safety match, return instructions to agent
9. Agent: Addresses rule, includes <promise> tag
10. Evaluator: On next check, mark .passed (promise found)
```

### Correspondence Rule (Set)

```
1. Detector: File src/foo/bar.py changed
2. Matcher: Matches pattern "src/{path}.py" with {path}="foo/bar"
3. Resolver: Generate expected files from other patterns:
   - "tests/{path}_test.py" -> "tests/foo/bar_test.py"
4. Detector: Check if tests/foo/bar_test.py also changed
5. Detector: If yes, mark .skipped (correspondence satisfied)
6. Detector: If no, create .queued entry
7. Evaluator: Return instructions prompting for test update
```

### Correspondence Rule (Pair)

```
1. Detector: File api/users.py changed (trigger pattern)
2. Matcher: Matches "api/{path}.py" with {path}="users"
3. Resolver: Generate expected: "docs/api/users.md"
4. Detector: Check if docs/api/users.md also changed
5. Detector: If yes, mark .skipped
6. Detector: If no, create .queued entry
7. Evaluator: Return instructions

Note: If only docs/api/users.md changed (not api/users.py),
the pair rule does NOT trigger (directional).
```

### Command Rule

```
1. Detector: Python file changed, matches "**/*.py"
2. Detector: Create .queued entry for format rule
3. Evaluator: Execute "ruff format {file}"
4. Evaluator: Run git diff to check for changes
5. Evaluator: If changes made, re-run command (idempotency check)
6. Evaluator: If no additional changes, mark .passed
7. Evaluator: If changes keep occurring, mark .failed, alert user
```

## Agent Output Management

### Problem

When many rules trigger, the agent receives excessive output, degrading performance.

### Solution

**1. Output Batching**
Group related rules into concise sections:

```
The following rules require attention:

## Source/Test Pairing
src/auth/login.py → tests/auth/login_test.py
src/api/users.py → tests/api/users_test.py

## API Documentation
api/users.py → docs/api/users.md

## README Accuracy
Source files changed. Verify README.md is accurate.
```

**2. Grouped by Rule Name**
Multiple violations of the same rule are grouped together under a single heading, keeping output compact.

**3. Minimal Decoration**
Avoid excessive formatting, numbering, or emphasis. Use simple arrow notation for correspondence violations.

## State Persistence

### Directory Structure

```
.deepwork/
├── rules/                   # Rule definitions (frontmatter markdown)
│   ├── readme-accuracy.md
│   ├── source-test-pairing.md
│   ├── api-documentation.md
│   └── python-formatting.md
├── tmp/                     # GITIGNORED - transient state
│   └── rules/
│       ├── queue/           # Queue entries
│       │   ├── abc123.queued.json
│       │   └── def456.passed.json
│       ├── baselines/       # Cached baseline states
│       │   └── prompt_1705420800.json
│       └── cache/           # Pattern matching cache
│           └── patterns.json
└── rules_state.json         # Session state summary
```

**Important:** The entire `.deepwork/tmp/` directory is gitignored. All queue entries, baselines, and caches are local transient state that is not committed. This means cleanup is not critical—files can accumulate and will be naturally cleaned when the directory is deleted or the repo is re-cloned.

### Rule File Format

Each rule is a markdown file with YAML frontmatter:

```markdown
---
name: README Accuracy
trigger: src/**/*.py
safety: README.md
---
Instructions shown to the agent when this rule fires.

These can be multi-line with full markdown formatting.
```

This format enables:
1. Code files to reference rules in comments
2. Human-readable rule documentation
3. Easy editing with any markdown editor
4. Clear separation of configuration and content

### Baseline Management

For `compare_to: prompt`, baselines are captured at prompt submission:

```json
{
  "timestamp": "2024-01-16T12:00:00Z",
  "commit": "abc123",
  "staged_files": ["file1.py", "file2.py"],
  "untracked_files": ["file3.py"]
}
```

Multiple baselines can exist for different prompts in a session.

### Queue Lifecycle

```
                  ┌─────────┐
                  │ Created │
                  │ .queued │
                  └────┬────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ .passed │   │ .failed │   │.skipped │
    └─────────┘   └─────────┘   └─────────┘
```

Terminal states persist in `.deepwork/tmp/` (gitignored) until manually cleared or the directory is deleted.

## Error Handling

### Pattern Errors

Invalid patterns are caught at rule load time:

```python
class PatternError(RulesError):
    """Invalid pattern syntax."""
    pass

# Validation
def validate_pattern(pattern: str) -> None:
    # Check for unbalanced braces
    # Check for invalid variable names
    # Check for unsupported syntax
```

### Command Errors

Command execution errors are captured and reported:

```json
{
  "status": "failed",
  "action_result": {
    "type": "command",
    "command": "ruff format {file}",
    "exit_code": 1,
    "stdout": "",
    "stderr": "error: invalid syntax in foo.py:10"
  }
}
```

### Queue Corruption

If queue entries become corrupted:
1. Log error with entry details
2. Remove corrupted entry
3. Re-detect triggers on next evaluation

## Configuration

### Rule Files

Rules are stored in `.deepwork/rules/` as individual markdown files with YAML frontmatter. See `doc/rules_syntax.md` for complete syntax documentation.

**Loading Order:**
1. All `.md` files in `.deepwork/rules/` are loaded
2. Files are processed in alphabetical order
3. Filename (without extension) becomes rule identifier

**Rule Discovery:**
```python
def load_rules(rules_dir: Path) -> list[Rule]:
    """Load all rules from the rules directory."""
    rules = []
    for path in sorted(rules_dir.glob("*.md")):
        rule = parse_rule_file(path)
        rule.name = path.stem  # filename without .md
        rules.append(rule)
    return rules
```

### System Configuration

In `.deepwork/config.yml`:

```yaml
rules:
  enabled: true
  rules_dir: .deepwork/rules  # Can be customized
```

## Performance Considerations

### Caching

- Pattern compilation is cached per-session
- Baseline diffs are cached by commit hash
- Queue lookups use hash-based O(1) access

### Lazy Evaluation

- Patterns only compiled when needed
- File lists only computed for triggered rules
- Instructions only loaded when rule fires

### Parallel Processing

- Multiple queue entries can be processed in parallel
- Command actions can run concurrently (with file locking)
- Pattern matching is parallelized across rules

## Migration from Legacy System

The legacy system used a single `.deepwork.rules.yml` file with array of rules. The new system uses individual markdown files in `.deepwork/rules/`.

**Breaking Changes:**
- Single YAML file replaced with folder of markdown files
- Rule `name` field replaced with filename
- `instructions` / `instructions_file` replaced with markdown body
- New features: sets, pairs, commands, queue-based state

**No backwards compatibility is provided.** Existing `.deepwork.rules.yml` files must be converted manually.

**Conversion Example:**

Old format (`.deepwork.rules.yml`):
```yaml
- name: "README Accuracy"
  trigger: "src/**/*"
  safety: "README.md"
  instructions: |
    Please verify README.md is accurate.
```

New format (`.deepwork/rules/readme-accuracy.md`):
```markdown
---
trigger: src/**/*
safety: README.md
---
Please verify README.md is accurate.
```

## Security Considerations

### Command Execution

- Commands run in sandboxed subprocess
- No shell expansion (arguments passed as array)
- Working directory is always repo root
- Environment variables are filtered

### Queue File Permissions

- Queue directory: 700 (owner only)
- Queue files: 600 (owner only)
- No sensitive data in queue entries

### Input Validation

- All rule files validated against schema
- Pattern variables sanitized before use
- File paths normalized and validated
