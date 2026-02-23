# Analyze Document Dependencies

## Objective

Examine a documentation file's content and filesystem location to determine which source files could affect its accuracy, then recommend a strategy for creating a .deepreview rule to keep it current.

## Task

Given a documentation file path, perform a thorough dependency analysis to identify the source files that the document describes or depends on. Produce a structured analysis that will drive the next step's rule creation.

### Process

1. **Read the documentation file**
   - Read the full contents of the file at the provided `doc_path`
   - Identify the key topics, concepts, and claims the document makes
   - Note any explicit references to files, directories, modules, or code constructs

2. **Examine the filesystem context**
   - Look at the document's location in the directory tree
   - Identify sibling files, parent directories, and nearby related files
   - Use `Glob` and `Grep` to find source files that contain identifiers, functions, classes, or concepts mentioned in the document
   - Search for files that import, reference, or implement what the document describes

3. **Build the dependency list**
   - For each identified source file, note WHY it could affect the document's accuracy
   - Categorize dependencies as:
     - **Direct**: The document explicitly describes this file's contents (e.g., API docs describing an endpoint handler)
     - **Structural**: Changes to the file's existence, location, or interface would invalidate the doc (e.g., a README referencing a directory structure)
     - **Behavioral**: Changes to the file's behavior could make the doc's claims inaccurate (e.g., docs describing a feature's behavior)

4. **Decide narrow vs wide strategy**
   - **Narrow** (specific rule for this document): Use when the dependency set is small — literally 2-5 specific files that can each be named explicitly in glob patterns
   - **Wide** (broader rule covering a directory/hierarchy): Use when:
     - Many files in a directory could affect the doc
     - The set is hard to enumerate with a few specific globs
     - New files added to a directory would also be relevant
   - When in doubt, prefer wide — it's better to trigger a review that finds no issues than to miss a relevant change

5. **Determine rule naming**
   - Narrow: `update_<doc_name_without_extension>` (e.g., `update_architecture` for `architecture.md`)
   - Wide: `update_documents_relating_to_<watched_path_description>` (e.g., `update_documents_relating_to_src_core` for docs about `src/core/`)

6. **Check for existing overlapping rules**
   - Read the existing `.deepreview` file (if it exists)
   - For wide strategy: check if any existing rule already has match patterns that substantially overlap with the proposed patterns
   - If an overlapping rule exists, recommend adding this document to that rule's monitored list instead of creating a new rule
   - Document the overlapping rule name and how the patterns overlap

7. **Compose the recommended glob patterns**
   - Write the specific glob patterns for `match.include`
   - Always include the documentation file itself in the match patterns (so the review also triggers when someone edits the doc directly)
   - Consider whether any `match.exclude` patterns are needed (e.g., test files, generated files)
   - **Be careful with exclusions**: Before excluding a directory from match patterns, check whether the document contains a directory tree listing or structural reference that includes that directory. If the doc mentions a directory in a tree listing, changes to that directory (even adding/removing files) could invalidate the doc's tree — so don't exclude it. Only exclude directories that are truly irrelevant to the document's accuracy (e.g., `__pycache__/`, `.git/`).

## Output Format

### analysis

A markdown document with the full dependency analysis and rule recommendation.

**Structure**:
```markdown
# Document Dependency Analysis

## Document Under Analysis
- **Path**: [doc_path]
- **Summary**: [1-2 sentence summary of what the document covers]

## Identified Dependencies

### Direct Dependencies
| Source File | Reason |
|-------------|--------|
| [path/to/file.py] | [Why changes to this file affect the doc] |

### Structural Dependencies
| Source File/Directory | Reason |
|----------------------|--------|
| [path/to/dir/] | [Why structural changes here affect the doc] |

### Behavioral Dependencies
| Source File | Reason |
|-------------|--------|
| [path/to/module.py] | [Why behavior changes here affect the doc] |

## Strategy Decision

**Strategy**: [Narrow / Wide]

**Rationale**: [Why this strategy was chosen — reference the dependency count and pattern complexity]

## Recommended Rule

**Rule name**: [update_<name> or update_documents_relating_to_<desc>]

**Match patterns**:
```yaml
include:
  - "[glob/pattern/1]"
  - "[glob/pattern/2]"
  - "[doc_path itself]"
exclude:    # if needed
  - "[exclusion pattern]"
```

**Review strategy**: [matches_together or all_changed_files]

## Existing Rule Assessment

[One of:]
- **No .deepreview file exists.** A new file and rule will be created.
- **No overlapping rules found.** Existing rules target different file sets.
- **Overlapping rule found: `[rule_name]`**. Its match patterns `[patterns]` substantially overlap with the proposed patterns. Recommend adding `[doc_path]` to this rule's monitored document list instead of creating a new rule.
```

**Concrete example** (narrow case — a specific README describing a CLI module):
```markdown
# Document Dependency Analysis

## Document Under Analysis
- **Path**: docs/cli-reference.md
- **Summary**: Documents the CLI commands, flags, and usage examples for the deepwork CLI.

## Identified Dependencies

### Direct Dependencies
| Source File | Reason |
|-------------|--------|
| src/deepwork/cli/serve.py | Implements the `serve` command documented in the reference |
| src/deepwork/cli/hook.py | Implements the `hook` command documented in the reference |

### Structural Dependencies
| Source File/Directory | Reason |
|----------------------|--------|
| src/deepwork/cli/__init__.py | CLI entry point — adding/removing commands here changes what's available |

### Behavioral Dependencies
| Source File | Reason |
|-------------|--------|
| (none) | |

## Strategy Decision

**Strategy**: Narrow

**Rationale**: Only 3 specific files affect this document. They can be enumerated explicitly.

## Recommended Rule

**Rule name**: update_cli_reference

**Match patterns**:
```yaml
include:
  - "src/deepwork/cli/serve.py"
  - "src/deepwork/cli/hook.py"
  - "src/deepwork/cli/__init__.py"
  - "docs/cli-reference.md"
```

**Review strategy**: matches_together

## Existing Rule Assessment

No overlapping rules found. The existing `python_code_review` rule matches `**/*.py` but serves a different purpose (code quality, not documentation freshness).
```

## Quality Criteria

- All source files that could realistically affect the document's accuracy are identified
- Glob patterns correctly capture the identified dependencies
- The narrow vs wide decision is well-reasoned based on the dependency set size
- The document itself is included in the match patterns
- Existing .deepreview rules are checked for overlap before recommending a new rule
- The analysis provides clear rationale that can be verified by the reviewer

## Context

This analysis is the foundation for the rule that will be created in the next step. Getting the dependency identification right is critical — too narrow means changes slip through without review, too broad means noisy reviews that get ignored. The reviewer will verify this analysis against the actual filesystem before the rule is applied.
