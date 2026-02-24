## Validating Requirements with Review Rules

When a project has formal requirements (e.g., RFC 2119 "MUST/SHOULD" specs), each requirement needs validation. Some requirements are **deterministic** and belong in automated tests. Others require **judgment** and belong in review rules. Choosing the right mechanism is critical — the wrong choice either creates false confidence or wastes reviewer effort.

### When to use tests vs. review rules

**Use automated tests** when the requirement specifies a concrete, machine-verifiable fact:
- "Config file MUST exist at path X" → `assert path.exists()`
- "The `name` field MUST be `deepwork`" → `assert data["name"] == "deepwork"`
- "Arguments MUST include `--platform claude`" → `assert "--platform" in args`

**Use review rules** when evaluating the requirement requires reading comprehension or judgment:
- "Skill MUST instruct the agent to launch tasks in parallel"
- "Skill MUST instruct the agent to reuse existing rules rather than creating duplicates"
- "Documentation MUST stay in sync with the code it describes"

> **Key distinction:** If you can verify the requirement by checking an exact value, path, or structure, use a test. If you need to _read and understand_ whether prose, code, or documentation adequately satisfies the requirement's intent, use a review rule.

### Anti-patterns

**Bad: keyword tests for judgment requirements.** A test that checks `"parallel" in content.lower()` to validate "MUST launch tasks in parallel" is a keyword search pretending to be a verification. The word "parallel" could appear in an unrelated context, be negated ("do NOT run in parallel"), or be absent while the instruction clearly conveys parallel execution through different wording. **Use a review rule instead** — a reviewer can actually read the instructions and evaluate whether they adequately direct parallel execution.

```yaml
# BAD — this is a test pretending to be deterministic:
#   assert "reuse" in content.lower() or "existing" in content.lower()
#
# GOOD — a review rule that evaluates instruction quality:
skill_instruction_quality:
  description: "REQ-001.5.4: Verify skill instructs agent to reuse existing rules."
  match:
    include:
      - "plugins/skills/configure_reviews/SKILL.md"
  review:
    strategy: individual
    instructions: |
      REQ-001.5.4 requires: "The skill MUST instruct the agent to reuse
      existing review rules and instructions where possible rather than
      creating duplicates."
      Read the skill file and evaluate whether the instructions clearly
      convey a preference for reuse over duplication.
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
  .4.4: "MUST launch review tasks in parallel"                         → REVIEW RULE (judgment)
  .4.5: "MUST auto-apply obvious fixes"                                → REVIEW RULE (judgment)
  .4.6: "MUST present trade-offs via AskUserQuestion"                  → TEST (specific identifier in content)
```

The tests verify structural facts (file exists, field has value, identifier present). The review rules evaluate whether the _instructions_ adequately convey behavioral directives to an AI agent.