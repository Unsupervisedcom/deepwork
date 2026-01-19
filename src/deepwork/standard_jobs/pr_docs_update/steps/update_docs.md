# Update Documentation

## Objective

Update AGENTS.md files or copilot-specific instructions based on the PR analysis, and track processed PRs in the state file to prevent duplicate processing in future runs.

## Task

Apply the documentation recommendations from the analysis step, update the appropriate files, and maintain the state file for tracking.

### Step 1: Load the Analysis

1. **Read `pr_analysis.md`**
   - Parse the recommendations
   - Identify which files need updates
   - Group updates by target file

2. **Load the state file**
   - Read `.deepwork/pr_docs_state.json` (or user-specified path)
   - Prepare to add newly processed PR numbers

### Step 2: Identify Target Documentation Files

Based on the analysis, determine which documentation files to update:

1. **AGENTS.md files**
   - Check for existing AGENTS.md files in relevant job directories
   - Typical locations:
     - `.deepwork/jobs/[job_name]/AGENTS.md`
     - `src/deepwork/standard_jobs/[job_name]/AGENTS.md`
   - If no AGENTS.md exists for relevant jobs, consider creating one

2. **Copilot-specific instructions**
   - Look for copilot instruction files
   - Common locations might include:
     - `.github/copilot/`
     - `.copilot/`
     - Other copilot-specific configuration locations
   - If no copilot instructions exist and updates are needed, note this for the user

3. **Create an update plan**
   - List all files to be updated
   - Organize updates by file to minimize context switching

### Step 3: Update Documentation Files

For each documentation file identified:

1. **Review existing content**
   - Read the current file content
   - Understand the existing structure and sections
   - Identify where new content should be added

2. **Apply updates**
   - Add new information based on PR analysis
   - Include PR reference numbers for traceability
   - Follow the existing format and style
   - Maintain chronological order if applicable
   - Keep entries clear and concise

3. **AGENTS.md format example**:
   ```markdown
   ## Last Updated
   
   - Date: 2026-01-19
   - From: PR documentation sync (PRs #123, #456)
   
   ## Recent Changes
   
   ### PR #123: New Automated Testing Job
   - A new job type for automated testing is now available
   - Location: `.deepwork/jobs/automated_test/`
   - Use this for test automation workflows
   - See job.yml for full specification
   ```

4. **Handle multiple file updates**
   - Update all relevant files identified in the analysis
   - Maintain consistency across updates
   - Ensure cross-references are accurate

### Step 4: Update State File

1. **Collect processed PR numbers**
   - Extract PR numbers from the analysis
   - Include all PRs (both relevant and not relevant)
   - This ensures we don't reprocess any PRs

2. **Update the state file**
   - Load existing `processed_prs` list
   - Add new PR numbers to the list
   - Remove duplicates if any
   - Sort the list (optional, for readability)

3. **Write the updated state file**
   ```json
   {
     "processed_prs": [123, 456, 789, 1011, 1213],
     "last_update": "2026-01-19T07:00:00Z",
     "total_processed": 5
   }
   ```

### Step 5: Create Summary Report

Create `updated_files_list.md` documenting what was done:

```markdown
# Documentation Update Summary

**Date**: 2026-01-19
**PRs Processed**: 5 (PRs #123, #456, #789, #1011, #1213)
**Files Updated**: 2

## Updated Files

### .deepwork/jobs/deepwork_jobs/AGENTS.md
- Added information about new automated testing job (PR #123)
- Updated last modified date

### .github/copilot/instructions.md
- Documented new copilot command syntax (PR #456)
- Added usage examples

## State File Updated

- State file: `.deepwork/pr_docs_state.json`
- New processed PRs added: 5
- Total PRs tracked: 15

## PRs Processed But Not Documented

- PR #789: Minor typo fix (not relevant)
- PR #1011: Internal refactoring (no documentation impact)
- PR #1213: CI configuration (no agent-visible changes)

## Next Steps

To process more PRs from further back in history, run this job again with:
- Increase `pr_count` parameter (e.g., 20 or 30)
- The state file will automatically skip already processed PRs
```

## Output Format

- **File**: `updated_files_list.md`
- **Content**: Summary of changes made and files updated
- **Location**: Current working directory

## Quality Criteria

- ✓ All relevant documentation files identified and updated
- ✓ Updates include PR references for traceability
- ✓ Existing file structure and format maintained
- ✓ State file updated with all processed PR numbers
- ✓ State file includes metadata (last_update, total_processed)
- ✓ Summary report created with clear list of changes
- ✓ Changes are ready to be committed
- ✓ If no files exist for updates, user is informed

## Notes

- If AGENTS.md files don't exist in expected locations, ask the user if they should be created
- Maintain the existing tone and style of documentation files
- Include enough context so future readers understand the changes
- The state file enables incremental processing across multiple runs
- Users can manually edit the state file to reprocess specific PRs if needed
- Consider running a git diff to show the user what changed before committing
