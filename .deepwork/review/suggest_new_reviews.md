# Suggest New Review Rules and DeepSchemas

You are reviewing a changeset to determine whether any new DeepWork review rules or DeepSchemas should be added to catch issues found in these changes going forward.

## Three enforcement mechanisms

1. **`.deepreview` rules** — review rules that run during `/review` and quality gates. Best for requirements that apply broadly across many files of a type (e.g., "all prompts MUST use the terms X, Y, and Z") or cross-file consistency checks. Use these when the requirement is general and applies to a glob pattern of files.

2. **Named DeepSchemas** (`.deepwork/schemas/<name>/deepschema.yml`) — rich schemas for recurring file types matched by glob patterns. Best when a class of files shares structural or content requirements. Named DeepSchemas automatically generate review rules AND provide write-time validation.

3. **Anonymous DeepSchemas** (`.deepschema.<filename>.yml`) — single-file schemas placed next to the file they govern. Best for requirements specific to one file's behavior or content (e.g., "the error message in situation X MUST include a suggestion for how to fix the problem"). These keep the requirement co-located with the implementation and provide both write-time validation and review-time checks.

**Choosing between them:**
- Requirement applies to many files matching a pattern → `.deepreview` rule or named DeepSchema
- Requirement is about a specific file's content or behavior → anonymous DeepSchema
- Requirement is about cross-file consistency or process → `.deepreview` rule

## Steps

1. **Get current rules and schemas**: Call `mcp__plugin_deepwork_deepwork__get_configured_reviews` to see all currently configured review rules (including DeepSchema-generated ones). Also call `mcp__plugin_deepwork_deepwork__get_named_schemas` to see existing DeepSchemas. Understand what's already covered.

2. **Read the reviews README**: Read `@README_REVIEWS.md` (in the repository root) to understand the full range of review capabilities and rule structures.

3. **Analyze the changeset**: Look at all the changed files. For each change, consider:
   - Did this change introduce a type of issue that a review rule or DeepSchema could catch?
   - Is there a pattern here that's likely to recur?
   - Would an existing rule benefit from a small scope expansion to cover a new file type?
   - Is there a file type that would benefit from a named DeepSchema (structural requirements shared across many files)?
   - Is there a specific file with behavioral or content requirements that would benefit from an anonymous DeepSchema placed next to it?

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
