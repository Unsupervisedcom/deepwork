# Add Documentation Update Rules

## Objective

Find documentation files in the project that describe the project itself, and create `.deepreview` rules to keep each one up-to-date when related source files change.

## Task

### 1. Search for project documentation files

Search the repository for files that document the project itself — its architecture, APIs, setup, configuration, usage, or internals. Common locations and patterns:

- `README.md`, `README*.md` at the root or in key directories
- `doc/`, `docs/`, `documentation/` directories
- `ARCHITECTURE.md`, `CONTRIBUTING.md`, `CHANGELOG.md`
- `*.md` files in the project root that describe the project
- API documentation, design documents, runbooks

**Exclude** documentation that describes external things (e.g., notes about a third-party API, research documents, user-facing help content that doesn't describe the project's own code or structure). Also exclude auto-generated documentation.

If no project documentation files are found, report that in the output and finish.

### 2. Check existing rules

Read all `.deepreview` files in the project. Note which documentation files already have update rules protecting them. Skip any documentation file that is already covered by an existing rule.

### 3. For each unprotected documentation file

Launch the `add_document_update_rule` workflow as a nested workflow (via `start_workflow`) for each documentation file that needs a rule. Pass the file path as the `doc_path` input.

**Important**: Run each `add_document_update_rule` invocation in a separate Task agent so they can execute in parallel. Each Task should:
1. Call `start_workflow` with `job_name: "deepwork_reviews"`, `workflow_name: "add_document_update_rule"`, and the `doc_path` as the goal
2. Follow the workflow steps (analyze_dependencies, apply_rule)
3. Complete the nested workflow

### 4. Review the resulting rules for scope efficiency

After all `add_document_update_rule` workflows complete, read all `.deepreview` files and review the rules that were created. Consider:

- Are there multiple narrow rules whose `match.include` patterns substantially overlap? If so, they should be merged into a single wider rule that covers all the documentation files together.
- Are there rules with overly broad triggers that will fire on many unrelated changes? Narrow them.
- The goal is the minimum number of rules that covers all documentation files with appropriately scoped triggers. Having more separate reviews with narrower scope is not always more efficient than a slightly wider, shared review — each review spawns a sub-agent with material overhead.

Make any merging or narrowing adjustments directly.

## Output

### documentation_files_found

A markdown file listing all project documentation files that were found, whether each was already protected by an existing rule or newly protected, and the rule name covering it. Save this to `.deepwork/tmp/documentation_files_found.md`.

### deepreview_files

All `.deepreview` files that were created or modified.

## Quality Criteria

- All project documentation files describing the project itself are identified
- External documentation and auto-generated docs are excluded
- Each unprotected doc file has a corresponding rule via the `add_document_update_rule` workflow
- The set of rules is efficient — overlapping narrow rules have been merged where appropriate
- Trigger scope for each rule is as narrow as possible while still catching relevant changes
- No documentation file is left unprotected unless it was already covered
