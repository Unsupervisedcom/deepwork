# Add DeepWork Native Reviews

## Objective

Ensure the project's top-level `.deepreview` file contains the two built-in DeepWork review rules: `suggest_new_reviews` and `prompt_best_practices`. These are general-purpose rules that benefit any project using DeepWork Reviews.

## Task

### 1. Read the example review instruction files

Read the example review instruction files shipped with the DeepWork plugin to understand what each rule does:

- `example_reviews/suggest_new_reviews.md` — Instructions for a rule that analyzes changesets and suggests new review rules
- `example_reviews/prompt_best_practices.md` — Instructions for a rule that reviews prompt/instruction files against Anthropic best practices

These files are the canonical examples. Use them as reference when writing the inline rule instructions below.

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

Adapt the `match.include` patterns to the project if needed — for example, if the project has prompt files in other locations (e.g., `.gemini/`, custom agent directories), add those patterns too. The patterns above are the baseline.

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

The top-level `.deepreview` file containing both native review rules (alongside any pre-existing rules).

## Quality Criteria

- The `.deepreview` file exists at the repository root and is valid YAML
- A `prompt_best_practices` rule is present with `strategy: individual` and match patterns covering prompt/instruction files
- A `suggest_new_reviews` rule is present with `strategy: matches_together` and broad match patterns
- Pre-existing rules in the file are preserved unchanged
- Match patterns are adapted to the project's actual structure (not just copy-pasted defaults)
