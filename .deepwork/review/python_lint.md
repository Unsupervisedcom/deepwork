Run ruff and mypy on the changed Python files listed below. Fix what you can automatically, then report only issues that remain unresolved.

## Steps

1. Run `uv run ruff check --fix` on each file listed under "Files to Review".
2. Run `uv run ruff format` on each file listed under "Files to Review".
3. Run `uv run mypy` on each file listed under "Files to Review".
4. Fix any remaining issues you can resolve (e.g., adding type annotations, renaming ambiguous variables).
5. Re-run all three checks to confirm your fixes are clean.

## Output Format

Only report issues that remain **after** your fixes. Do not report issues you already resolved.

- PASS: All checks pass (no remaining issues).
- FAIL: Unfixable lint errors or type errors remain. List each with file, line, and details.
