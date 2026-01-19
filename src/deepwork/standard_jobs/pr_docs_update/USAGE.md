# PR Documentation Update Job - Example Usage

This document provides example usage scenarios for the `pr_docs_update` job.

## Overview

The `pr_docs_update` job automatically updates documentation by analyzing recently merged pull requests. It's designed to:
- Keep AGENTS.md files up to date with code changes
- Update copilot-specific instructions when relevant
- Track processed PRs to avoid duplicates
- Enable incremental processing across multiple runs

## Basic Usage

### First Run - Process Last 10 PRs

```bash
# Run all steps to process the 10 most recent merged PRs
/pr_docs_update.fetch_prs
/pr_docs_update.analyze_prs
/pr_docs_update.update_docs
```

The job will:
1. Fetch the 10 most recent merged PRs
2. Filter out any already processed (from state file)
3. Analyze each PR for documentation relevance
4. Update appropriate documentation files
5. Save processed PR numbers to state file

### Subsequent Runs - Process More PRs

```bash
# Run with a higher count to go deeper into history
# The state file automatically skips already-processed PRs
/pr_docs_update.fetch_prs pr_count=20
/pr_docs_update.analyze_prs
/pr_docs_update.update_docs
```

## Advanced Usage

### Custom State File Location

If you want to track state separately for different purposes:

```bash
/pr_docs_update.fetch_prs state_file=".deepwork/pr_docs_copilot_state.json"
/pr_docs_update.analyze_prs
/pr_docs_update.update_docs state_file=".deepwork/pr_docs_copilot_state.json"
```

### Reprocessing Specific PRs

To reprocess specific PRs, edit the state file:

```bash
# View current state
cat .deepwork/pr_docs_state.json

# Remove specific PR numbers you want to reprocess
# Edit the file and remove those numbers from the "processed_prs" array
```

### Processing Large Batches

For initial setup or catching up after a long time:

```bash
# Process 50 PRs at once
/pr_docs_update.fetch_prs pr_count=50
/pr_docs_update.analyze_prs
/pr_docs_update.update_docs
```

## State File Structure

The state file (`.deepwork/pr_docs_state.json`) tracks processed PRs:

```json
{
  "processed_prs": [123, 456, 789],
  "last_update": "2026-01-19T07:00:00Z",
  "total_processed": 3
}
```

## What Gets Updated?

### AGENTS.md Files

For general code changes that all agents should know about:
- New jobs or workflows
- Codebase structure changes
- New conventions or patterns
- Important context for working with the code

Located at: `.deepwork/jobs/[job_name]/AGENTS.md`

### Copilot-Specific Instructions

For changes specific to GitHub Copilot integration:
- Copilot-specific features
- Copilot workflow changes
- Copilot tool usage patterns

Located at: `.github/copilot/` or similar copilot instruction locations

## Scheduling Recommendations

- **Weekly**: Run with default settings (10 PRs) to stay current
- **After Major Releases**: Run with higher count (30-50 PRs)
- **Initial Setup**: Process all recent PRs in batches

## Integration with Existing Workflows

This job can be combined with other DeepWork jobs:

```bash
# Update docs from PRs, then commit the changes
/pr_docs_update.fetch_prs
/pr_docs_update.analyze_prs
/pr_docs_update.update_docs

# Review and commit
/commit.test
/commit.lint
/commit.commit_and_push
```

## Troubleshooting

### No New PRs Found

If all fetched PRs have been processed:
- Increase the `pr_count` parameter
- Check the state file to see what's been processed
- Consider clearing the state file to reprocess all PRs

### GitHub API Rate Limiting

If you hit rate limits:
- Reduce the `pr_count` parameter
- Wait for the rate limit to reset
- Use authenticated GitHub API access if available

### Documentation Files Not Found

If expected documentation files don't exist:
- The job will notify you about missing files
- Create the necessary AGENTS.md or instruction files
- Re-run the update step

## Example Output

After running the job, you'll have:

1. **pr_list.json**: List of fetched PRs (filtered by state)
2. **pr_analysis.md**: Analysis of each PR with recommendations
3. **updated_files_list.md**: Summary of what was updated
4. **Updated documentation files**: AGENTS.md or copilot instructions with new content
5. **Updated state file**: Tracking newly processed PRs
