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
# All permissions to add to settings.permissions.allow.
ALLOW_PERMISSIONS = [
    # MCP tools
    "mcp__plugin_deepwork_deepwork__*",
    # .deepwork/ directory access (leading slash = project-root-relative)
    "Read(/.deepwork/**/*)",
    "Write(/.deepwork/**/*)",
    "Edit(/.deepwork/**/*)",
    # Bash commands the plugin routinely runs (uv cache glob covers hash-varying paths)
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

    # 3. Ensure all required permissions are in allow list
    permissions = settings.setdefault("permissions", {})
    allow = permissions.setdefault("allow", [])
    for perm in ALLOW_PERMISSIONS:
        if perm not in allow:
            allow.append(perm)
            changes.append(f"Added '{perm}' to permissions.allow")

    if changes:
        settings_path.write_text(json.dumps(settings, indent=2) + "\n")

    return changes
