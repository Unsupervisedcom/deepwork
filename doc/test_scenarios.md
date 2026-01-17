# Rules System Test Scenarios

This document describes test scenarios for validating the rules system implementation.

## 1. Pattern Matching

### 1.1 Basic Glob Patterns

| ID | Scenario | Pattern | File | Expected |
|----|----------|---------|------|----------|
| PM-1.1.1 | Exact match | `README.md` | `README.md` | Match |
| PM-1.1.2 | Exact no match | `README.md` | `readme.md` | No match |
| PM-1.1.3 | Single wildcard | `*.py` | `main.py` | Match |
| PM-1.1.4 | Single wildcard nested | `*.py` | `src/main.py` | No match |
| PM-1.1.5 | Double wildcard | `**/*.py` | `src/main.py` | Match |
| PM-1.1.6 | Double wildcard deep | `**/*.py` | `src/a/b/c/main.py` | Match |
| PM-1.1.7 | Double wildcard root | `**/*.py` | `main.py` | Match |
| PM-1.1.8 | Directory prefix | `src/**/*` | `src/foo.py` | Match |
| PM-1.1.9 | Directory prefix deep | `src/**/*` | `src/a/b/c.py` | Match |
| PM-1.1.10 | Directory no match | `src/**/*` | `lib/foo.py` | No match |
| PM-1.1.11 | Brace expansion | `*.{js,ts}` | `app.ts` | Match |
| PM-1.1.12 | Brace expansion second | `*.{js,ts}` | `app.js` | Match |
| PM-1.1.13 | Brace expansion no match | `*.{js,ts}` | `app.py` | No match |

### 1.2 Variable Patterns

| ID | Scenario | Pattern | File | Expected Variables |
|----|----------|---------|------|-------------------|
| PM-1.2.1 | Single var path | `src/{path}.py` | `src/foo/bar.py` | `{path: "foo/bar"}` |
| PM-1.2.2 | Single var name | `src/{name}.py` | `src/utils.py` | `{name: "utils"}` |
| PM-1.2.3 | Name no nested | `src/{name}.py` | `src/foo/bar.py` | No match |
| PM-1.2.4 | Two variables | `{dir}/{name}.py` | `src/main.py` | `{dir: "src", name: "main"}` |
| PM-1.2.5 | Prefix and suffix | `test_{name}_test.py` | `test_foo_test.py` | `{name: "foo"}` |
| PM-1.2.6 | Nested path | `src/{path}/index.py` | `src/a/b/index.py` | `{path: "a/b"}` |
| PM-1.2.7 | Explicit multi | `src/{**mod}/main.py` | `src/a/b/c/main.py` | `{mod: "a/b/c"}` |
| PM-1.2.8 | Explicit single | `src/{*name}.py` | `src/utils.py` | `{name: "utils"}` |
| PM-1.2.9 | Mixed explicit | `{*dir}/{**path}.py` | `src/a/b/c.py` | `{dir: "src", path: "a/b/c"}` |

### 1.3 Pattern Resolution

| ID | Scenario | Pattern | Variables | Expected Output |
|----|----------|---------|-----------|-----------------|
| PM-1.3.1 | Simple substitution | `tests/{path}_test.py` | `{path: "foo"}` | `tests/foo_test.py` |
| PM-1.3.2 | Nested path | `tests/{path}_test.py` | `{path: "a/b/c"}` | `tests/a/b/c_test.py` |
| PM-1.3.3 | Multiple vars | `{dir}/test_{name}.py` | `{dir: "tests", name: "foo"}` | `tests/test_foo.py` |

## 2. Instruction Rules

### 2.1 Basic Trigger/Safety

| ID | Scenario | Changed Files | Trigger | Safety | Expected |
|----|----------|---------------|---------|--------|----------|
| IR-2.1.1 | Trigger match, no safety | `["src/main.py"]` | `src/**/*.py` | None | Fire |
| IR-2.1.2 | Trigger match, safety match | `["src/main.py", "README.md"]` | `src/**/*.py` | `README.md` | No fire |
| IR-2.1.3 | Trigger no match | `["docs/readme.md"]` | `src/**/*.py` | None | No fire |
| IR-2.1.4 | Multiple triggers, one match | `["lib/utils.py"]` | `["src/**/*.py", "lib/**/*.py"]` | None | Fire |
| IR-2.1.5 | Safety match only | `["README.md"]` | `src/**/*.py` | `README.md` | No fire |
| IR-2.1.6 | Multiple safety, one match | `["src/main.py", "CHANGELOG.md"]` | `src/**/*.py` | `["README.md", "CHANGELOG.md"]` | No fire |
| IR-2.1.7 | Multiple triggers, multiple files | `["src/a.py", "lib/b.py"]` | `["src/**/*.py", "lib/**/*.py"]` | None | Fire |

