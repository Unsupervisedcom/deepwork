# Create Release PR

## Objective

Create a pull request with the release changes targeting the main branch.

## Task

Commit the updated release files and create a pull request using the GitHub CLI.

### Process

1. **Create a release branch**
   ```bash
   git checkout -b release/vX.Y.Z
   ```
   Where X.Y.Z is the new version from the previous step.

2. **Stage the release files**
   ```bash
   git add CHANGELOG.md pyproject.toml uv.lock
   ```

3. **Commit the changes**
   ```bash
   git commit -m "chore: Release vX.Y.Z"
   ```

4. **Push the branch**
   ```bash
   git push -u origin release/vX.Y.Z
   ```

5. **Create the pull request**
   ```bash
   gh pr create --title "Release vX.Y.Z" --body "$(cat <<'EOF'
   ## Summary

   Release version X.Y.Z

   ## Changes

   [Copy the changelog entry for this version here]

   ## Checklist

   - [ ] CHANGELOG.md updated
   - [ ] pyproject.toml version bumped
   - [ ] uv.lock synced
   EOF
   )" --base main
   ```

6. **Record the PR URL**
   Save the PR URL to `release/pr_url.md` for reference.

## Output Format

### release/pr_url.md

A simple file containing the PR URL for easy reference.

**Structure**:
```markdown
# Release PR

**Version**: X.Y.Z
**PR URL**: https://github.com/owner/repo/pull/123
**Created**: YYYY-MM-DD

## Next Steps

1. Review the PR
2. Ensure CI passes
3. Merge to main
4. Create GitHub release with tag vX.Y.Z
```

## Quality Criteria

- Release branch is created with correct naming (`release/vX.Y.Z`)
- All three files are committed (CHANGELOG.md, pyproject.toml, uv.lock)
- Commit message follows conventional format
- PR is created targeting main branch
- PR body includes the changelog entry
- PR URL is saved to `release/pr_url.md`
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This is the final step of the release workflow. After this step completes, the user should:
1. Review the PR
2. Wait for CI to pass
3. Merge the PR
4. Create a GitHub release with a tag matching the version

The PR provides a review checkpoint before the release is finalized.
