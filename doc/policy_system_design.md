# Policy System Design

## Overview

The deepwork policy system enables automated enforcement of development standards during AI-assisted coding sessions. This document describes the architecture for the next-generation policy system with support for:

1. **File correspondence matching** (sets and pairs)
2. **Idempotent command execution**
3. **Stateful evaluation with queue-based processing**
4. **Efficient agent output management**

## Core Concepts

### Policy Types

The system supports three policy types:

| Type | Purpose | Trigger Direction |
|------|---------|-------------------|
| **Instruction policies** | Prompt agent with instructions | Any matched file |
| **Command policies** | Run idempotent commands | Any matched file |
| **Correspondence policies** | Enforce file relationships | When relationship is incomplete |

### File Correspondence

Correspondence policies define relationships between files that should change together.

**Sets (Bidirectional)**
- Define N patterns that share a common variable path
- If ANY file matching one pattern changes, ALL corresponding files should change
- Example: Source files and their tests

**Pairs (Directional)**
- Define a trigger pattern and one or more expected patterns
- Changes to trigger files require corresponding expected files to also change
- Changes to expected files alone do not trigger the policy
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

### Actions

Policies can specify two types of actions:

**Prompt Action (default)**
```yaml
action:
  type: prompt
  instructions: |
    Please review the changes...
```

**Command Action**
```yaml
action:
  type: command
  command: "ruff format {file}"
  run_for: each_match
```

Command actions execute idempotent commands. The system verifies idempotency by running the command twice and checking that no additional changes occur.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Policy System                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Detector   │───▶│    Queue     │◀───│  Evaluator   │      │
│  │              │    │              │    │              │      │
│  │ - Watch files│    │ .deepwork/   │    │ - Process    │      │
│  │ - Match pols │    │ tmp/policy/  │    │   queued     │      │
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

The detector identifies when policies should be evaluated:

1. **Trigger Detection**: Monitors for file changes that match policy triggers
2. **Deduplication**: Computes a hash to avoid re-processing identical triggers
3. **Queue Entry Creation**: Creates entries for the evaluator to process

**Trigger Hash Computation**:
```python
hash_input = f"{policy_name}:{sorted(trigger_files)}:{baseline_ref}"
trigger_hash = sha256(hash_input.encode()).hexdigest()[:12]
```

The baseline_ref varies by `compare_to` mode:
- `base`: merge-base commit hash
- `default_tip`: remote tip commit hash
- `prompt`: timestamp of last prompt submission

### Queue

The queue persists policy trigger state in `.deepwork/tmp/policy/queue/`:

```
.deepwork/tmp/policy/queue/
├── {hash}.queued.json      # Detected, awaiting evaluation
├── {hash}.passed.json      # Evaluated, policy satisfied
├── {hash}.failed.json      # Evaluated, policy not satisfied
└── {hash}.skipped.json     # Safety pattern matched, skipped
```

**Queue Entry Schema**:
```json
{
  "policy_name": "string",
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
- Entries older than 24 hours are automatically pruned
- `passed` and `skipped` entries are pruned after 1 hour
- Manual cleanup via `deepwork policy clear-queue`

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

### Standard Instruction Policy

```
1. Detector: File changes detected
2. Detector: Check each policy's trigger patterns
3. Detector: For matching policy, compute trigger hash
4. Detector: If hash not in queue, create .queued entry
5. Evaluator: Process queued entry
6. Evaluator: Check safety patterns against changed files
7. Evaluator: If safety matches, mark .skipped
8. Evaluator: If no safety match, return instructions to agent
9. Agent: Addresses policy, includes <promise> tag
10. Evaluator: On next check, mark .passed (promise found)
```

### Correspondence Policy (Set)

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

### Correspondence Policy (Pair)

```
1. Detector: File api/users.py changed (trigger pattern)
2. Matcher: Matches "api/{path}.py" with {path}="users"
3. Resolver: Generate expected: "docs/api/users.md"
4. Detector: Check if docs/api/users.md also changed
5. Detector: If yes, mark .skipped
6. Detector: If no, create .queued entry
7. Evaluator: Return instructions

Note: If only docs/api/users.md changed (not api/users.py),
the pair policy does NOT trigger (directional).
```

### Command Policy

```
1. Detector: Python file changed, matches "**/*.py"
2. Detector: Create .queued entry for format policy
3. Evaluator: Execute "ruff format {file}"
4. Evaluator: Run git diff to check for changes
5. Evaluator: If changes made, re-run command (idempotency check)
6. Evaluator: If no additional changes, mark .passed
7. Evaluator: If changes keep occurring, mark .failed, alert user
```

## Agent Output Management

### Problem

When many policies trigger, the agent receives excessive output, degrading performance.

### Solution

**1. Output Batching**
Group related policies into single messages:

```
The following policies require attention:

