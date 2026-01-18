# Format Code

## Objective

Run ruff formatting and linting checks, fixing any issues until the code is clean (maximum 5 attempts).

## Task

Execute ruff to check code formatting and linting. If any issues are found, fix them. Continue this cycle until ruff reports no issues or you've made 5 fix attempts.

**Note**: This step is designed to run as a subagent to minimize token usage. Focus on efficient, targeted fixes.

### Process

1. **Check format and lint status**
   The hook automatically runs:
   ```bash
   uv run ruff format --check src/ tests/
   uv run ruff check src/ tests/
   ```

2. **Analyze ruff output**
   - If both commands pass (exit code 0), you're done with this step
   - If issues are reported, examine them carefully

3. **Fix issues** (if needed)

   **For formatting issues**:
   ```bash
   uv run ruff format src/ tests/
   ```
   This auto-fixes formatting issues.

   **For linting issues**:
   - Some can be auto-fixed: `uv run ruff check --fix src/ tests/`
   - Others require manual fixes based on the error messages
   - Common issues: unused imports, undefined names, line length

4. **Repeat if necessary**
   - Re-run checks after fixes
   - Continue until all issues are resolved
   - Track your attempts - stop after 5 fix attempts if issues remain
   - If you cannot fix after 5 attempts, report remaining issues to the user

### Common Ruff Issues and Fixes

| Issue | Fix |
|-------|-----|
| F401 unused import | Remove the import |
| F841 unused variable | Remove or use the variable |
| E501 line too long | Break into multiple lines |
| I001 import sorting | Run `ruff check --fix` or reorder manually |
| E711 comparison to None | Use `is None` instead of `== None` |

### Important Notes

- **Run ruff format first** - It auto-fixes most formatting issues
- **Use --fix for lint issues** - Many lint issues can be auto-fixed
- **Minimal manual fixes** - Only manually fix what auto-fix can't handle
- **Track attempts** - Keep count of fix attempts to respect the 5-attempt limit

## Output Format

No file output is required. Success is determined by ruff passing all checks.

**On success**: Report that ruff checks pass and proceed to the next step.

**On failure after 5 attempts**: Report which issues remain and why you couldn't fix them.

## Quality Criteria

- `uv run ruff format --check src/ tests/` passes (exit code 0)
- `uv run ruff check src/ tests/` passes (exit code 0)
- Any fixes made don't break functionality (tests should still pass)
- If issues couldn't be fixed in 5 attempts, clear explanation provided

## Hook Behavior

After you complete this step, a hook will automatically run ruff format and lint checks and show you the results.

**Interpreting the hook output:**
- **Both checks passed (exit code 0)**: The step is complete. Proceed to the next step.
- **Checks failed (exit code non-zero)**: You must fix the issues. Use `uv run ruff format src/ tests/` for formatting and `uv run ruff check --fix src/ tests/` for auto-fixable lint issues. For remaining issues, fix manually. The hook will re-run after each attempt.

**Important**: The hook runs automatically - you don't need to run the checks yourself after fixing. Just focus on making fixes, and the hook will verify them.

## Context

This is the second step in the commit workflow, after tests pass. Code must be properly formatted and lint-free before committing.
