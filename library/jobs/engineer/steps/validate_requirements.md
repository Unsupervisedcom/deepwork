# Validate requirements

Check that all requirement files follow the RFC 2119 format, numbering is
consistent, and the index is complete.

## Procedure

1. Read `.deepwork/tmp/requirements_context.md` for the requirements directory path.
2. Read `.deepwork/tmp/requirements_draft.md` for the list of created/modified files.
3. For each `REQ-*.md` file in the requirements directory, verify:
   - **Header format**: starts with `# REQ-NNN: Title`.
   - **RFC 2119 declaration**: contains the key words declaration paragraph. The
     expected text starts with: `Key words: RFC 2119 (MUST, MUST NOT, SHALL, ...`.
   - **Sub-requirement format**: each requirement is `**REQ-NNN.X**` with
     sequential numbering starting at 1.
   - **Keyword presence**: every sub-requirement contains at least one RFC 2119
     keyword (`MUST`, `MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`,
     `MAY`, `REQUIRED`, `OPTIONAL`) in uppercase.
   - **Testability**: each sub-requirement specifies an observable outcome — a
     measurable state, detectable artifact, or pass/fail condition. Example of
     testable: "The system MUST respond within 200ms." Example of non-testable:
     "The system SHOULD be fast." If a file cannot be read or is empty, record
     its status as FAIL with issue "File unreadable or empty."
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
- **Overall status**: PASS if all checks pass. FAIL if any of the following: bad
  header format, missing RFC 2119 declaration, missing keyword in any
  sub-requirement, broken index rows (row points to missing file), or
  unreadable/empty requirement files. ID gaps and missing AGENTS.md entry
  (when using the default path) are warnings only and do not cause FAIL.
