# Search GitHub

## Objective

Search GitHub pull requests and issues using the filter substrings to identify relevant work and discussions.

## Task

Search GitHub PRs and issues for matches against the filter keywords using GitHub MCP tools, and compile the results into a structured markdown report.

### Process

1. **Read filter keywords**
   - Read filters.txt from the previous step
   - Parse the keywords (one per line)
   - If empty, search will include all open PRs and issues

2. **Detect repository information**
   - Determine the GitHub repository owner and name from git remote
   - Use: `git remote get-url origin`
   - Parse the URL to extract owner and repo name
   - Example: `https://github.com/owner/repo.git` → owner: "owner", repo: "repo"

3. **Search pull requests**
   - Use GitHub MCP tools to search for PRs:
     - `list_pull_requests` or `search_pull_requests` tool
   - Search for PRs matching filter keywords in:
     - PR title
     - PR description
     - Branch names (head and base)
   - Filter to PRs matching ALL keywords (case-insensitive)
   - For matching PRs:
     - Include PR number
     - Include PR title
     - Include PR state (open/closed/merged)
     - Include author
     - Include labels (if any)
     - Include creation date
     - Include link to PR

4. **Search issues**
   - Use GitHub MCP tools to search for issues:
     - `list_issues` or `search_issues` tool
   - Search for issues matching filter keywords in:
     - Issue title
     - Issue description
     - Labels
   - Filter to issues matching ALL keywords (case-insensitive)
   - For matching issues:
     - Include issue number
     - Include issue title
     - Include issue state (open/closed)
     - Include author
     - Include labels (if any)
     - Include creation date
     - Include link to issue

5. **Organize results**
   - Create github_results.md with clear sections:
     - **Search Filters** - List the filter keywords used
     - **Repository** - Show owner/repo being searched
     - **Matching Pull Requests** - Table or list of PRs
     - **Matching Issues** - Table or list of issues
     - **Summary** - Count of matches in each category

6. **Format for readability**
   - Use markdown tables for structured data
   - Include clickable links to PRs and issues
   - Sort results by date (most recent first)
   - Highlight PR/issue state (open/closed/merged)
   - Group by state if helpful

## Example Output Structure

```markdown
# GitHub Search Results

## Search Filters
- foo
- bar

## Repository
- Owner: Unsupervisedcom
- Repository: deepwork

## Matching Pull Requests

| # | Title | State | Author | Labels | Created | Link |
|---|-------|-------|--------|--------|---------|------|
| #42 | Add foo-bar integration feature | Open | johndoe | enhancement, foo | 2024-01-15 | [View PR](https://github.com/owner/repo/pull/42) |
| #38 | Fix foo and bar compatibility | Merged | janesmith | bugfix, foo, bar | 2024-01-10 | [View PR](https://github.com/owner/repo/pull/38) |

**Total:** 2 pull requests (1 open, 1 merged)

## Matching Issues

| # | Title | State | Author | Labels | Created | Link |
|---|-------|-------|--------|--------|---------|------|
| #55 | Improve foo-bar performance | Open | bobsmith | enhancement | 2024-01-18 | [View Issue](https://github.com/owner/repo/issues/55) |
| #48 | Bug in foo when used with bar | Closed | alicejones | bug, fixed | 2024-01-12 | [View Issue](https://github.com/owner/repo/issues/48) |

**Total:** 2 issues (1 open, 1 closed)

## Summary

Found work related to filters: foo, bar
- 2 matching pull requests (1 open, 1 merged)
- 2 matching issues (1 open, 1 closed)
- Most recent activity: 2024-01-18
```

## Quality Criteria

- filters.txt was read and parsed correctly
- Repository information was detected from git remote
- GitHub MCP tools were used to search PRs and issues
- Results include only items matching ALL filter keywords (case-insensitive)
- github_results.md is well-formatted and easy to read
- Each result includes relevant context (number, title, state, author, labels, date)
- Links are provided to view PRs and issues on GitHub
- Summary provides high-level statistics
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This step searches GitHub for PRs and issues matching the filter criteria. The results will be combined with git search results in a later step to provide a comprehensive view of repository activity.

## GitHub MCP Tools Available

You have access to these GitHub MCP tools:
- `github-mcp-server-list_pull_requests` - List PRs in a repository
- `github-mcp-server-search_pull_requests` - Search PRs with query syntax
- `github-mcp-server-list_issues` - List issues in a repository
- `github-mcp-server-search_issues` - Search issues with query syntax

Use the search tools with appropriate query syntax to filter by keywords.

## Tips

- Use GitHub search query syntax: `repo:owner/repo keyword1 keyword2`
- Filter case-insensitively for better matching
- Handle empty filter list (show all results)
- Consider pagination if there are many results
- Include both open and closed items for comprehensive view
- Parse git remote URL carefully to extract owner/repo
