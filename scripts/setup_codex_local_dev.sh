#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$repo_root" <<'PY'
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def find_plugin_target(repo_root: Path) -> Path | None:
    override = os.environ.get("DEEPWORK_CODEX_PLUGIN_DIR")
    if override:
        candidate = Path(override).expanduser()
        return candidate.resolve() if candidate.is_dir() else None

    candidates = [
        repo_root / "plugins" / "codex",
        repo_root / "plugins" / "deepwork",
    ]

    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return None


def update_plugin_link(plugin_link: Path, plugin_target: Path) -> tuple[bool, Path | None]:
    backup_path: Path | None = None
    changed = False

    if plugin_link.is_symlink():
        if plugin_link.resolve() != plugin_target:
            backup_path = plugin_link.with_name(
                f"{plugin_link.name}.backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            plugin_link.rename(backup_path)
            changed = True
    elif plugin_link.exists():
        backup_path = plugin_link.with_name(
            f"{plugin_link.name}.backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        plugin_link.rename(backup_path)
        changed = True

    if not plugin_link.exists():
        plugin_link.symlink_to(plugin_target, target_is_directory=True)
        changed = True

    return changed, backup_path


def update_marketplace(marketplace_path: Path) -> bool:
    if marketplace_path.exists():
        try:
            data = json.loads(marketplace_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Failed to parse {marketplace_path}: {exc}") from exc
    else:
        data = {}

    if not isinstance(data, dict):
        raise SystemExit(f"{marketplace_path} must contain a JSON object.")

    plugins = data.setdefault("plugins", [])
    if not isinstance(plugins, list):
        raise SystemExit(f"{marketplace_path} field 'plugins' must be a JSON array.")

    if data.get("name") in (None, "", "[TODO: marketplace-name]"):
        data["name"] = "deepwork-local"

    interface = data.setdefault("interface", {})
    if not isinstance(interface, dict):
        raise SystemExit(f"{marketplace_path} field 'interface' must be a JSON object.")

    if interface.get("displayName") in (None, "", "[TODO: Marketplace Display Name]"):
        interface["displayName"] = "DeepWork Local"

    entry = {
        "name": "deepwork",
        "source": {
            "source": "local",
            "path": "./plugins/deepwork",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }

    changed = False
    for index, existing in enumerate(plugins):
        if isinstance(existing, dict) and existing.get("name") == "deepwork":
            if existing != entry:
                plugins[index] = entry
                changed = True
            break
    else:
        plugins.append(entry)
        changed = True

    updated_text = json.dumps(data, indent=2) + "\n"
    existing_text = marketplace_path.read_text(encoding="utf-8") if marketplace_path.exists() else ""
    if updated_text != existing_text:
        marketplace_path.write_text(updated_text, encoding="utf-8")
        changed = True

    return changed


def upsert_project_trust(config_text: str, repo_root: Path) -> tuple[str, bool]:
    path_str = str(repo_root)
    section_re = re.compile(
        rf'(?ms)^\[projects\."{re.escape(path_str)}"\]\n.*?(?=^\[|\Z)'
    )
    match = section_re.search(config_text)

    if match:
        section = match.group(0)
        if re.search(r'(?m)^trust_level\s*=\s*"trusted"\s*$', section):
            return config_text, False

        if re.search(r'(?m)^trust_level\s*=', section):
            new_section = re.sub(
                r'(?m)^trust_level\s*=.*$',
                'trust_level = "trusted"',
                section,
            )
        else:
            suffix = "" if section.endswith("\n") else "\n"
            new_section = f'{section}{suffix}trust_level = "trusted"\n'
        return config_text[: match.start()] + new_section + config_text[match.end() :], True

    prefix = "" if not config_text or config_text.endswith("\n") else "\n"
    new_section = f'\n[projects."{path_str}"]\ntrust_level = "trusted"\n'
    return config_text + prefix + new_section, True


def upsert_deepwork_mcp_server(config_text: str, repo_root: Path) -> tuple[str, bool]:
    path_str = str(repo_root)
    args = json.dumps(
        ["develop", "-c", "uv", "run", "deepwork", "serve", "--path", path_str, "--platform", "codex"]
    )
    new_section = (
        "[mcp_servers.deepwork_current_repo]\n"
        'command = "nix"\n'
        f"args = {args}\n"
        f'cwd = "{path_str}"\n'
    )

    section_re = re.compile(r"(?ms)^\[mcp_servers\.deepwork_current_repo\]\n.*?(?=^\[|\Z)")
    match = section_re.search(config_text)
    if match:
        existing = match.group(0)
        if existing == new_section:
            return config_text, False
        return config_text[: match.start()] + new_section + config_text[match.end() :], True

    prefix = "" if not config_text or config_text.endswith("\n") else "\n"
    return config_text + prefix + "\n" + new_section, True


def update_codex_config(config_path: Path, repo_root: Path) -> tuple[bool, list[str]]:
    config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    notes: list[str] = []

    updated_text, trust_changed = upsert_project_trust(config_text, repo_root)
    updated_text, mcp_changed = upsert_deepwork_mcp_server(updated_text, repo_root)

    if updated_text != config_text:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(updated_text, encoding="utf-8")

    if trust_changed:
        notes.append(f"trusted project: {repo_root}")
    if mcp_changed:
        notes.append(f"updated deepwork_current_repo MCP server: {repo_root}")

    return updated_text != config_text, notes


repo_root = Path(sys.argv[1]).resolve()
home = Path(os.environ.get("HOME", str(Path.home()))).expanduser().resolve()

plugin_target = find_plugin_target(repo_root)
plugin_parent = home / "plugins"
plugin_link = plugin_parent / "deepwork"
marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
config_path = home / ".codex" / "config.toml"

plugin_parent.mkdir(parents=True, exist_ok=True)
marketplace_path.parent.mkdir(parents=True, exist_ok=True)

changed_items: list[str] = []
info_items: list[str] = []

if plugin_target is not None:
    plugin_changed, backup_path = update_plugin_link(plugin_link, plugin_target)
    if plugin_changed:
        changed_items.append(f"plugin link: {plugin_link} -> {plugin_target}")
    else:
        info_items.append(f"plugin link already correct: {plugin_link} -> {plugin_target}")
    if backup_path is not None:
        changed_items.append(f"backup created: {backup_path}")

    marketplace_changed = update_marketplace(marketplace_path)
    if marketplace_changed:
        changed_items.append(f"marketplace updated: {marketplace_path}")
    else:
        info_items.append(f"marketplace already correct: {marketplace_path}")
else:
    info_items.append(
        "no repo-local Codex plugin bundle found under plugins/codex or plugins/deepwork; "
        "skipped plugin symlink and marketplace updates"
    )

config_changed, config_notes = update_codex_config(config_path, repo_root)
if config_changed:
    changed_items.extend(config_notes)
else:
    info_items.append(f"Codex config already points to this checkout: {config_path}")

if changed_items:
    print("DeepWork Codex local dev configured: changed")
    for item in changed_items:
        print(f"- {item}")
    for item in info_items:
        print(f"- {item}")
    print("Restart Codex to pick up the changes.")
else:
    print("DeepWork Codex local dev configured: no-op")
    for item in info_items:
        print(f"- {item}")
PY
