# Fix Settings Files

## Objective

Clean up `.claude/settings.json` and related configuration files, removing legacy artifacts from prior DeepWork versions. This step ensures the Claude Code settings are free of deprecated permissions, duplicate hooks, and hardcoded paths.

## Task

Audit and repair the `.claude/settings.json` file, removing gunk accumulated from older DeepWork implementations.

### Step 1: Create Backup

Before making any changes, create a backup:

```bash
cp .claude/settings.json .claude/settings.json.backup
```

### Step 2: Inventory DeepWork Jobs

First, get the list of jobs that exist in `.deepwork/jobs/`:

```bash
ls .deepwork/jobs/
```

Note these job names - you will use them to identify which `Skill(...)` entries to remove.

### Step 3: Remove DeepWork Skill Permissions

Look for and **remove** `Skill(...)` permission entries that match DeepWork jobs. Only remove entries where the skill name matches a job in `.deepwork/jobs/`.

**What to look for:**
```json
"permissions": {
  "allow": [
    "Skill(deepwork_jobs)",           // Remove if 'deepwork_jobs' is in .deepwork/jobs/
    "Skill(deepwork_jobs.define)",    // Remove - matches job_name.step pattern
    "Skill(competitive_research)",    // Remove if 'competitive_research' is in .deepwork/jobs/
    "Skill(my_custom_skill)",         // KEEP - not a DeepWork job
    ...
  ]
}
```

**IMPORTANT:** Only remove skills that:
- Exactly match a job name in `.deepwork/jobs/` (e.g., `Skill(job_name)`)
- Match the pattern `job_name.step_name` where `job_name` is in `.deepwork/jobs/`

**DO NOT remove** skills that don't match DeepWork jobs - the user may have created these manually for other purposes.

### Step 4: Remove Duplicate Hooks

Check for duplicate hook entries in the `hooks` section. Prior versions sometimes added the same hook multiple times.

**Example of duplicates to consolidate:**
```json
"hooks": {
  "UserPromptSubmit": [
    {
      "matcher": "",
      "hooks": [{ "type": "command", "command": "some_command" }]
    },
    {
      "matcher": "",
      "hooks": [{ "type": "command", "command": "some_command" }]  // DUPLICATE
    }
  ]
}
```

Keep only one instance of each unique hook.

### Step 5: Remove Hardcoded User Paths

Search for and remove any hardcoded paths that reference specific user directories:

**Patterns to find and remove:**
- `/Users/username/.local/pipx/venvs/deepwork/bin/python`
- `/home/username/.local/...`
- Any path containing a specific username

These should either be removed or replaced with relative paths.

### Step 6: Remove DeepWork Rules Hooks (Fully Deprecated)

DeepWork Rules have been completely removed from the system. Remove ALL hooks related to rules:

**Hooks to remove entirely:**
- Any hook with command `deepwork hook rules_check`
- Any hook with command containing `rules_check`
- Any hook referencing `.deepwork/jobs/deepwork_rules/hooks/`
- Any hook referencing `.deepwork/rules/`

**Also remove these permissions if present:**
- `Skill(deepwork_rules)`
- `Skill(deepwork_rules.define)`
- `Bash(rm -rf .deepwork/tmp/rules/queue/*.json)`

### Step 7: Remove Other Deprecated Commands

Remove hooks referencing other deprecated DeepWork commands:

**Commands to remove:**
- `deepwork hook *` - The entire hook subcommand is deprecated
- References to any `.deepwork/jobs/*/hooks/` scripts

### Step 8: Clean Up Empty Sections

If after cleanup any sections are empty, consider removing them:

```json
// Remove if empty:
"hooks": {
  "Stop": []  // Remove this empty array
}
```

### Step 9: Validate JSON

After all edits, ensure the file is valid JSON:

```bash
python -c "import json; json.load(open('.claude/settings.json'))"
```

If there are syntax errors, fix them before proceeding.

## Example Before/After

### Before (with gunk):
```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "matcher": "", "hooks": [{ "type": "command", "command": ".deepwork/jobs/deepwork_rules/hooks/user_prompt_submit.sh" }] },
      { "matcher": "", "hooks": [{ "type": "command", "command": ".deepwork/jobs/deepwork_rules/hooks/user_prompt_submit.sh" }] }
    ],
    "Stop": [
      { "matcher": "", "hooks": [{ "type": "command", "command": "deepwork hook rules_check" }] }
    ],
    "SubagentStop": [
      { "matcher": "", "hooks": [{ "type": "command", "command": "/Users/tyler/.local/pipx/venvs/deepwork/bin/python -m deepwork.hooks.rules_check" }] }
    ]
  },
  "permissions": {
    "allow": [
      "Skill(competitive_research)",
      "Skill(competitive_research.discover_competitors)",
      "Skill(deepwork_jobs)",
      "Skill(deepwork_jobs.define)",
      "Read(./.deepwork/**)",
      "WebSearch"
    ]
  }
}
```

### After (cleaned):
```json
{
  "hooks": {},
  "permissions": {
    "allow": [
      "Read(./.deepwork/**)",
      "WebSearch"
    ]
  }
}
```

## Important Notes

1. **Don't remove non-DeepWork permissions** - Keep permissions like `WebSearch`, `Read(...)`, `Bash(...)` that aren't related to old DeepWork skills
2. **Preserve `make_new_job.sh`** - Keep any `Bash(...)` permission referencing `make_new_job.sh` (e.g., `Bash(.deepwork/jobs/deepwork_jobs/scripts/make_new_job.sh *)`) - this is a current DeepWork script
3. **Be conservative** - If unsure whether something is legacy, ask the user
4. **Document changes** - Note what was removed for the final summary