### 2.2 Compare Modes

```
Setup: Branch diverged 3 commits ago from main
- Commit 1: Added src/feature.py
- Commit 2: Modified src/feature.py
- Commit 3: Added tests/feature_test.py
- Unstaged: Modified src/utils.py
```

| ID | Scenario | compare_to | Expected Changed Files |
|----|----------|------------|----------------------|
| IR-2.2.1 | Base comparison | `base` | `["src/feature.py", "tests/feature_test.py", "src/utils.py"]` |
| IR-2.2.2 | Default tip (main ahead 1) | `default_tip` | All base + main's changes |
| IR-2.2.3 | Prompt baseline (captured after commit 2) | `prompt` | `["tests/feature_test.py", "src/utils.py"]` |

### 2.3 Promise Tags

Promise tags use the rule's `name` field (not filename) with a checkmark prefix for human readability.

| ID | Scenario | Conversation Contains | Rule `name` | Expected |
|----|----------|----------------------|---------------|----------|
| IR-2.3.1 | Standard promise | `<promise>✓ README Accuracy</promise>` | `README Accuracy` | Suppressed |
| IR-2.3.2 | Without checkmark | `<promise>README Accuracy</promise>` | `README Accuracy` | Suppressed |
| IR-2.3.3 | Case insensitive | `<promise>✓ readme accuracy</promise>` | `README Accuracy` | Suppressed |
| IR-2.3.4 | Whitespace | `<promise>  ✓ README Accuracy  </promise>` | `README Accuracy` | Suppressed |
| IR-2.3.5 | No promise | (none) | `README Accuracy` | Not suppressed |
| IR-2.3.6 | Wrong promise | `<promise>✓ Other Rule</promise>` | `README Accuracy` | Not suppressed |
| IR-2.3.7 | Multiple promises | `<promise>✓ A</promise><promise>✓ B</promise>` | `A` | Suppressed |

## 3. Correspondence Sets

### 3.1 Two-Pattern Sets

```yaml
set:
  - "src/{path}.py"
  - "tests/{path}_test.py"
```

| ID | Scenario | Changed Files | Expected |
|----|----------|---------------|----------|
| CS-3.1.1 | Both changed | `["src/foo.py", "tests/foo_test.py"]` | No fire (satisfied) |
| CS-3.1.2 | Only source | `["src/foo.py"]` | Fire (missing test) |
| CS-3.1.3 | Only test | `["tests/foo_test.py"]` | Fire (missing source) |
| CS-3.1.4 | Nested both | `["src/a/b.py", "tests/a/b_test.py"]` | No fire |
| CS-3.1.5 | Nested only source | `["src/a/b.py"]` | Fire |
| CS-3.1.6 | Unrelated file | `["docs/readme.md"]` | No fire |
| CS-3.1.7 | Source + unrelated | `["src/foo.py", "docs/readme.md"]` | Fire |
| CS-3.1.8 | Both + unrelated | `["src/foo.py", "tests/foo_test.py", "docs/readme.md"]` | No fire |

### 3.2 Three-Pattern Sets

```yaml
set:
  - "models/{name}.py"
  - "schemas/{name}.py"
  - "migrations/{name}.sql"
```

| ID | Scenario | Changed Files | Expected |
|----|----------|---------------|----------|
| CS-3.2.1 | All three | `["models/user.py", "schemas/user.py", "migrations/user.sql"]` | No fire |
| CS-3.2.2 | Two of three | `["models/user.py", "schemas/user.py"]` | Fire (missing migration) |
| CS-3.2.3 | One of three | `["models/user.py"]` | Fire (missing 2) |
| CS-3.2.4 | Different names | `["models/user.py", "schemas/order.py"]` | Fire (both incomplete) |

### 3.3 Edge Cases

| ID | Scenario | Changed Files | Expected |
|----|----------|---------------|----------|
| CS-3.3.1 | File matches both patterns | `["src/test_foo_test.py"]` | Depends on pattern specificity |
| CS-3.3.2 | Empty path variable | (N/A - patterns require content) | Pattern validation error |
| CS-3.3.3 | Multiple files same pattern | `["src/a.py", "src/b.py"]` | Fire for each without corresponding test |

