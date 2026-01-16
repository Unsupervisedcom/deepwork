# Define Policy

## Objective

Create or update policies to enforce team guidelines, documentation requirements, file correspondences, or automated commands when specific files change.

## Task

Guide the user through defining a new policy by asking structured questions. **Do not create the policy without first understanding what they want to enforce.**

**Important**: Use the AskUserQuestion tool to ask structured questions when gathering information from the user.

---

## Step 1: Understand the Policy Purpose

Ask structured questions to understand what the user wants to enforce:

1. **What should this policy enforce?**
   - Documentation sync? Security review? File correspondence? Code formatting?

2. **What files trigger this policy?**
   - Which files/directories, when changed, should trigger action?

3. **What should happen when the policy fires?**
   - Show instructions to the agent? Run a command automatically?

---

## Step 2: Choose Detection Mode

Policies support three detection modes:

### Trigger/Safety (Default)
Fire when trigger patterns match AND safety patterns don't.

**Use for**: General checks like "source changed, verify README"

```yaml
trigger: "app/config/**/*"
safety: "docs/install_guide.md"
```

### Set (Bidirectional Correspondence)
Fire when files matching one pattern change but corresponding files don't.

**Use for**: Source/test pairing, i18n files, paired documentation

```yaml
set:
  - src/{path}.py
  - tests/{path}_test.py
```

If `src/utils/helper.py` changes, expects `tests/utils/helper_test.py` to also change.

### Pair (Directional Correspondence)
Fire when trigger files change but expected files don't. Changes to expected files alone don't trigger.

**Use for**: API code requires docs (but docs changes don't require API changes)

```yaml
pair:
  trigger: src/api/{name}.py
  expects: docs/api/{name}.md
```

### Variable Pattern Syntax

- `{path}` - Matches multiple path segments (e.g., `foo/bar/baz`)
- `{name}` - Matches a single segment (e.g., `helper`)

---

## Step 3: Choose Action Type

### Prompt (Default)
Show instructions to the agent. The markdown body becomes the instructions.

```markdown
---
name: Security Review
trigger: "src/auth/**/*"
---
Please review for hardcoded credentials and validate input handling.
```

### Command
Run an idempotent command automatically. No markdown body needed.

```markdown
---
name: Format Python
trigger: "**/*.py"
action:
  command: "ruff format {file}"
  run_for: each_match
---
```

**Command variables**:
- `{file}` - Current file being processed
- `{files}` - Space-separated list of all matching files
- `{repo_root}` - Repository root path

**run_for options**:
- `each_match` - Run command once per matching file
- `all_matches` - Run command once with all files

---

## Step 4: Define Optional Settings

### compare_to (Optional)
Controls what baseline is used for detecting changed files:

- `base` (default) - Changes since branch diverged from main/master
- `default_tip` - Changes compared to current main/master tip
- `prompt` - Changes since the last prompt submission

Most policies should use the default (`base`).

---

## Step 5: Create the Policy File

### File Location
Create: `.deepwork/policies/[policy-name].md`

Use kebab-case for filename (e.g., `source-test-pairing.md`, `format-python.md`)

### Examples

**Trigger/Safety with Prompt:**
```markdown
---
name: Update Install Guide
trigger: "app/config/**/*"
safety: "docs/install_guide.md"
---
Configuration files have changed. Please review docs/install_guide.md
and update installation instructions if needed.
```

**Set (Bidirectional) with Prompt:**
```markdown
---
name: Source/Test Pairing
set:
  - src/{path}.py
  - tests/{path}_test.py
---
When source files change, corresponding test files should also change.
Please create or update tests for the modified source files.
```

**Pair (Directional) with Prompt:**
```markdown
---
name: API Documentation
pair:
  trigger: src/api/{name}.py
  expects: docs/api/{name}.md
---
API code has changed. Please update the corresponding documentation.
```

**Command Action:**
```markdown
---
name: Format Python Files
trigger: "**/*.py"
action:
  command: "ruff format {file}"
  run_for: each_match
---
```

**Multiple Trigger Patterns:**
```markdown
---
name: Security Review
trigger:
  - "src/auth/**/*"
  - "src/security/**/*"
safety:
  - "SECURITY.md"
  - "docs/security_audit.md"
---
Authentication or security code has been changed. Please review for:
1. Hardcoded credentials or secrets
2. Input validation issues
3. Access control logic
```

---

## Step 6: Verify the Policy

After creating the policy:

1. **Check YAML frontmatter syntax** - Ensure valid YAML
2. **Verify detection mode is appropriate** - trigger/safety vs set vs pair
3. **Test patterns match intended files** - Check glob/variable patterns
4. **Review instructions/command** - Ensure they're actionable
5. **Check for conflicts** - Ensure no overlap with existing policies

---

## Pattern Reference

### Glob Patterns
- `*` - Matches any characters within a single path segment
- `**` - Matches across multiple path segments (recursive)
- `?` - Matches a single character

### Variable Patterns
- `{path}` - Captures multiple segments: `src/{path}.py` matches `src/a/b/c.py` → path=`a/b/c`
- `{name}` - Captures single segment: `src/{name}.py` matches `src/utils.py` → name=`utils`

### Common Examples
- `src/**/*.py` - All Python files in src (recursive)
- `app/config/**/*` - All files in app/config
- `*.md` - Markdown files in root only
- `**/*.test.ts` - All test files anywhere
- `src/{path}.ts` ↔ `tests/{path}.test.ts` - Source/test pairs

---

## Output Format

Create: `.deepwork/policies/[policy-name].md`

---

## Quality Criteria

- Asked structured questions to understand requirements
- Chose appropriate detection mode (trigger/safety, set, or pair)
- Chose appropriate action type (prompt or command)
- Policy name is clear and descriptive
- Patterns accurately match intended files
- Instructions or command are actionable
- YAML frontmatter is valid

---

## Context

Policies are evaluated automatically when you finish working. The system:

1. Loads policies from `.deepwork/policies/`
2. Detects changed files based on `compare_to` setting
3. Evaluates each policy based on its detection mode
4. For **command** actions: Runs the command automatically
5. For **prompt** actions: Shows instructions if policy fires

Mark a policy as addressed by including `<promise>✓ Policy Name</promise>` in your response.
