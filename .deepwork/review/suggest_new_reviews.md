# Suggest New Review Rules

You are reviewing a changeset to determine whether any new DeepWork review rules should be added to catch issues found in these changes going forward.

## Steps

1. **Get current rules**: Call `mcp__plugin_deepwork_deepwork__get_configured_reviews` to see all currently configured review rules. Understand what's already covered.

2. **Read the reviews README**: Read `README_REVIEWS.md` in the repository root to understand the full range of review capabilities and rule structures.

3. **Analyze the changeset**: Look at all the changed files. For each change, consider:
   - Did this change introduce a type of issue that a review rule could catch?
   - Is there a pattern here that's likely to recur?
   - Would an existing rule benefit from a small scope expansion to cover a new file type?

4. **Write new rules directly**: For each rule you decide to create:
   - If it's a **new rule**: add it to the appropriate `.deepreview` file with full YAML
   - If it's an **addition to an existing rule's `include` list**: edit the existing rule in-place
   - If the rule needs a dedicated instruction file: create it in `.deepwork/review/`

5. **Output**: List each new rule or modification you made, with its name and description. This is your only deliverable.

## CRITICAL: Be Extremely Conservative

New rules have ongoing cost -- every future review run spawns agents for them. Only suggest rules that meet **at least one** of these criteria:

1. **Extremely narrow** (targets 1 specific file or a very small, bounded set) -- cost is near-zero because it rarely triggers
2. **Slight addition to an existing rule** (e.g., adding a glob pattern to an existing `include` list) -- no new review agent spawned, just widens coverage of one that already runs
3. **Catches an issue that is likely to recur** and is worth the ongoing cost of a wider rule -- something that actually bit us in this changeset or a known class of mistake

If the changeset is clean and doesn't suggest any valuable new rules, say so and output nothing. Do not invent rules just to have output. An empty suggestion list is a perfectly valid result.

### Example: Expanding an existing rule's include list

If a new agent-oriented markdown file was created (e.g., `.claude/agents/researcher.md`), you could add its pattern to the existing `prompt_best_practices` rule:

```yaml
prompt_best_practices:
  match:
    include:
      - ...existing patterns...
      - ".claude/agents/*.md"    # New: agent definitions are prompt-heavy files
```

This costs almost nothing -- it adds files to an existing review that already runs -- but catches prompt quality issues in a file type that wasn't previously covered. That's the ideal kind of suggestion.
