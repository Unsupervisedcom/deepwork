Run ruff and mypy on the changed Python files listed below.

## Steps

1. Run `uv run ruff check --fix` on each file listed under "Files to Review".
2. Run `uv run ruff format` on each file listed under "Files to Review".
3. Run `uv run mypy` on each file listed under "Files to Review".
4. If ruff made changes, report what was fixed.
5. If there are remaining ruff errors that `--fix` could not resolve, report them with file paths, line numbers, and rule codes.
6. If mypy reports type errors, list them with file paths, line numbers, and error messages.

## Output Format

- PASS: No issues found (or all ruff issues were auto-fixed and mypy is clean).
- FAIL: Unfixable lint errors or type errors remain. List each with file, line, and details.
