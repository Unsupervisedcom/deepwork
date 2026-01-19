# Fetch Recently Merged PRs

## Objective

Retrieve a list of recently merged pull requests from GitHub and filter out any that have already been processed, based on a state file.

## Task

Fetch recently merged PRs from the current repository and prepare a list of unprocessed PRs for analysis.

### Step 1: Understand the Parameters

1. **PR Count**: Determine how many recent PRs to fetch
   - Default: 10 PRs
   - If user specified a count, use that value
   - Can fetch more to go deeper into history

2. **State File**: Load the state file to track processed PRs
   - Default location: `.deepwork/pr_docs_state.json`
   - If file doesn't exist, create it with an empty list
   - File format: `{"processed_prs": [123, 456, 789]}`

### Step 2: Fetch Merged PRs from GitHub

Use GitHub tools available to you to fetch recently merged pull requests:

1. **Get the repository information**
   - Repository owner and name from current git repository
   - Use `git remote -v` to identify the GitHub repository

2. **Fetch merged PRs**
   - Use GitHub API or available GitHub tools to list merged pull requests
   - Sort by merge date (most recent first)
   - Fetch the number requested (default 10, or user-specified count)
   
3. **For each PR, collect**:
   - PR number
   - Title
   - Description/body
   - Merge date
   - Author
   - Labels (if any)
   - Changed files (summary)
   - Link to the PR

### Step 3: Filter Out Already Processed PRs

1. **Load the state file**
   - Read `.deepwork/pr_docs_state.json` (or user-specified path)
   - Parse the JSON to get the list of processed PR numbers
   - If file doesn't exist, treat it as empty (no processed PRs)

2. **Filter the PR list**
   - Remove PRs whose numbers are in the `processed_prs` list
   - Keep only unprocessed PRs

3. **Handle the case of no new PRs**
   - If all fetched PRs have been processed, inform the user
   - Suggest fetching more PRs by increasing the count
   - Recommend using a larger `pr_count` value to go deeper into history

### Step 4: Create Output File

Create `pr_list.json` with the following structure:

```json
{
  "repository": "owner/repo-name",
  "fetch_date": "2026-01-19T07:00:00Z",
  "total_fetched": 10,
  "new_prs": 5,
  "prs": [
    {
      "number": 123,
      "title": "Add new feature",
      "description": "This PR adds...",
      "merge_date": "2026-01-15T10:30:00Z",
      "author": "username",
      "labels": ["enhancement", "documentation"],
      "changed_files": ["src/feature.py", "docs/README.md"],
      "url": "https://github.com/owner/repo/pull/123"
    }
  ]
}
```

## Output Format

- **File**: `pr_list.json`
- **Content**: JSON structure with repository info and list of unprocessed merged PRs
- **Location**: Current working directory

## Quality Criteria

- ✓ Repository information correctly identified from git remote
- ✓ At least the requested number of PRs fetched (unless fewer exist)
- ✓ State file loaded (or created if missing)
- ✓ Already-processed PRs filtered out
- ✓ PR data includes all required fields (number, title, description, merge_date, author, url)
- ✓ Output file created with valid JSON structure
- ✓ If no new PRs found, user informed about options to fetch more

## Notes

- This step uses GitHub API access, which may require authentication
- If you encounter rate limiting, inform the user
- The state file prevents duplicate processing across multiple runs
- Users can delete or edit the state file to reprocess specific PRs if needed