## 4. Correspondence Pairs

### 4.1 Basic Pairs

```yaml
pair:
  trigger: "api/{path}.py"
  expects: "docs/api/{path}.md"
```

| ID | Scenario | Changed Files | Expected |
|----|----------|---------------|----------|
| CP-4.1.1 | Both changed | `["api/users.py", "docs/api/users.md"]` | No fire |
| CP-4.1.2 | Only trigger | `["api/users.py"]` | Fire |
| CP-4.1.3 | Only expected | `["docs/api/users.md"]` | No fire (directional) |
| CP-4.1.4 | Trigger + unrelated | `["api/users.py", "README.md"]` | Fire |
| CP-4.1.5 | Expected + unrelated | `["docs/api/users.md", "README.md"]` | No fire |

### 4.2 Multi-Expects Pairs

```yaml
pair:
  trigger: "api/{path}.py"
  expects:
    - "docs/api/{path}.md"
    - "openapi/{path}.yaml"
```

| ID | Scenario | Changed Files | Expected |
|----|----------|---------------|----------|
| CP-4.2.1 | All three | `["api/users.py", "docs/api/users.md", "openapi/users.yaml"]` | No fire |
| CP-4.2.2 | Trigger + one expect | `["api/users.py", "docs/api/users.md"]` | Fire (missing openapi) |
| CP-4.2.3 | Only trigger | `["api/users.py"]` | Fire (missing both) |
| CP-4.2.4 | Both expects only | `["docs/api/users.md", "openapi/users.yaml"]` | No fire |

## 5. Command Rules

### 5.1 Basic Commands

```yaml
- name: "Format Python"
  trigger: "**/*.py"
  action:
    command: "ruff format {file}"
    run_for: each_match
```

| ID | Scenario | Changed Files | Expected Behavior |
|----|----------|---------------|-------------------|
| CMD-5.1.1 | Single file | `["src/main.py"]` | Run `ruff format src/main.py` |
| CMD-5.1.2 | Multiple files | `["src/a.py", "src/b.py"]` | Run command for each file |
| CMD-5.1.3 | Non-matching | `["README.md"]` | No command run |

### 5.2 All Matches Mode

```yaml
action:
  command: "eslint --fix {files}"
  run_for: all_matches
```

| ID | Scenario | Changed Files | Expected Command |
|----|----------|---------------|------------------|
| CMD-5.2.1 | Multiple files | `["a.js", "b.js", "c.js"]` | `eslint --fix a.js b.js c.js` |
| CMD-5.2.2 | Single file | `["a.js"]` | `eslint --fix a.js` |

### 5.3 Command Errors

| ID | Scenario | Command Result | Expected |
|----|----------|----------------|----------|
| CMD-5.3.1 | Exit code 0 | Success | Pass |
| CMD-5.3.2 | Exit code 1 | Failure | Fail, show stderr |
| CMD-5.3.3 | Timeout | Command hangs | Fail, timeout error |
| CMD-5.3.4 | Command not found | Not executable | Fail, not found error |

## 6. Queue System

### 6.1 Queue Entry Lifecycle

| ID | Scenario | Initial State | Action | Final State |
|----|----------|---------------|--------|-------------|
| QS-6.1.1 | New trigger | (none) | Trigger detected | `.queued` |
| QS-6.1.2 | Safety suppression | `.queued` | Safety pattern matches | `.skipped` |
| QS-6.1.3 | Prompt addressed | `.queued` | Promise tag found | `.passed` |
| QS-6.1.4 | Command success | `.queued` | Command passes | `.passed` |
| QS-6.1.5 | Command failure | `.queued` | Command fails | `.failed` |
| QS-6.1.6 | Re-trigger same | `.passed` | Same files changed | No new entry |
| QS-6.1.7 | Re-trigger different | `.passed` | Different files | New `.queued` |

### 6.2 Hash Calculation

| ID | Scenario | Rule | Files | Baseline | Expected Hash Differs? |
|----|----------|--------|-------|----------|------------------------|
| QS-6.2.1 | Same everything | RuleA | `[a.py]` | commit1 | Same hash |
| QS-6.2.2 | Different files | RuleA | `[a.py]` vs `[b.py]` | commit1 | Different |
| QS-6.2.3 | Different baseline | RuleA | `[a.py]` | commit1 vs commit2 | Different |
| QS-6.2.4 | Different rule | RuleA vs RuleB | `[a.py]` | commit1 | Different |