## File Correspondence Issues (3)

1. **Source/Test Pairing**: src/auth/login.py changed without tests/auth/login_test.py
2. **Source/Test Pairing**: src/api/users.py changed without tests/api/users_test.py
3. **API Documentation**: api/users.py changed without docs/api/users.md

## Code Quality (1)

4. **README Accuracy**: Source files changed, please verify README.md
```

**2. Priority Levels**
Policies can specify priority (critical, high, normal, low):

```yaml
- name: "Security Review"
  trigger: "src/auth/**/*"
  priority: critical
```

Only critical and high priority shown immediately. Normal/low shown in summary.

**3. Deferred Policies**
Low-priority policies can be deferred to end of session:

```yaml
- name: "Documentation Check"
  trigger: "src/**/*"
  priority: low
  defer: true  # Show at session end, not immediately
```

**4. Collapsed Instructions**
Long instructions are truncated with expansion available:

```
## README Accuracy

Source code changed. Please verify README.md is accurate.

[+] Show full instructions (15 lines)
```

## State Persistence

### Directory Structure

```
.deepwork/
├── policies/                # Policy definitions (frontmatter markdown)
│   ├── readme-accuracy.md
│   ├── source-test-pairing.md
│   ├── api-documentation.md
│   └── python-formatting.md
├── tmp/
│   └── policy/
│       ├── queue/           # Queue entries
│       │   ├── abc123.queued.json
│       │   └── def456.passed.json
│       ├── baselines/       # Cached baseline states
│       │   └── prompt_1705420800.json
│       └── cache/           # Pattern matching cache
│           └── patterns.json
└── policy_state.json        # Session state summary
```

### Policy File Format

Each policy is a markdown file with YAML frontmatter:

```markdown
---
trigger: src/**/*.py
safety: README.md
priority: normal
---
Instructions shown to the agent when this policy fires.

These can be multi-line with full markdown formatting.
```

This format enables:
1. Code files to reference policies in comments
2. Human-readable policy documentation
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
         │             │             │
         └─────────────┼─────────────┘
                       │
                       ▼
                  ┌─────────┐
                  │ Pruned  │
                  │(cleanup)│
                  └─────────┘
```

## Error Handling

### Pattern Errors

Invalid patterns are caught at policy load time:

```python
class PatternError(PolicyError):
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

### Policy Files

Policies are stored in `.deepwork/policies/` as individual markdown files with YAML frontmatter. See `doc/policy_syntax.md` for complete syntax documentation.

**Loading Order:**
1. All `.md` files in `.deepwork/policies/` are loaded
2. Files are processed in alphabetical order
3. Filename (without extension) becomes policy identifier

**Policy Discovery:**
```python
def load_policies(policies_dir: Path) -> list[Policy]:
    """Load all policies from the policies directory."""
    policies = []
    for path in sorted(policies_dir.glob("*.md")):
        policy = parse_policy_file(path)
        policy.name = path.stem  # filename without .md
        policies.append(policy)
    return policies
```

### System Configuration

In `.deepwork/config.yml`:

```yaml
policy:
  enabled: true
  policies_dir: .deepwork/policies  # Can be customized
  queue_retention_hours: 24
  max_queued_entries: 100
  output_mode: batched  # batched, individual, summary
  priority_threshold: normal  # Show this priority and above
```

## Performance Considerations

### Caching

- Pattern compilation is cached per-session
- Baseline diffs are cached by commit hash
- Queue lookups use hash-based O(1) access

### Lazy Evaluation

- Patterns only compiled when needed
- File lists only computed for triggered policies
- Instructions only loaded when policy fires

### Parallel Processing

- Multiple queue entries can be processed in parallel
- Command actions can run concurrently (with file locking)
- Pattern matching is parallelized across policies

## Migration from Legacy System

The legacy system used a single `.deepwork.policy.yml` file with array of policies. The new system uses individual markdown files in `.deepwork/policies/`.

**Breaking Changes:**
- Single YAML file replaced with folder of markdown files
- Policy `name` field replaced with filename
- `instructions` / `instructions_file` replaced with markdown body
- New features: sets, pairs, commands, queue-based state

**No backwards compatibility is provided.** Existing `.deepwork.policy.yml` files must be converted manually.

**Conversion Example:**

Old format (`.deepwork.policy.yml`):
```yaml
- name: "README Accuracy"
  trigger: "src/**/*"
  safety: "README.md"
  instructions: |
    Please verify README.md is accurate.
```

New format (`.deepwork/policies/readme-accuracy.md`):
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

- All policy files validated against schema
- Pattern variables sanitized before use
- File paths normalized and validated
