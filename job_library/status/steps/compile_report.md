# Compile Report

## Objective

Combine all search results from git and GitHub into a comprehensive, well-organized status report that helps decision makers quickly understand current work.

## Task

Read the git and GitHub search results, integrate them into a unified report, and provide an executive summary of the repository's status.

### Process

1. **Read input files**
   - Read git_results.md from the search_git step
   - Read github_results.md from the search_github step
   - Extract key information from each

2. **Create executive summary**
   - Provide high-level overview at the top
   - Include:
     - Total number of active branches with matching work
     - Total number of commits found
     - Total number of open PRs and issues
     - Date range of activity
     - Key themes or patterns observed
   - Keep summary concise (3-5 bullet points)

3. **Organize by work category**
   - **Active Development** - Open PRs and their associated branches
   - **Open Issues** - Issues awaiting resolution
   - **Recent Commits** - Commit activity on main/master and feature branches
   - **Completed Work** - Merged PRs and closed issues (if relevant)

4. **Cross-reference information**
   - Link PRs to their associated branches (from git results)
   - Link commits to their PRs (if mentioned in commit messages)
   - Show relationships between issues and PRs
   - Identify orphaned branches (branches without open PRs)

5. **Add context for decision making**
   - Highlight stale work (old branches or PRs without recent activity)
   - Flag potential blockers (PRs waiting for review, unassigned issues)
   - Note areas of high activity (multiple PRs/commits in same area)
   - Identify dependencies between work items (if evident)

6. **Format for readability**
   - Use clear section headers
   - Include a table of contents for easy navigation
   - Use visual indicators (✓, ⚠️, 🔄, etc.) for status
   - Keep most recent work at the top
   - Use standard markdown formatting (tables, headers, lists) for broad compatibility

## Example Output Structure

```markdown
# Repository Status Report

**Generated:** 2024-01-19  
**Filters Applied:** foo, bar

## Executive Summary

- 🔄 **2 active branches** with ongoing development related to foo-bar integration
- ✅ **1 merged PR** completing foo-bar compatibility fixes
- 📝 **2 open issues** requiring attention (1 enhancement, 1 bug)
- 📊 **3 recent commits** across feature branches and main
- ⏱️ Most recent activity: 2024-01-18 (1 day ago)

## Table of Contents
- [Active Development](#active-development)
- [Open Issues](#open-issues)
- [Recent Commits](#recent-commits)
- [Completed Work](#completed-work)

---

## Active Development

### 🔄 Open Pull Requests

| PR | Title | Branch | Status | Author | Updated |
|----|-------|--------|--------|--------|---------|
| [#42](https://github.com/owner/repo/pull/42) | Add foo-bar integration feature | `feature/foo-bar-implementation` | Review pending | johndoe | 2 days ago |

**Branch Status:** 3 commits ahead of main  
**Latest Commit:** abc1234 - Add foo-bar integration (johndoe, 2024-01-15)

---

## Open Issues

### 🐛 Bugs

| Issue | Title | Labels | Author | Created |
|-------|-------|--------|--------|---------|
| [#48](https://github.com/owner/repo/issues/48) | Bug in foo when used with bar | bug | alicejones | 7 days ago |

### ✨ Enhancements

| Issue | Title | Labels | Author | Created |
|-------|-------|--------|--------|---------|
| [#55](https://github.com/owner/repo/issues/55) | Improve foo-bar performance | enhancement | bobsmith | 1 day ago |

---

## Recent Commits

### On Feature Branches

| SHA | Date | Branch | Author | Message |
|-----|------|--------|--------|---------|
| abc1234 | Jan 15 | feature/foo-bar-implementation | johndoe | Add foo-bar integration |

### On Main Branch

| SHA | Date | Author | Message | PR |
|-----|------|--------|---------|-----|
| def5678 | Jan 10 | janesmith | Fix foo-bar bug | [#38](https://github.com/owner/repo/pull/38) |
| ghi9012 | Jan 5 | bobjohnson | Implement foo with bar support | [#35](https://github.com/owner/repo/pull/35) |

---

## Completed Work

### ✅ Merged Pull Requests

| PR | Title | Merged | Author |
|----|-------|--------|--------|
| [#38](https://github.com/owner/repo/pull/38) | Fix foo and bar compatibility | Jan 10 | janesmith |

### ✓ Closed Issues

| Issue | Title | Closed | Resolution |
|-------|-------|--------|------------|
| [#45](https://github.com/owner/repo/issues/45) | foo-bar crashes on edge case | Jan 11 | Fixed in #38 |

---

## Insights & Recommendations

- **Active Work:** Primary focus is on foo-bar integration feature (#42)
- **Performance:** New issue raised about foo-bar performance (#55) - may want to address before merging #42
- **Recent Fixes:** Good progress on compatibility issues, with bug fix merged last week
- **No Blockers:** No obvious blockers identified in current work

---

## Summary Statistics

- **Branches:** 2 active, 0 stale (>30 days old)
- **Pull Requests:** 1 open, 1 merged (last 2 weeks)
- **Issues:** 2 open, 1 closed (last 2 weeks)
- **Commits:** 3 matching commits across all branches
- **Contributors:** 4 active (johndoe, janesmith, bobjohnson, alicejones)
```

## Quality Criteria

- Both git_results.md and github_results.md were read and processed
- Executive summary provides clear high-level overview
- Report is organized into clear sections
- Cross-references between PRs, branches, and commits are included
- Status indicators help quickly identify state of work
- Insights section provides actionable information for decision makers
- Report is comprehensive yet easy to scan quickly
- status_report.md is saved in the working directory
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This is the final step of the status workflow. The compiled report provides decision makers with a comprehensive view of all work in the repository related to the specified filters, making it easy to get up to speed on current activity.

## Tips

- Focus on actionable information that helps decision making
- Use visual indicators and formatting to make scanning easy
- Include timestamps and relative dates ("2 days ago") for context
- Highlight potential issues or blockers prominently
- Keep the executive summary concise but informative
- Link related items together to show the big picture
