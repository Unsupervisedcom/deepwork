# Apply Review Rule

## Objective

Create or update the `.deepreview` file based on the approved dependency analysis from the previous step.

## Task

Read the dependency analysis, then either create a new rule or extend an existing rule in the `.deepreview` file so that changes to the identified source files trigger a documentation freshness review.

### Process

1. **Read the dependency analysis**
   - Read the analysis file from the previous step
   - Extract: rule name, match patterns, strategy decision, existing rule assessment

2. **Read the current .deepreview file**
   - If it exists, read and parse its contents
   - If it doesn't exist, you'll create a new file

3. **Apply the rule based on the analysis recommendation**

   **If creating a new rule** (no overlapping rule found):
   - Add a new top-level key to the `.deepreview` file using the recommended rule name
   - Set the `description` to clearly state what documentation this rule protects
   - Set `match.include` to the recommended glob patterns
   - Set `match.exclude` if the analysis recommended exclusions
   - Set `review.strategy` to the recommended strategy
   - Set `review.additional_context.unchanged_matching_files` to `true`
   - Write clear `review.instructions` (see instruction guidelines below)

   **If extending an existing rule** (overlapping rule found):
   - Read the existing rule's instructions
   - Add the new documentation file to the list of monitored documents in the instructions
   - Add the documentation file path to `match.include` if not already covered by existing patterns
   - Ensure `review.additional_context.unchanged_matching_files` is `true`
   - Do NOT change the existing rule's match patterns for source files unless the analysis specifically recommends it
   - When updating the instructions text, follow the wide (multi-doc) template in Step 4 to ensure all monitored documents are listed

4. **Write the review instructions**

   Replace bracketed placeholders in the templates below with values from the dependency analysis:
   - `[doc_path]` — the documentation file path from the analysis
   - `[doc_path_1]`, `[doc_path_2]` — multiple documentation file paths (for wide rules)
   - `[watched area description]` — a short description of the source file area (e.g., "src/deepwork/core/")

   Use the narrow (single-doc) template when the analysis recommends a narrow strategy with a single documentation file. Use the wide (multi-doc) template when the analysis recommends a wide strategy or when multiple documents are monitored by one rule.

   The review instructions should tell the reviewer to:
   - Read the specified documentation file(s)
   - Compare the document's claims against the changed source files
   - Flag any sections of the document that may be outdated or inaccurate
   - Suggest specific updates if possible

   **Instruction template for a narrow (single-doc) rule**:
   ```
   When source files change, check whether [doc_path] needs updating.

   Read [doc_path] and compare its content against the changed files.
   Flag any sections that are now outdated or inaccurate due to the changes.
   If the documentation file itself was changed, verify the updates are correct
   and consistent with the source files.
   ```

   **Instruction template for a wide (multi-doc) rule**:
   ```
   When source files in [watched area description] change, check whether the
   following documentation files need updating:
   - [doc_path_1]
   - [doc_path_2]

   Read each documentation file and compare its content against the changed
   source files. Flag any sections that are now outdated or inaccurate.
   If a documentation file itself was changed, verify the updates are correct
   and consistent with the source files.
   ```

5. **Validate the .deepreview file**
   - Ensure valid YAML syntax
   - Ensure all required fields are present: description, match.include, review.strategy, review.instructions
   - Ensure the rule name follows naming conventions (lowercase, underscores/hyphens)
   - Ensure `unchanged_matching_files: true` is set
   - If any validation check fails, fix the issue before proceeding. Do not output an invalid `.deepreview` file.

## Output Format

### deepreview_file

The `.deepreview` file at the repository root with the new or updated rule.

**Example of a new narrow rule added to an existing .deepreview file**:
```yaml
# ... existing rules above ...

update_cli_reference:
  description: "Ensure CLI reference docs stay current when CLI source files change."
  match:
    include:
      - "src/deepwork/cli/serve.py"
      - "src/deepwork/cli/hook.py"
      - "src/deepwork/cli/__init__.py"
      - "docs/cli-reference.md"
  review:
    strategy: matches_together
    instructions: |
      When CLI source files change, check whether docs/cli-reference.md needs updating.

      Read docs/cli-reference.md and compare its content against the changed files.
      Flag any sections that are now outdated or inaccurate due to the changes.
      If the documentation file itself was changed, verify the updates are correct
      and consistent with the source files.
    additional_context:
      unchanged_matching_files: true
```

**Example of a wide rule protecting multiple docs**:
```yaml
update_documents_relating_to_src_core:
  description: "Ensure documentation stays current when core source files change."
  match:
    include:
      - "src/deepwork/core/**"
      - "doc/architecture.md"
      - "doc/internals.md"
  review:
    strategy: matches_together
    instructions: |
      When source files in src/deepwork/core/ change, check whether the following
      documentation files need updating:
      - doc/architecture.md
      - doc/internals.md

      Read each documentation file and compare its content against the changed
      source files. Flag any sections that are now outdated or inaccurate.
      If a documentation file itself was changed, verify the updates are correct
      and consistent with the source files.
    additional_context:
      unchanged_matching_files: true
```

**Example of extending an existing rule** (adding a doc to monitored list):
```yaml
# Before: existing rule monitored only doc/architecture.md
# After: now also monitors doc/api-reference.md

update_documents_relating_to_src_core:
  description: "Ensure documentation stays current when core source files change."
  match:
    include:
      - "src/deepwork/core/**"
      - "doc/architecture.md"
      - "doc/api-reference.md"    # newly added
  review:
    strategy: matches_together
    instructions: |
      When source files in src/deepwork/core/ change, check whether the following
      documentation files need updating:
      - doc/architecture.md
      - doc/api-reference.md

      Read each documentation file and compare its content against the changed
      source files. Flag any sections that are now outdated or inaccurate.
    additional_context:
      unchanged_matching_files: true
```

## Quality Criteria

- The rule faithfully implements the approved dependency analysis — same patterns, strategy, and naming
- The `.deepreview` file is valid YAML
- All required fields are present (description, match.include, review.strategy, review.instructions)
- Review instructions clearly reference the documentation file(s) being protected
- `additional_context.unchanged_matching_files` is set to `true`
- If extending an existing rule, existing patterns are preserved and the doc is cleanly added

## Context

This step applies the plan from the analysis step. The .deepreview rule will trigger automatically during code reviews when matched files change, prompting a reviewer to check whether the protected documentation is still accurate. The `unchanged_matching_files: true` setting is essential — without it, the reviewer can't see the documentation file when only source files changed.