### 6.3 Queue Cleanup

| ID | Scenario | Entry Age | Entry Status | Expected |
|----|----------|-----------|--------------|----------|
| QS-6.3.1 | Old queued | 25 hours | `.queued` | Pruned |
| QS-6.3.2 | Recent queued | 1 hour | `.queued` | Kept |
| QS-6.3.3 | Old passed | 2 hours | `.passed` | Pruned |
| QS-6.3.4 | Recent passed | 30 min | `.passed` | Kept |
| QS-6.3.5 | Old failed | 25 hours | `.failed` | Pruned |

### 6.4 Concurrent Access

| ID | Scenario | Process A | Process B | Expected |
|----|----------|-----------|-----------|----------|
| QS-6.4.1 | Simultaneous create | Creates entry | Creates entry | One wins, other no-ops |
| QS-6.4.2 | Create during eval | Creating | Evaluating existing | A creates new, B continues |
| QS-6.4.3 | Both evaluate same | Evaluating | Evaluating | File locking prevents race |

## 7. Output Management

### 7.1 Output Batching

| ID | Scenario | Triggered Rules | Expected Output |
|----|----------|-----------------|-----------------|
| OM-7.1.1 | Single rule | 1 | Full instructions |
| OM-7.1.2 | Two rules | 2 | Both, grouped |
| OM-7.1.3 | Many rules | 10 | Batched by rule name |
| OM-7.1.4 | Same rule multiple files | 3 Source/Test pairs | Grouped under single heading |

### 7.2 Output Format

| ID | Scenario | Input | Expected Format |
|----|----------|-------|-----------------|
| OM-7.2.1 | Correspondence violation | `src/foo.py` missing `tests/foo_test.py` | `src/foo.py → tests/foo_test.py` |
| OM-7.2.2 | Multiple same rule | 3 correspondence violations | Single heading, 3 lines |
| OM-7.2.3 | Instruction rule | Source files changed | Short summary + instructions |

## 8. Schema Validation

### 8.1 Required Fields

| ID | Scenario | Missing Field | Expected Error |
|----|----------|---------------|----------------|
| SV-8.1.1 | Missing name | `name` | "required field 'name'" |
| SV-8.1.2 | Missing detection mode | no `trigger`, `set`, or `pair` | "must have 'trigger', 'set', or 'pair'" |
| SV-8.1.3 | Missing markdown body | empty body (prompt action) | "instruction rules require markdown body" |
| SV-8.1.4 | Missing set patterns | `set` is empty | "set requires at least 2 patterns" |

### 8.2 Mutually Exclusive Fields

| ID | Scenario | Fields Present | Expected Error |
|----|----------|----------------|----------------|
| SV-8.2.1 | Both trigger and set | `trigger` + `set` | "use trigger, set, or pair" |
| SV-8.2.2 | Both trigger and pair | `trigger` + `pair` | "use trigger, set, or pair" |
| SV-8.2.3 | All detection modes | `trigger` + `set` + `pair` | "use only one detection mode" |

### 8.3 Pattern Validation

| ID | Scenario | Pattern | Expected Error |
|----|----------|---------|----------------|
| SV-8.3.1 | Unclosed brace | `src/{path.py` | "unclosed brace" |
| SV-8.3.2 | Empty variable | `src/{}.py` | "empty variable name" |
| SV-8.3.3 | Invalid chars in var | `src/{path/name}.py` | "invalid variable name" |
| SV-8.3.4 | Duplicate variable | `{path}/{path}.py` | "duplicate variable 'path'" |

### 8.4 Value Validation

| ID | Scenario | Field | Value | Expected Error |
|----|----------|-------|-------|----------------|
| SV-8.4.1 | Invalid compare_to | `compare_to` | `"yesterday"` | "must be base, default_tip, or prompt" |
| SV-8.4.2 | Invalid run_for | `run_for` | `"first_match"` | "must be each_match or all_matches" |

## 9. Integration Tests

### 9.1 End-to-End Instruction Rule

```
Given: Rule requiring tests for source changes
When: User modifies src/auth/login.py without test
Then:
  1. Stop hook fires
  2. Detector creates queue entry
  3. Evaluator returns instructions
  4. Agent sees rule message
  5. Agent adds tests
  6. Agent includes promise tag
  7. Next stop: queue entry marked passed
  8. Agent can stop successfully
```

### 9.2 End-to-End Command Rule

