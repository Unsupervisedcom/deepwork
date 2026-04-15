"""Ensure ~/.claude/settings.json is configured for DeepWork."""

from __future__ import annotations

import json
from pathlib import Path

MARKETPLACE_KEY = "deepwork-plugins"
MARKETPLACE_SOURCE = {
    "source": "github",
    "repo": "Unsupervisedcom/deepwork",
}
PLUGIN_KEY = "deepwork@deepwork-plugins"
MCP_PERMISSION = "mcp__plugin_deepwork_deepwork__*"
# Permissions granting full access to .deepwork/ in every project.
# Leading slash makes the path project-root-relative (per Claude Code docs),
# so these rules apply to `.deepwork/**/*` in each project, not `~/.deepwork/`.
DEEPWORK_DIR_PERMISSIONS = [
    "Read(/.deepwork/**/*)",
    "Write(/.deepwork/**/*)",
    "Edit(/.deepwork/**/*)",
]
# Bash permissions for commands the plugin routinely runs.
# Without these, each invocation triggers a permission prompt.
# The uv cache glob covers hash-varying archive paths that change on reinstall.
BASH_PERMISSIONS = [
    "Bash(deepwork:*)",
    "Bash(uvx deepwork:*)",
    "Bash(~/.cache/uv/archive-v0/*/bin/deepwork:*)",
    "Bash(command -v uv)",
    "Bash(uv --version)",
]


def claude_setup() -> list[str]:
    """Configure ~/.claude/settings.json for DeepWork.

    Returns a list of human-readable messages describing what changed.
    If nothing changed, returns an empty list.
    """
    settings_path = Path.home() / ".claude" / "settings.json"

    if settings_path.exists():
        settings = json.loads(settings_path.read_text())
    else:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = {}

    changes: list[str] = []

    # 1. Ensure marketplace is registered in extraKnownMarketplaces
    marketplaces = settings.setdefault("extraKnownMarketplaces", {})
    if MARKETPLACE_KEY not in marketplaces:
        marketplaces[MARKETPLACE_KEY] = {
            "source": MARKETPLACE_SOURCE,
            "autoUpdate": True,
        }
        changes.append(f"Added '{MARKETPLACE_KEY}' to extraKnownMarketplaces")
    else:
        entry = marketplaces[MARKETPLACE_KEY]
        existing_source = entry.get("source", {})
        if (
            existing_source.get("source") != MARKETPLACE_SOURCE["source"]
            or existing_source.get("repo") != MARKETPLACE_SOURCE["repo"]
        ):
            entry["source"] = MARKETPLACE_SOURCE
            changes.append(f"Updated '{MARKETPLACE_KEY}' marketplace source")
        if entry.get("autoUpdate") is not True:
            entry["autoUpdate"] = True
            changes.append(f"Enabled auto-update for '{MARKETPLACE_KEY}' marketplace")

    # 2. Ensure plugin is enabled
    enabled_plugins = settings.setdefault("enabledPlugins", {})
    if enabled_plugins.get(PLUGIN_KEY) is not True:
        enabled_plugins[PLUGIN_KEY] = True
        changes.append(f"Enabled plugin '{PLUGIN_KEY}'")

    # 3. Ensure MCP tool permission is in allow list
    permissions = settings.setdefault("permissions", {})
    allow = permissions.setdefault("allow", [])
    if MCP_PERMISSION not in allow:
        allow.append(MCP_PERMISSION)
        changes.append(f"Added '{MCP_PERMISSION}' to permissions.allow")

    # 4. Ensure full access to .deepwork/ in every project
    for perm in DEEPWORK_DIR_PERMISSIONS:
        if perm not in allow:
            allow.append(perm)
            changes.append(f"Added '{perm}' to permissions.allow")

    # 5. Pre-grant Bash permissions for common plugin operations
    for perm in BASH_PERMISSIONS:
        if perm not in allow:
            allow.append(perm)
            changes.append(f"Added '{perm}' to permissions.allow")

    if changes:
        settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    return changes
