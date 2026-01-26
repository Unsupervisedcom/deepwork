# Commit and Push

## Objective

Review the changed files to verify they match the agent's expectations, create a commit with an appropriate message, and push to the remote repository.

## Task

Check the list of changed files against what was modified during this session, ensure they match expectations, then commit and push the changes.

### Process

1. **Get the list of changed files**
   ```bash
   git status
   ```
   Also run `git diff --stat` to see a summary of changes.

2. **Verify changes match expectations**

   Compare the changed files against what you modified during this session:
   - Do the modified files match what you edited?
   - Are there any unexpected new files?
   - Are there any unexpected deleted files?
   - Do the line counts seem reasonable for the changes you made?

   If changes match expectations, proceed to the next step.

   If there are unexpected changes:
   - Investigate why (e.g., lint auto-fixes, generated files)
   - If they're legitimate side effects of your work, include them
   - If they're unrelated or shouldn't be committed, use `git restore` to discard them

3. **Update CHANGELOG.md if needed**

   If your changes include new features, bug fixes, or other notable changes:
   - Add entries to the `## [Unreleased]` section of CHANGELOG.md
   - Use the appropriate subsection: `### Added`, `### Changed`, `### Fixed`, or `### Removed`
   - Write concise descriptions that explain the user-facing impact

   **CRITICAL: NEVER modify version numbers**
   - Do NOT change the version in `pyproject.toml`
   - Do NOT change version headers in CHANGELOG.md (e.g., `## [0.4.2]`)
   - Do NOT rename the `## [Unreleased]` section
   - Version updates are handled by the release workflow, not commits

4. **Stage all appropriate changes**
   ```bash
   git add -A
   ```
   Or stage specific files if some were excluded.

5. **View recent commit messages for style reference**
   ```bash
   git log --oneline -10
   ```

6. **Create the commit**

   Generate an appropriate commit message based on:
   - The changes made
   - The style of recent commits
   - Conventional commit format if the project uses it

   **IMPORTANT:** Use the commit job script (not `git commit` directly):
   ```bash
   .claude/hooks/commit_job_git_commit.sh -m "commit message here"
   ```

7. **Push to remote**
   ```bash
   git push
   ```
   If the branch has no upstream, use:
   ```bash
   git push -u origin HEAD
   ```

## Quality Criteria

- Changed files were verified against expectations
- CHANGELOG.md was updated with entries in [Unreleased] section (if changes warrant documentation)
- Version numbers were NOT modified (pyproject.toml version and CHANGELOG version headers unchanged)
- Commit was created with appropriate message
- Changes were pushed to remote

## Context

This is the final step of the commit workflow. The agent verifies that the changed files match its own expectations from the work done during the session, then commits and pushes. This catches unexpected changes while avoiding unnecessary user interruptions.
