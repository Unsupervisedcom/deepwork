# Clean Up Errata

## Objective

Remove obsolete files and folders from prior DeepWork versions. This final step cleans up artifacts that are no longer used by the MCP-based system, creating a summary of all changes made during the repair workflow.

## Task

Identify and clean up deprecated files and folders, then create a comprehensive summary document.

### Step 1: Handle Old Skills Folder

Check if `.claude/skills/` exists. This folder was used by the old skill-based system and is no longer needed.

```bash
ls -la .claude/skills/ 2>/dev/null || echo "No skills folder (good!)"
```

**If it exists:**
1. Count the contents: `ls .claude/skills/ | wc -l`
2. Ask the user whether to:
   - **Delete** the folder entirely (recommended if migrated to MCP)
   - **Back up** to `.claude/skills.backup/` before deleting
   - **Keep** if they have custom skills not yet migrated

**Old skill structure to recognize:**
```
.claude/skills/
├── job_name/
│   └── SKILL.md
├── job_name.step_name/
│   └── SKILL.md
└── ...
```

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

### Step 7: Create Repair Summary

Create a `repair_summary.md` file documenting all changes made during this workflow:

```markdown
# DeepWork Repair Summary

**Date:** [current date]
**Project:** [project name]

## Settings Fixes (fix_settings step)

- [ ] Removed X `Skill(...)` permission entries
- [ ] Consolidated Y duplicate hooks
- [ ] Removed Z hardcoded paths
- [ ] Removed deprecated `deepwork hook` commands

## Job Fixes (fix_jobs step)

### [job_name]
- [ ] Removed `exposed` field from steps: [list]
- [ ] Migrated `stop_hooks` to `hooks.after_agent`
- [ ] Updated workflow to remove `review_job_spec`
- [ ] Version bumped to X.Y.Z

### [another_job]
- [ ] ...

## Errata Cleanup (errata step)

- [ ] Handled `.claude/skills/` folder: [deleted/backed up/kept]
- [ ] Cleaned `.deepwork/tmp/`: removed X files
- [ ] Reviewed `.deepwork/rules/`: [action taken]
- [ ] Updated `.deepwork/config.yml` version format

## Files Changed

```
[list of all files modified/deleted]
```

## Recommended Next Steps

1. Review changes with `git diff`
2. Test that `deepwork sync` runs without errors
3. Commit changes with message: "chore: migrate to DeepWork MCP format"
4. Delete backup files after confirming everything works
```

## Quality Criteria

- `.claude/skills/` folder is handled (removed, backed up, or documented why kept)
- `.deepwork/tmp/` contents are cleaned appropriately
- `.deepwork/rules/` folder is backed up and removed (DeepWork Rules fully deprecated)
- `.deepwork/tmp/rules/` folder is removed
- `.deepwork/jobs/deepwork_rules/` folder is removed if present
- `.deepwork/config.yml` uses current version format
- A `repair_summary.md` file is created documenting all changes
- Git status shows clean changes ready to commit
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Example Summary Output

```markdown
# DeepWork Repair Summary

**Date:** 2024-02-04
**Project:** internal-agentspace

## Settings Fixes

- Removed 87 `Skill(...)` permission entries
- Consolidated 2 duplicate `UserPromptSubmit` hooks into 1
- Removed hardcoded path: `/Users/tyler/.local/pipx/venvs/deepwork/bin/python`
- Removed 3 deprecated `deepwork hook rules_check` commands

## Job Fixes

### deepwork_jobs
- Updated from old version (workflow includes `review_job_spec`)
- Reinstalled with `deepwork install --platform claude`

### competitive_research
- Removed `exposed: true` from `discover_competitors` step
- Migrated 1 `stop_hooks` to `hooks.after_agent`
- Version bumped to 1.0.1

## Errata Cleanup

- Backed up `.claude/skills/` to `.claude/skills.backup/` (174 files)
- Deleted `.claude/skills/` folder
- Cleaned `.deepwork/tmp/rules/queue/` (12 old JSON files)
- Kept `.deepwork/rules/` (contains active example rules)
- Updated `.deepwork/config.yml` version to "1.0"

## Recommended Next Steps

1. `git add -A && git diff --staged`
2. `deepwork sync` (verify no errors)
3. `git commit -m "chore: migrate to DeepWork MCP format"`
4. After testing: `rm -rf .claude/skills.backup/`
```

## Important Notes

1. **Always back up before deleting** - User data is irreplaceable
2. **Ask before destructive actions** - When in doubt, ask the user
3. **Document everything** - The summary is valuable for understanding what changed
4. **Don't auto-commit** - Let the user review and commit changes themselves
