# Clean Up Errata

## Objective

Remove obsolete files and folders from prior DeepWork versions. This final step cleans up artifacts that are no longer used by the MCP-based system.

## Task

Identify and clean up deprecated files and folders.

### Step 1: Remove Legacy Job Skill Folders

Old DeepWork versions created individual skill folders for each job and step. These need to be removed while preserving the main `deepwork` skill folder.

**Process:**

1. **List all jobs** in `.deepwork/jobs/`:
   ```bash
   ls .deepwork/jobs/
   ```

2. **For each job**, kick off a sub-agent to find and remove legacy skill folders. The sub-agent should:
   - Search in both `.claude/skills/` and `.gemini/skills/`
   - Find folders matching:
     - `{job_name}/` - folder named exactly like the job
     - `{job_name}.*/` - folders starting with the job name followed by a period (e.g., `my_job.step1/`, `my_job.step2/`)
   - Remove each matching folder
   - Report what was removed

   **Example commands for a job named `competitive_research`:**
   ```bash
   # Find and remove from .claude/skills/
   rm -rf .claude/skills/competitive_research/ 2>/dev/null
   rm -rf .claude/skills/competitive_research.*/ 2>/dev/null

   # Find and remove from .gemini/skills/
   rm -rf .gemini/skills/competitive_research/ 2>/dev/null
   rm -rf .gemini/skills/competitive_research.*/ 2>/dev/null
   ```

3. **Run sub-agents in parallel** - one for each job to speed up the process.

4. **Verify the `deepwork` skill folder remains:**
   ```bash
   ls -d .claude/skills/deepwork/ 2>/dev/null || echo "ERROR: deepwork skill missing!"
   ls -d .gemini/skills/deepwork/ 2>/dev/null || echo "WARNING: gemini deepwork skill missing (may not have been installed)"
   ```

   **CRITICAL:** The `deepwork` skill folder in `.claude/skills/deepwork/` MUST still exist after cleanup. If it is missing, something went wrong - do NOT proceed and investigate what happened.

**What this removes:**
```
.claude/skills/
├── competitive_research/     <- REMOVE (legacy job folder)
├── competitive_research.discover/  <- REMOVE (legacy step folder)
├── competitive_research.analyze/   <- REMOVE (legacy step folder)
├── deepwork/                 <- KEEP (current MCP entry point)
└── some_other_job/           <- REMOVE (legacy job folder)
```

**Do NOT remove:**
- `.claude/skills/deepwork/` - This is the current MCP-based skill entry point
- `.gemini/skills/deepwork/` - Same for Gemini
- Any skill folders that don't match job names in `.deepwork/jobs/`

### Step 2: Clean Temp Files

Check `.deepwork/tmp/` for accumulated temporary files:

```bash
ls -la .deepwork/tmp/ 2>/dev/null || echo "No tmp folder"
```

**Safe to delete:**
- `.deepwork/tmp/rules/queue/*.json` - Old rules queue files
- Any files older than 7 days
- Empty subdirectories

**Be careful with:**
- Files that might be in-progress work
- Anything with recent modification times

```bash
# Clean old queue files
rm -rf .deepwork/tmp/rules/queue/*.json 2>/dev/null

# Remove empty directories
find .deepwork/tmp -type d -empty -delete 2>/dev/null
```

### Step 3: Remove Rules Folder (Fully Deprecated)

DeepWork Rules have been completely removed from the system. The `.deepwork/rules/` folder should be deleted.

```bash
ls -la .deepwork/rules/ 2>/dev/null || echo "No rules folder (good!)"
```

**If the folder exists:**

1. **Back up the folder** (in case user wants to reference old rules):
   ```bash
   mv .deepwork/rules/ .deepwork/rules.backup/
   ```

2. **Inform the user** that DeepWork Rules are deprecated and the folder has been backed up

3. **After user confirms** the backup is acceptable, the backup can be deleted later

**Also remove these related items if present:**
- `.deepwork/tmp/rules/` folder and all contents
- `.deepwork/jobs/deepwork_rules/` folder (the old rules job)
- Any `deepwork_rules` job that may have been installed

```bash
rm -rf .deepwork/tmp/rules/ 2>/dev/null
rm -rf .deepwork/jobs/deepwork_rules/ 2>/dev/null
```

### Step 4: Update Config Version

Check `.deepwork/config.yml` for outdated version format:

```bash
cat .deepwork/config.yml
```

**Old format:**
```yaml
version: 1.0.0
platforms:
- claude
```

**Current format:**
```yaml
version: "1.0"
platforms:
  - claude
```

Update if needed to match current schema expectations.

### Step 5: Remove Other Obsolete Files

Check for and remove other obsolete files:

| File/Pattern | Description | Action |
|--------------|-------------|--------|
| `.deepwork/.last_head_ref` | Git state tracking | Keep (used by MCP) |
| `.deepwork/.last_work_tree` | Git state tracking | Keep (used by MCP) |
| `.deepwork/.gitignore` | Ignore patterns | Review and update |
| `.claude/commands/` | Generated commands | Keep (current system) |
| `.claude/settings.local.json` | Local overrides | Keep (user settings) |

### Step 6: Verify Git Status

Check that the cleanup hasn't left untracked garbage:

```bash
git status
```

**Review:**
- Deleted files should show as deleted
- No new untracked files should appear (unless intentionally created)
- Backup files (`.backup`) should be in `.gitignore` or cleaned up

## Quality Criteria

- Legacy job skill folders are removed from `.claude/skills/` and `.gemini/skills/` (folders matching job names or `jobname.*` patterns)
- The `deepwork` skill folder in `.claude/skills/deepwork/` still exists after cleanup
- `.deepwork/tmp/` contents are cleaned appropriately
- `.deepwork/rules/` folder is backed up and removed (DeepWork Rules fully deprecated)
- `.deepwork/tmp/rules/` folder is removed
- `.deepwork/jobs/deepwork_rules/` folder is removed if present
- `.deepwork/config.yml` uses current version format
- Git status shows clean changes ready to commit
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Important Notes

1. **Always back up before deleting** - User data is irreplaceable
2. **Ask before destructive actions** - When in doubt, ask the user
3. **Don't auto-commit** - Let the user review and commit changes themselves
