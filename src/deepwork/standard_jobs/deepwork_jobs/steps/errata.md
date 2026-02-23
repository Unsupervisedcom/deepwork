# Clean Up Errata

## Objective

Remove obsolete files and folders from prior DeepWork versions. This final step cleans up artifacts that are no longer used by the MCP-based system.

## Task

Identify and clean up deprecated files and folders.

### Step 1: Remove Legacy Job Skill Folders

Old DeepWork versions created individual skill folders for each job and step. These need to be removed, including the main `deepwork` skill folder (which is now provided by the plugin system and no longer belongs in the repo).

**Process:**

1. **List all jobs** in `.deepwork/jobs/`:
   ```bash
   ls .deepwork/jobs/
   ```

2. **Kick off a single sub-agent** to remove all legacy skill folders for every job at once. Be concise — output minimal text, only reporting what was removed or confirming nothing was found. The sub-agent should:
   - For each job in `.deepwork/jobs/`, search in both `.claude/skills/` and `.gemini/skills/` for folders matching:
     - `{job_name}/` - folder named exactly like the job
     - `{job_name}.*/` - folders starting with the job name followed by a period (e.g., `my_job.step1/`, `my_job.step2/`)
   - Remove each matching folder
   - **Also remove** `.claude/skills/deepwork/` and `.gemini/skills/deepwork/` — the `deepwork` skill is now provided by the plugin system and should not exist in the repo
   - Report only: what was removed (one line per folder) or "No legacy folders found"

   **Example commands for a job named `competitive_research`:**
   ```bash
   # Find and remove from .claude/skills/
   rm -rf .claude/skills/competitive_research/ 2>/dev/null
   rm -rf .claude/skills/competitive_research.*/ 2>/dev/null

   # Find and remove from .gemini/skills/
   rm -rf .gemini/skills/competitive_research/ 2>/dev/null
   rm -rf .gemini/skills/competitive_research.*/ 2>/dev/null
   ```

3. **Remove the `deepwork` skill folders** (now provided by the plugin):
   ```bash
   rm -rf .claude/skills/deepwork/ 2>/dev/null
   rm -rf .gemini/skills/deepwork/ 2>/dev/null
   ```

**What this removes:**
```
.claude/skills/
├── competitive_research/     <- REMOVE (legacy job folder)
├── competitive_research.discover/  <- REMOVE (legacy step folder)
├── competitive_research.analyze/   <- REMOVE (legacy step folder)
├── deepwork/                 <- REMOVE (now provided by plugin)
└── some_other_job/           <- REMOVE (legacy job folder)
```

**Do NOT remove:**
- Any skill folders that don't match job names in `.deepwork/jobs/` (and aren't `deepwork/`)

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
- Anything modified within the last 24 hours

```bash
# Clean old queue files
rm -rf .deepwork/tmp/rules/queue/*.json 2>/dev/null

# Remove empty directories
find .deepwork/tmp -type d -empty -delete 2>/dev/null
```

### Step 3: Remove Rules Folder (Fully Deprecated)

DeepWork Rules have been completely removed from the system. Delete the `.deepwork/rules/` folder and all related items:

```bash
rm -rf .deepwork/rules/ 2>/dev/null
rm -rf .deepwork/tmp/rules/ 2>/dev/null
rm -rf .deepwork/jobs/deepwork_rules/ 2>/dev/null
```

### Step 4: Update Config Version

Check `.deepwork/config.yml` for outdated version format. If the file does not exist, skip this step.

```bash
cat .deepwork/config.yml 2>/dev/null || echo "No config.yml found — skipping"
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

### Step 5: Remove `deepwork serve` from `.mcp.json`

Old DeepWork versions added a `deepwork serve` MCP server entry directly to the repo's `.mcp.json` file. This is now handled by the plugin system and must be removed.

**Process:**

1. Check if `.mcp.json` exists in the repo root:
   ```bash
   cat .mcp.json 2>/dev/null || echo "No .mcp.json found"
   ```

2. If it exists, look for any entry whose `command` is `deepwork` with `serve` as an argument (e.g., `"command": "deepwork", "args": ["serve"]` or `"command": "uvx", "args": ["deepwork", "serve", ...]`). Remove that entire server entry.

3. If `.mcp.json` becomes empty (no remaining server entries) after removal, delete the file entirely:
   ```bash
   rm .mcp.json
   ```

4. If other MCP servers remain, keep the file with only the `deepwork serve` entry removed.

**Example `.mcp.json` before cleanup:**
```json
{
  "mcpServers": {
    "deepwork": {
      "command": "uvx",
      "args": ["deepwork", "serve"]
    },
    "other-server": {
      "command": "some-tool",
      "args": ["serve"]
    }
  }
}
```

**After cleanup (other servers remain):**
```json
{
  "mcpServers": {
    "other-server": {
      "command": "some-tool",
      "args": ["serve"]
    }
  }
}
```

### Step 6: Remove Other Obsolete Files

Check for and remove other obsolete files:

| File/Pattern | Description | Action |
|--------------|-------------|--------|
| `.deepwork/.last_head_ref` | Git state tracking | Keep (used by MCP) |
| `.deepwork/.last_work_tree` | Git state tracking | Keep (used by MCP) |
| `.deepwork/.gitignore` | Ignore patterns | Keep (ensure `tmp/` and `*.backup` are listed) |
| `.claude/commands/` | Generated commands | Keep (current system) |
| `.claude/settings.local.json` | Local overrides | Keep (user settings) |

### Step 7: Verify Git Status

Check that the cleanup hasn't left untracked garbage:

```bash
git status
```

**Review:**
- Deleted files should show as deleted
- No new untracked files should appear (unless intentionally created)
- Backup files (`.backup`) should be in `.gitignore` or cleaned up

## Important Notes

1. **Always back up before deleting** - User data is irreplaceable
2. **Ask before destructive actions** - When in doubt, ask the user
3. **Don't auto-commit** - Let the user review and commit changes themselves
