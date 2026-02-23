# Add DeepWork Native Reviews

## Objective

Ensure the project's top-level `.deepreview` file contains the two built-in DeepWork review rules: `suggest_new_reviews` and `prompt_best_practices`. These are general-purpose rules that benefit any project using DeepWork Reviews.

## Task

### 1. Read the example review instruction files

Read these files from the DeepWork plugin:
- `plugins/claude/example_reviews/prompt_best_practices.md`
- `plugins/claude/example_reviews/suggest_new_reviews.md`

These are the full, detailed versions of the two review instruction prompts. Read them to understand the review's intent, checklist, and tone. The inline YAML rules in steps 3 and 4 below are condensed versions — use the example files to fill in any gaps or to judge whether the inline version captures the key points.

For reference, this is how the DeepWork project's own `.deepreview` configures these two rules (using `instructions: { file: ... }` to point at the example files above):

```yaml
prompt_best_practices:
  description: "Review prompt/instruction markdown files for Anthropic prompt engineering best practices."
  match:
    include:
      - "**/CLAUDE.md"
      - "**/AGENTS.md"
      - ".claude/**/*.md"
      - ".deepwork/review/*.md"
      - ".deepwork/jobs/**/*.md"
  review:
    strategy: individual
    instructions:
      file: .deepwork/review/prompt_best_practices.md

suggest_new_reviews:
  description: "Analyze all changes and suggest new review rules that would catch issues going forward."
  match:
    include:
      - "**/*"
    exclude:
      - ".github/**"
  review:
    strategy: matches_together
    instructions:
      file: .deepwork/review/suggest_new_reviews.md
```

When creating rules for the target project, adapt the `match.include` patterns to its structure. The inline YAML in steps 3 and 4 uses inline `instructions:` text (suitable for projects that don't have the external instruction files), while the above uses `instructions: { file: ... }` references.

If the example files are not found (e.g., the plugin is installed differently), proceed using the inline YAML in steps 3 and 4 below.

### 2. Check the existing `.deepreview` file

Read the top-level `.deepreview` file if it exists. Check whether `suggest_new_reviews` and/or `prompt_best_practices` rules are already present.

- If both rules already exist with reasonable configurations, skip to the output step — no changes needed.
- If one or both are missing, proceed to add the missing rule(s).
- If a rule exists but has a substantially different configuration (wrong strategy, missing match patterns), update it to match the specification below.

### 3. Add the `prompt_best_practices` rule (if not present)

Add to `.deepreview`:

```yaml
prompt_best_practices:
  description: "Review prompt/instruction markdown files for Anthropic prompt engineering best practices."
  match:
    include:
      - "**/CLAUDE.md"
      - "**/AGENTS.md"
      - ".claude/**/*.md"
      - ".deepwork/review/*.md"
      - ".deepwork/jobs/**/*.md"
  review:
    strategy: individual
    instructions: |
      Review this markdown file as a prompt or instruction file, evaluating it
      against Anthropic's prompt engineering best practices.

      For each issue found, report:
      1. Location (section or line)
      2. Severity (Critical / High / Medium / Low)
      3. Best practice violated
      4. Description of the issue
      5. Suggested improvement

      Check for:
      - Clarity and specificity (concrete criteria vs vague language)
      - Structure and formatting (XML tags, headers, numbered lists for distinct sections)
      - Role and context (enough context for the AI, explicit assumptions)
      - Examples for complex/nuanced tasks
      - Output format specification
      - Prompt anti-patterns (contradictions, instruction overload, buried critical instructions)
      - Variable/placeholder clarity

      Use judgment proportional to the file's complexity. A short, focused
      instruction for a simple task does not need few-shot examples or XML tags.
      Do not flag issues for best practices that are irrelevant to the file's purpose.
```

Adapt the `match.include` patterns to the project if needed. Check for directories containing `.md` files that appear to be AI instruction files (e.g., `.gemini/`, `.cursorrules`, custom agent directories). If found, add those patterns too. You may add both missing rules in a single edit to the `.deepreview` file. The patterns above are the baseline.

### 4. Add the `suggest_new_reviews` rule (if not present)

Add to `.deepreview`:

```yaml
suggest_new_reviews:
  description: "Analyze all changes and suggest new review rules that would catch issues going forward."
  match:
    include:
      - "**/*"
    exclude:
      - ".github/**"
  review:
    strategy: matches_together
    instructions: |
      Analyze the changeset to determine whether any new DeepWork review rules
      should be added.

      1. Call get_configured_reviews to see all currently configured review rules.
      2. Read README_REVIEWS.md if present for context on review capabilities.
      3. For each change, consider:
         - Did this change introduce a type of issue a review rule could catch?
         - Is there a pattern likely to recur?
         - Would an existing rule benefit from a small scope expansion?
      4. Be extremely conservative. Only suggest rules that are:
         - Extremely narrow (targets 1 specific file or small bounded set)
         - Slight additions to existing rules (adding a glob to an include list)
         - Catches an issue likely to recur and worth ongoing cost
      5. If no rules are warranted, say so. An empty suggestion list is valid.
```

### 5. Validate

Ensure the `.deepreview` file is valid YAML. Ensure both rules have all required fields: `description`, `match.include`, `review.strategy`, `review.instructions`.

## Output

### deepreview_file

The top-level `.deepreview` file containing both native review rules (alongside any pre-existing rules). If no changes were required (both rules already existed with correct configuration), still provide the `.deepreview` file path as the output to confirm the check was completed.

## Quality Criteria

- The `.deepreview` file exists at the repository root and is valid YAML
- A `prompt_best_practices` rule is present with `strategy: individual` and match patterns covering prompt/instruction files
- A `suggest_new_reviews` rule is present with `strategy: matches_together` and broad match patterns
- Pre-existing rules in the file are preserved unchanged
- Match patterns are adapted to the project's actual structure (not just copy-pasted defaults)
