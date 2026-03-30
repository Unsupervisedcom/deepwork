# Suggest New Review Rules and DeepSchemas

You are reviewing a changeset to determine whether any new DeepWork review rules or DeepSchemas should be added to catch issues found in these changes going forward.

## Two enforcement mechanisms

1. **`.deepreview` rules** — review rules that run during `/review` and quality gates. Best for cross-file checks, process enforcement, and subjective quality criteria.
2. **DeepSchemas** — rich file-level schemas (`.deepwork/schemas/<name>/deepschema.yml` for named, `.deepschema.<filename>.yml` for anonymous). Best for per-file structural requirements, JSON Schema validation, and bash verification commands. DeepSchemas automatically generate review rules AND provide write-time validation hooks.

Use DeepSchemas when the issue is about a specific file type having structural or content requirements. Use `.deepreview` rules when the issue is about cross-file consistency, process adherence, or subjective review.

## Steps

1. **Get current rules and schemas**: Call `mcp__plugin_deepwork_deepwork__get_configured_reviews` to see all currently configured review rules (including DeepSchema-generated ones). Also call `mcp__plugin_deepwork_deepwork__get_named_schemas` to see existing DeepSchemas. Understand what's already covered.

2. **Read the reviews README**: Read `@README_REVIEWS.md` (in the repository root) to understand the full range of review capabilities and rule structures.

3. **Analyze the changeset**: Look at all the changed files. For each change, consider:
   - Did this change introduce a type of issue that a review rule or DeepSchema could catch?
   - Is there a pattern here that's likely to recur?
   - Would an existing rule benefit from a small scope expansion to cover a new file type?
   - Is there a file type that would benefit from a DeepSchema (structural requirements, JSON Schema, or bash verification)?

4. **Write new rules or schemas directly**: For each rule you decide to create:
   - If it's a **new `.deepreview` rule**: add it to the appropriate `.deepreview` file with full YAML
   - If it's an **addition to an existing rule's `include` list**: edit the existing rule in-place
   - If the rule needs a dedicated instruction file: create it in `.deepwork/review/`
   - If it's a **new named DeepSchema**: create `.deepwork/schemas/<name>/deepschema.yml` with `summary`, `matchers`, and `requirements`
   - If it's a **new anonymous DeepSchema**: create `.deepschema.<filename>.yml` next to the target file

5. **Output**: After writing rules/schemas to their files, list each new rule or schema you created, with just its name and description. This summary is your final report.

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
