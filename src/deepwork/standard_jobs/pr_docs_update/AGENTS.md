# Project Context for pr_docs_update

This job automatically updates documentation by analyzing recently merged pull requests.

## Purpose

The `pr_docs_update` job helps maintain up-to-date AGENTS.md files and copilot-specific instructions by:
- Fetching recently merged PRs from the GitHub repository
- Analyzing PR content for documentation-relevant changes
- Updating appropriate documentation files
- Tracking processed PRs to enable incremental updates

## Dual Location Maintenance

**Important**: This is an example job that can be used in any repository. If you're working on the DeepWork repository itself and want to make this a standard job, follow the dual location pattern:

1. **Source of truth**: `src/deepwork/standard_jobs/pr_docs_update/`
   - Make changes here first
   - Tracked in version control

2. **Working copy**: `.deepwork/jobs/pr_docs_update/`
   - Updated from source using `deepwork install`
   - Used by `deepwork sync` to generate commands

## File Organization

```
pr_docs_update/
├── AGENTS.md              # This file
├── job.yml                # Job definition
└── steps/
    ├── fetch_prs.md       # Fetch merged PRs from GitHub
    ├── analyze_prs.md     # Analyze PR content
    └── update_docs.md     # Update documentation files
```

## How It Works

1. **State Tracking**: Uses `.deepwork/pr_docs_state.json` to track processed PRs
2. **Incremental Processing**: Only processes new PRs, skips already-processed ones
3. **Flexible Configuration**: Can specify PR count and state file location
4. **Multiple Runs**: Can be run repeatedly to go deeper into PR history

## Usage Notes

- Run periodically (e.g., weekly) to keep documentation current
- Increase `pr_count` parameter to process more PRs at once
- State file prevents duplicate processing across runs
- Can be used in any repository with GitHub PRs

## State File Format

```json
{
  "processed_prs": [123, 456, 789],
  "last_update": "2026-01-19T07:00:00Z",
  "total_processed": 3
}
```

## Requirements

- GitHub API access (uses GitHub MCP tools)
- Write access to documentation files
- Git repository with GitHub remote

## Last Updated

- Date: 2026-01-19
- From: Initial job creation
