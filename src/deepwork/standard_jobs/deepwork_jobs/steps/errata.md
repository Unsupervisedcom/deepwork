# Clean Up Errata

## Objective

Remove obsolete files and folders from prior DeepWork versions. This final step cleans up artifacts that are no longer used by the MCP-based system.

## Task

Identify and clean up deprecated files and folders.

### Step 1: Clean Temp Files

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

### Step 2: Remove Rules Folder (Fully Deprecated)

DeepWork Rules have been completely removed from the system. Delete the `.deepwork/rules/` folder and all related items:

```bash
rm -rf .deepwork/rules/ 2>/dev/null
rm -rf .deepwork/tmp/rules/ 2>/dev/null
rm -rf .deepwork/jobs/deepwork_rules/ 2>/dev/null
```

### Step 3: Update Config Version

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

### Step 4: Remove `deepwork serve` from `.mcp.json`

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

### Step 5: Remove Other Obsolete Files

Check for and remove other obsolete files:

| File/Pattern | Description | Action |
|--------------|-------------|--------|
| `.deepwork/.last_head_ref` | Git state tracking | Keep (used by MCP) |
| `.deepwork/.last_work_tree` | Git state tracking | Keep (used by MCP) |
| `.deepwork/.gitignore` | Ignore patterns | Keep (ensure `tmp/` and `*.backup` are listed) |
| `.claude/commands/` | Generated commands | Keep (current system) |
| `.claude/settings.local.json` | Local overrides | Keep (user settings) |

### Step 6: Library Job Access via Nix Dev Shell

Library jobs replace some patterns previously handled by copied job files. This step ensures users are aware of the recommended setup path.

Check whether the project uses a Nix flake devshell and whether shared library jobs are configured.

**Detection logic:**

1. Check if `flake.nix` exists in the repo root:
   ```bash
   test -f flake.nix && echo "flake found" || echo "no flake"
   ```

2. **If `flake.nix` exists**, check whether it already sets `DEEPWORK_ADDITIONAL_JOBS_FOLDERS`:
   ```bash
   grep -q 'DEEPWORK_ADDITIONAL_JOBS_FOLDERS' flake.nix && echo "already configured" || echo "not configured"
   ```

3. **If already configured**: Do nothing. No output about library jobs — this is silent.

4. **If `flake.nix` exists but library jobs are NOT configured**: Offer to set it up. Tell the user:
   > Your project uses a Nix flake. You can access shared DeepWork library jobs by adding a sparse checkout to your shellHook. This keeps library jobs live and up-to-date without copying them into your project.

   Then suggest adding to their `flake.nix` shellHook:
   ```nix
   shellHook = ''
     export REPO_ROOT=$(git rev-parse --show-toplevel)

     # Clone DeepWork library jobs if not present
     if [ ! -d "$REPO_ROOT/.deepwork/upstream" ]; then
       git clone --sparse --filter=blob:none \
         https://github.com/Unsupervisedcom/deepwork.git \
         "$REPO_ROOT/.deepwork/upstream"
       git -C "$REPO_ROOT/.deepwork/upstream" sparse-checkout set --cone library/jobs/
     fi

     export DEEPWORK_ADDITIONAL_JOBS_FOLDERS="$REPO_ROOT/.deepwork/upstream/library/jobs"
   '';
   ```

   And adding `.deepwork/upstream/` to `.gitignore`.

   If the user wants only specific library jobs, they can use sparse checkout to include/exclude:
   ```bash
   # Check out only specific jobs
   git -C .deepwork/upstream sparse-checkout set --cone library/jobs/repo/

   # Add more later
   git -C .deepwork/upstream sparse-checkout add library/jobs/spec_driven_development/
   ```

5. **If no `flake.nix` exists**: Mention it as an option. Tell the user:
   > DeepWork library jobs can be accessed via a Nix dev shell with `DEEPWORK_ADDITIONAL_JOBS_FOLDERS`. See `library/jobs/README.md` in the DeepWork repo for setup instructions.

   Do not go into detail — just make the user aware.

### Step 7: Verify Git Status

Check that the cleanup hasn't left untracked garbage:

```bash
git status
```

**Review:**
- Deleted files should show as deleted
- No new untracked files should appear (unless intentionally created)
- Backup files (`.backup`) should be in `.gitignore` or cleaned up

## Quality Criteria

- `.deepwork/rules/` folder is gone
- `.deepwork/jobs/deepwork_rules/` is gone
- The `deepwork serve` entry is removed from `.mcp.json` (or the file is deleted if empty)

## Important Notes

1. **Always back up before deleting** - User data is irreplaceable
2. **Ask before destructive actions** - When in doubt, ask the user
3. **Don't auto-commit** - Let the user review and commit changes themselves
