# Codex Local Dev Debugging History

## 2026-03-31: Stale Worktree Paths in Local Codex Dev Setup

### Symptoms
Codex restarts still loaded DeepWork from an older worktree even after switching to a newer checkout. The local marketplace entry existed, but the active MCP server in `~/.codex/config.toml` still pointed at a stale worktree path.

### Investigation
Compared the current checkout with an older DeepWork worktree and found an existing helper script there: `scripts/setup_codex_local_dev.sh`. The older script maintained the home-local marketplace entry and `~/plugins/deepwork` symlink, but it did not update `~/.codex/config.toml`.

### Root Cause
The local-dev helper handled plugin symlinks and marketplace metadata only. Codex's active MCP server configuration lived separately in `~/.codex/config.toml`, so switching worktrees could leave `deepwork_current_repo` pointing at an obsolete checkout.

Separately, this branch also had a half-created Codex plugin directory under
`plugins/deepwork/` with empty subdirectories but no manifest, no plugin MCP
config, and no skill files. That made the local registration point at a bundle
Codex could not load.

### The Fix
Ported `scripts/setup_codex_local_dev.sh` into this checkout and extended it to:
- mark the current checkout as trusted in `~/.codex/config.toml`
- repoint `mcp_servers.deepwork_current_repo` to the current repo root
- report `changed` versus `no-op`
- tell the user to restart Codex only when it actually changed local state

The script still updates `~/plugins/deepwork` and `~/.agents/plugins/marketplace.json` when a repo-local Codex plugin bundle exists.

Added the missing Codex plugin bundle files in-repo:
- `.agents/plugins/marketplace.json`
- `plugins/deepwork/.codex-plugin/plugin.json`
- `plugins/deepwork/.mcp.json`
- `plugins/deepwork/README_REVIEWS.md`
- `plugins/deepwork/example_reviews/*`
- `plugins/deepwork/skills/*/SKILL.md`

Extended the repo-local Codex hooks to cover DeepSchema write/edit validation in
addition to startup context restoration and post-commit review reminders.

### Test Cases Affected
- `tests/unit/test_setup_codex_local_dev.py`
- `tests/unit/plugins/test_codex_plugin.py`

### Key Learnings
- Codex local dev state is split across the plugin marketplace/symlink layer and `~/.codex/config.toml`; both must be updated when moving between worktrees.
- A local marketplace entry is not enough by itself; the referenced plugin directory must contain an actual Codex bundle.
- A local setup helper should be explicit and idempotent, and it should tell the user whether a restart is necessary.

### Related Files
- `scripts/setup_codex_local_dev.sh`
- `.agents/plugins/marketplace.json`
- `plugins/deepwork/.codex-plugin/plugin.json`
- `plugins/deepwork/.mcp.json`
- `plugins/deepwork/README_REVIEWS.md`
- `tests/unit/test_setup_codex_local_dev.py`
- `tests/unit/plugins/test_codex_plugin.py`
- `AGENTS.md`
- `CONTRIBUTING.md`
