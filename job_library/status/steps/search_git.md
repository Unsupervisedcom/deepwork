# Search Git

## Objective

Search local git branches and commits using the filter substrings to identify relevant work in the repository.

## Task

Search git branches and commit history for matches against the filter keywords, and compile the results into a structured markdown report.

### Process

1. **Read filter keywords**
   - Read filters.txt from the previous step
   - Parse the keywords (one per line)
   - If empty, search will include all branches and commits

2. **Search branches**
   - List all local and remote branches: `git branch -a`
   - Filter branches by keywords (match branch name against all keywords)
   - For matching branches:
     - Extract branch name
     - Get the latest commit on that branch
     - Check if branch is ahead/behind main or other base branch
   - Example matches for filters "foo" and "bar":
     - `feature/foo-bar-implementation` ✓ (contains both)
     - `feature/foo-feature` ✗ (missing "bar")
     - `bugfix/bar-and-foo` ✓ (contains both)

3. **Search commits**
   - Search commit messages: `git log --all --grep="<keyword>" --oneline`
   - For each keyword, find matching commits
   - Combine results and filter to commits matching ALL keywords
   - For matching commits:
     - Include commit SHA (short form)
     - Include commit message (first line)
     - Include author name
     - Include date
     - Include which branch(es) contain the commit
   - Limit to recent commits (last 100 or so) to keep output manageable

4. **Organize results**
   - Create git_results.md with clear sections:
     - **Search Filters** - List the filter keywords used
     - **Matching Branches** - Table or list of branches
     - **Matching Commits** - Table or list of commits
     - **Summary** - Count of matches in each category

5. **Format for readability**
   - Use markdown tables for structured data
   - Include links to commits if viewing in GitHub-compatible markdown
   - Sort results by date (most recent first)
   - Group related information together

## Example Output Structure

```markdown
# Git Search Results

## Search Filters
- foo
- bar

## Matching Branches

| Branch Name | Latest Commit | Status |
|------------|---------------|---------|
| feature/foo-bar-implementation | abc1234 Add foo-bar integration | 3 commits ahead of main |
| bugfix/bar-and-foo | def5678 Fix foo-bar bug | Merged to main |

**Total:** 2 branches

## Matching Commits

| SHA | Date | Author | Message | Branches |
|-----|------|--------|---------|----------|
| abc1234 | 2024-01-15 | John Doe | Add foo-bar integration | feature/foo-bar-implementation |
| def5678 | 2024-01-10 | Jane Smith | Fix foo-bar bug | bugfix/bar-and-foo, main |
| ghi9012 | 2024-01-05 | Bob Johnson | Implement foo with bar support | main |

**Total:** 3 commits

## Summary

Found work related to filters: foo, bar
- 2 matching branches
- 3 matching commits across all branches
- Most recent activity: 2024-01-15
```

## Quality Criteria

- filters.txt was read and parsed correctly
- All branches were searched (local and remote)
- Commit history was searched for matching keywords
- Results include only items matching ALL filter keywords
- git_results.md is well-formatted and easy to read
- Each result includes relevant context (SHA, author, date, message)
- Summary provides high-level statistics
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This step searches the local git repository for work matching the filter criteria. The results will be combined with GitHub search results in a later step to provide a comprehensive view of repository activity.

## Tips

- Use `git --no-pager` to prevent pager issues in automated scripts
- Consider using `git log --all --format=...` for consistent output formatting
- Filter case-insensitively for better matching
- Handle empty filter list (show all results)
- Limit results to keep output manageable (e.g., last 100 commits)
