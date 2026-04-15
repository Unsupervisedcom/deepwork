## .deepreview File Format

YAML file at the repository root. Each top-level key is a rule name:

```yaml
rule_name:
  description: "Short description of what this rule checks."
  match:
    include:
      - "glob/pattern/**"
    exclude:           # optional
      - "glob/to/exclude/**"
  review:
    strategy: individual | matches_together | all_changed_files
    instructions: |
      Inline review instructions for the reviewer.
    # OR reference an external file:
    # instructions:
    #   file: path/to/instructions.md
    additional_context:   # optional
      unchanged_matching_files: true   # include matching files even if not changed
      all_changed_filenames: true      # include list of all changed files
```

## Key Concepts

- **match.include**: Glob patterns that trigger this rule when matched files change
- **match.exclude**: Glob patterns to skip (optional). Files matching .gitignore
  rules (e.g. `__pycache__/`, `node_modules/`, `.env`) are excluded automatically,
  so they don't need to be listed here.
- **strategy**: How to batch reviews:

  | Strategy | Reviewer sees | Best for |
  |----------|--------------|----------|
  | `individual` | One file at a time | Per-file linting, style checks |
  | `matches_together` | All matched files together | Cross-file consistency, migration safety |
  | `all_changed_files` | _Every_ changed file (tripwire) | Security audits, broad impact analysis |
- **additional_context.unchanged_matching_files**: When true, the reviewer gets files
  matching include patterns even if they didn't change in this PR. Critical for
  document freshness checks — lets the reviewer see the doc even when only source
  files changed.

## Rule Naming Conventions

- Narrow rules (specific to one doc): `update_<doc_name_without_extension>`
- Wide rules (protecting multiple docs): `update_documents_relating_to_<watched_path_description>`
