# Draft requirements

Create or amend RFC 2119 requirement files in the project's requirements directory.

## Format

Each requirement file MUST follow this structure:

```markdown
# REQ-NNN: Title

Brief description of what this requirement covers.

Key words: RFC 2119 (MUST, MUST NOT, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
MAY, REQUIRED, OPTIONAL).

## Requirements

**REQ-NNN.1** The system MUST ...

**REQ-NNN.2** The system SHOULD ...
```

Rules:
- File name: `REQ-NNN-slug.md` where slug is a lowercase hyphenated summary.
- Each sub-requirement is numbered `REQ-NNN.X` starting at 1.
- Every sub-requirement MUST contain at least one RFC 2119 keyword in uppercase.
- Requirements MUST be testable — each statement should be verifiable by an
  automated test or a DeepWork review rule.

## Procedure

1. Read `.deepwork/tmp/requirements_context.md` for directory path, existing
   requirements, and user intent.
2. If **creating**: write new `REQ-NNN-slug.md` file(s) in the requirements directory.
3. If **amending**: read the existing requirement file, apply changes, preserve
   numbering continuity. Append new sub-requirements rather than renumbering unless
   the user explicitly requests renumbering.
4. Update `REQUIREMENTS.md` index to include any new entries. The index MUST be a
   Markdown table with columns `ID | Title | File`.
5. If the requirements directory does not exist, create it along with the
   `REQUIREMENTS.md` index file.
6. If AGENTS.md does not document the requirements path and the path is non-default,
   add a `## Requirements` section to AGENTS.md declaring the path.

## Output

Write `.deepwork/tmp/requirements_draft.md` containing:

- **Files created**: list of new files written
- **Files modified**: list of existing files amended
- **Index updated**: whether REQUIREMENTS.md was created or updated
- **AGENTS.md updated**: whether AGENTS.md was modified (and why)
- **Summary of changes**: brief description of each requirement added or modified
