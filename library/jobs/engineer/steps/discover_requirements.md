# Discover requirements context

Read the project's agent context file (`AGENTS.md`, `CLAUDE.md`, or equivalent) to
determine the requirements directory. Default to `./requirements/` if no override
is specified.

## Procedure

1. Read the project's agent context file. Look for a `## Requirements` section or
   any mention of a requirements directory path. If no agent context file exists
   (`AGENTS.md`, `CLAUDE.md`, or equivalent), treat this as equivalent to no
   override being specified and default to `./requirements/`.
2. If a custom path is declared, use it. Otherwise use `./requirements/`.
3. Check whether the requirements directory exists. If it does, read
   `REQUIREMENTS.md` (the index) and list all existing `REQ-*.md` files.
4. Read the user's goal (provided as input). Determine whether they want to:
   - Create a new requirement from scratch
   - Amend an existing requirement
   - Reorganize or renumber requirements
5. If creating a new requirement, determine the next available `REQ-NNN` number
   from the existing index.

## Output

Write `.deepwork/tmp/requirements_context.md` containing:

- **Requirements directory**: absolute or relative path
- **Existing requirements**: table of `ID | Title | File` (empty if none)
- **Next available ID**: e.g., `REQ-012`
- **User intent**: one of `create` | `amend` | `reorganize`
- **Target requirements**: which requirement IDs will be created or modified (for create: the next available ID; for amend/reorganize: the existing IDs)
- **Custom path override**: whether AGENTS.md declares a non-default path
