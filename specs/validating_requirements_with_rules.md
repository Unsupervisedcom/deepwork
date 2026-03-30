## Validating Requirements with Review Rules

When a project has formal requirements (e.g., RFC 2119 "MUST/SHOULD" specs), each requirement needs validation. Some requirements are **deterministic** and belong in automated tests. Others require **judgment** and belong in review rules. Choosing the right mechanism is critical — the wrong choice either creates false confidence or wastes reviewer effort.

### When to use tests vs. review rules

**Use automated tests** when the requirement specifies a concrete, machine-verifiable fact:
- "Config file MUST exist at path X" → `assert path.exists()`
- "The `name` field MUST be `deepwork`" → `assert data["name"] == "deepwork"`
- "Arguments MUST include `--platform claude`" → `assert "--platform" in args`

**Use `.deepreview` rules** when evaluating the requirement requires judgment AND applies broadly across many files:
- "All prompts MUST use the terms X, Y, and Z" — a standard that applies to every matching file
- "Documentation MUST stay in sync with the code it describes" — cross-file consistency

**Use anonymous DeepSchemas** (`.deepschema.<filename>.yml`) when the requirement requires judgment but targets a specific file:
- "Skill MUST instruct the agent to launch tasks in parallel" — place the requirement in a `.deepschema.SKILL.md.yml` next to the skill file
- "The error message in situation X MUST include a suggestion for how to fix the problem" — place it in a `.deepschema` for the implementing file
- "Skill MUST instruct the agent to reuse existing rules rather than creating duplicates" — specific to one skill file

Anonymous DeepSchemas keep requirements co-located with the file they govern and provide both write-time validation and review-time checks.

> **Key distinction:** If you can verify the requirement by checking an exact value, path, or structure, use a test. If you need to _read and understand_ whether content adequately satisfies the requirement's intent, use a `.deepreview` rule (for broad patterns) or an anonymous DeepSchema (for specific files).

### Anti-patterns

**Bad: keyword tests for judgment requirements.** A test that checks `"parallel" in content.lower()` to validate "MUST launch tasks in parallel" is a keyword search pretending to be a verification. The word "parallel" could appear in an unrelated context, be negated ("do NOT run in parallel"), or be absent while the instruction clearly conveys parallel execution through different wording. **Use a review rule instead** — a reviewer can actually read the instructions and evaluate whether they adequately direct parallel execution.

```python
# BAD — this is a test pretending to be deterministic:
assert "reuse" in content.lower() or "existing" in content.lower()
```

```yaml
# GOOD — an anonymous DeepSchema next to the skill file that evaluates
# instruction quality. Place this file at:
#   plugins/skills/configure_reviews/.deepschema.SKILL.md.yml
requirements:
  instructs-reuse: >
    The skill MUST instruct the agent to reuse existing review rules
    and instructions where possible rather than creating duplicates.
    (REQ-001.5.4)
```

**Bad: review rules for machine-verifiable requirements.** A review rule that asks a reviewer to "check whether plugin.json contains a `name` field set to `deepwork`" is wasting judgment on something a test can verify exactly. **Use a test instead.**

```python
# BAD — this belongs in a review rule, not a test:
def test_skill_instructs_reuse(self):
    content = skill_path.read_text()
    assert "reuse" in content.lower()  # Fragile keyword match!

# GOOD — this is a genuinely deterministic check:
def test_manifest_name(self):
    data = json.loads(manifest_path.read_text())
    assert data["name"] == "deepwork"  # Exact value comparison
```

### Example: requirement with both tests and review rules

A single requirement section often has a mix of deterministic and judgment sub-requirements. Split them accordingly:

```
REQ-001.4: Review Skill
  .4.1: "MUST provide skill at plugins/claude/skills/review/SKILL.md"  → TEST (file exists)
  .4.2: "MUST be invocable as /review"                                 → TEST (frontmatter name == "review")
  .4.3: "MUST use MCP review tools"                                    → TEST (specific identifier in content)
  .4.4: "MUST launch review tasks in parallel"                         → ANONYMOUS DEEPSCHEMA (judgment, specific file)
  .4.5: "MUST auto-apply obvious fixes"                                → ANONYMOUS DEEPSCHEMA (judgment, specific file)
  .4.6: "MUST present trade-offs via AskUserQuestion"                  → TEST (specific identifier in content)
```

The tests verify structural facts (file exists, field has value, identifier present). The judgment-based requirements targeting a specific file use anonymous DeepSchemas (`.deepschema.SKILL.md.yml` placed next to the skill file). Broad judgment-based requirements that span many files use `.deepreview` rules.