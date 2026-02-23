# Add Language-Specific Code Review Rules

## Objective

If the project contains code, create language-specific review guidelines and `.deepreview` rules so that code changes are reviewed against the project's own conventions and best practices.

## Task

### 1. Detect languages in the project

Scan the repository to identify which programming languages are used. Use file extensions and directory structure:

- `*.py` → Python
- `*.js`, `*.jsx`, `*.ts`, `*.tsx` → JavaScript/TypeScript
- `*.go` → Go
- `*.rs` → Rust
- `*.rb` → Ruby
- `*.java`, `*.kt` → Java/Kotlin
- `*.swift` → Swift
- `*.c`, `*.h`, `*.cpp`, `*.hpp` → C/C++

For other languages not listed, use the same pattern: identify by file extension and include any language with 3 or more files.

Count files per language to gauge significance. Skip languages with only 1-2 files (likely config or tooling, not project code). If the project has no code files, report that and finish.

### 2. Gather conventions for each language

For each significant language in the project, build a conventions/review guidelines document. Layer information from these sources in priority order:

#### a. Existing coding standards files

Search for existing guidelines the project already has:
- Linter configs (`.eslintrc`, `ruff.toml`, `pyproject.toml [tool.ruff]`, `.golangci.yml`, etc.)
- Style guides or coding standards documents in `doc/`, `docs/`, or the root
- `CONTRIBUTING.md` sections about code style
- Editor configs (`.editorconfig`)

If comprehensive guidelines already exist as a file, reference that file rather than duplicating its content.

#### b. README and project documentation

Check `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`, `AGENTS.md`, and similar files for any guidance on coding conventions, style preferences, or review expectations.

#### c. Extract conventions from existing code

If the above sources don't provide enough conventions, launch an Explore agent (via a separate Task, one per language) to examine existing code files and extract observable patterns. The agent prompt should ask it to examine 10-20 representative files and return a bulleted list of observed patterns covering:

- Naming conventions (camelCase vs snake_case, prefixes, suffixes)
- Import ordering and grouping
- Error handling patterns
- Logging conventions
- Test file organization and naming
- Comment style and documentation patterns
- Module/package structure conventions

Collect the output and use it directly in drafting the conventions file.

### 3. Create convention files

For each language, create or update a conventions file. Place it in:

- A `doc/` or `docs/` folder if one exists in the project
- Otherwise, `.deepwork/review/`

Name the file descriptively: e.g., `python_conventions.md`, `typescript_conventions.md`.

If a suitable conventions file already exists (found in step 2a), use it as-is — do not create a duplicate. Reference the existing file from the review rule instead.

Each conventions file should be a concise, actionable reference — not an exhaustive style guide. Focus on conventions that a reviewer can actually check by reading code.

### 4. Create `.deepreview` rules

For each language, add a review rule to the top-level `.deepreview` file. If the `.deepreview` file does not yet exist, create it at the project root. Every language review rule must:

- Use `strategy: individual` (one review per changed file)
- Have `match.include` patterns targeting that language's file extensions
- Have `match.exclude` patterns for generated files, vendor directories, etc.
- Inline the review instructions (do not use a file reference for the instructions themselves, though the instructions should reference the conventions file)

The inline review instructions for each rule should:

1. Tell the reviewer to read the conventions file for the project's standards
2. Review the changed file against those conventions
3. **Explicitly instruct the reviewer to check for DRY violations** — look for duplicated logic, repeated patterns, or code that could be extracted into a shared function/module
4. **Explicitly instruct the reviewer to verify all comments are still accurate** — check that comments, docstrings, and inline documentation still correctly describe the code after the changes

**Example rule structure:**

```yaml
python_code_review:
  description: "Review Python files against project conventions and best practices."
  match:
    include:
      - "**/*.py"
    exclude:
      - "**/migrations/**"
      - "**/__pycache__/**"
  review:
    strategy: individual
    instructions: |
      Review this Python file against the project's coding conventions
      documented in doc/python_conventions.md.

      Check for:
      - Adherence to naming conventions and style patterns
      - Proper error handling following project patterns
      - Import ordering and grouping
      - [other language-specific items from the conventions]

      Additionally, always check:
      - **DRY violations**: Is there duplicated logic or repeated patterns that
        should be extracted into a shared function, utility, or module?
      - **Comment accuracy**: Are all comments, docstrings, and inline
        documentation still accurate after the changes? Flag any comments that
        describe behavior that no longer matches the code.
```

### 5. Validate

- Each rule uses `strategy: individual`
- Match patterns correctly target the language's file extensions
- Generated/vendor files are excluded
- Review instructions reference the conventions file by path
- DRY and comment-accuracy checks are present in every rule
- The `.deepreview` file is valid YAML

## Output

### convention_files

All language convention files that were created or identified (existing ones count if referenced by rules).

### deepreview_files

All `.deepreview` files that were created or modified with language review rules.

## Quality Criteria

- Each language with significant presence in the project has a review rule
- Convention files are concise, actionable, and based on actual project patterns (not generic boilerplate)
- Every rule uses `strategy: individual` (per-file reviews)
- Every rule includes explicit DRY-violation and comment-accuracy checks
- Match patterns are appropriate for the language (correct extensions, sensible excludes)
- Existing coding standards files are referenced rather than duplicated