```
Given: Auto-format rule for Python files
When: User creates unformatted src/new_file.py
Then:
  1. Stop hook fires
  2. Detector creates queue entry
  3. Evaluator runs formatter
  4. Formatter modifies file
  5. Evaluator verifies idempotency
  6. Queue entry marked passed
  7. Agent notified of formatting changes
```

### 9.3 End-to-End Correspondence Set

```
Given: Source/test pairing rule
When: User modifies src/utils.py only
Then:
  1. Detector matches src/utils.py to pattern
  2. Resolver calculates expected tests/utils_test.py
  3. tests/utils_test.py not in changed files
  4. Queue entry created for incomplete correspondence
  5. Evaluator returns instructions
  6. Agent sees "expected tests/utils_test.py to change"
```

### 9.4 Multiple Rules Same File

```
Given:
  - Rule A: "Format Python" (command)
  - Rule B: "Test Coverage" (set)
  - Rule C: "README Accuracy" (instruction)
When: User modifies src/main.py
Then:
  1. All three rules trigger
  2. Command rule runs first
  3. Set rule checks for test
  4. Instruction rule prepares message
  5. Agent sees batched output with all requirements
```

### 9.5 Safety Pattern Across Rules

```
Given:
  - Rule A: trigger=src/**/*.py, safety=CHANGELOG.md
  - Rule B: trigger=src/**/*.py, safety=README.md
When: User modifies src/main.py and CHANGELOG.md
Then:
  1. Rule A: safety match, skipped
  2. Rule B: no safety match, fires
  3. Only Rule B instructions shown
```

## 10. Performance Tests

### 10.1 Large File Count

| ID | Scenario | File Count | Expected |
|----|----------|------------|----------|
| PT-10.1.1 | Many changed files | 100 | < 1s evaluation |
| PT-10.1.2 | Very many files | 1000 | < 5s evaluation |
| PT-10.1.3 | Pattern-heavy | 50 rules, 100 files | < 2s evaluation |

### 10.2 Queue Size

| ID | Scenario | Queue Entries | Expected |
|----|----------|---------------|----------|
| PT-10.2.1 | Moderate queue | 100 entries | < 100ms load |
| PT-10.2.2 | Large queue | 1000 entries | < 500ms load |
| PT-10.2.3 | Cleanup performance | 10000 old entries | < 1s cleanup |

### 10.3 Pattern Matching

| ID | Scenario | Patterns | Files | Expected |
|----|----------|----------|-------|----------|
| PT-10.3.1 | Simple patterns | 10 | 100 | < 10ms |
| PT-10.3.2 | Complex patterns | 50 with variables | 100 | < 50ms |
| PT-10.3.3 | Deep recursion | `**/**/**/*.py` | 1000 | < 100ms |

## Test Data Fixtures

### Sample Rule Files

Rules are stored as individual markdown files in `.deepwork/rules/`:

**`.deepwork/rules/readme-accuracy.md`**
```markdown
---
name: README Accuracy
trigger: src/**/*
safety: README.md
---
Please review README.md for accuracy.
```

**`.deepwork/rules/source-test-pairing.md`**
```markdown
---
name: Source/Test Pairing
set:
  - src/{path}.py
  - tests/{path}_test.py
---
Source and test should change together.
```

**`.deepwork/rules/api-documentation.md`**
```markdown
---
name: API Documentation
pair:
  trigger: api/{module}.py
  expects: docs/api/{module}.md
---
API changes need documentation.
```

**`.deepwork/rules/python-formatting.md`**
```markdown
---
name: Python Formatting
trigger: "**/*.py"
action:
  command: black {file}
  run_for: each_match
---
Auto-formats Python files with Black.
```

### Sample Queue Entry

```json
{
  "rule_name": "Source/Test Pairing",
  "rule_file": "source-test-pairing.md",
  "trigger_hash": "abc123def456",
  "status": "queued",
  "created_at": "2024-01-16T10:00:00Z",
  "evaluated_at": null,
  "baseline_ref": "abc123",
  "trigger_files": ["src/auth/login.py"],
  "expected_files": ["tests/auth/login_test.py"],
  "matched_files": [],
  "action_result": null
}
```

### Directory Structure for Tests

```
.deepwork/
├── rules/
│   ├── readme-accuracy.md
│   ├── source-test-pairing.md
│   ├── api-documentation.md
│   └── python-formatting.md
└── tmp/                         # GITIGNORED
    └── rules/
        └── queue/
            └── (queue entries created during tests)
```
