# Validate requirements

Check that all requirement files follow the RFC 2119 format, numbering is
consistent, and the index is complete.

## Procedure

1. Read `.deepwork/tmp/requirements_context.md` for the requirements directory path.
2. Read `.deepwork/tmp/requirements_draft.md` for the list of created/modified files.
3. For each `REQ-*.md` file in the requirements directory, verify:
   - **Header format**: starts with `# REQ-NNN: Title`.
   - **RFC 2119 declaration**: contains the key words declaration paragraph.
   - **Sub-requirement format**: each requirement is `**REQ-NNN.X**` with
     sequential numbering starting at 1.
   - **Keyword presence**: every sub-requirement contains at least one RFC 2119
     keyword (`MUST`, `MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`,
     `MAY`, `REQUIRED`, `OPTIONAL`) in uppercase.
   - **Testability**: each sub-requirement describes a verifiable behavior.
4. Verify `REQUIREMENTS.md` index:
   - Every `REQ-*.md` file in the directory has a corresponding row.
   - No index rows point to missing files.
   - IDs are sequential with no gaps (warn on gaps but do not fail).
5. Verify AGENTS.md documents the requirements path if it differs from
   `./requirements/`.

## Output

Write `.deepwork/tmp/requirements_validation.md` containing:

- **Files checked**: count of requirement files validated
- **Validation results**: table of `File | Status | Issues` for each file
- **Index status**: PASS or FAIL with details
- **AGENTS.md status**: PASS, FAIL, or N/A (default path needs no documentation)
- **Overall status**: PASS if all checks pass, FAIL if any critical issue found
