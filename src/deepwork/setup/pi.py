"""Pi CLI settings configuration for DeepWork."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKAGE_SOURCE = "git:github.com/Unsupervisedcom/deepwork"


def pi_setup() -> list[str]:
    """Ensure the DeepWork Pi package is listed in global Pi settings."""
    settings_path = Path.home() / ".pi" / "agent" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    settings: dict[str, Any] = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            backup = settings_path.with_suffix(".json.bak")
            backup.write_text(settings_path.read_text(encoding="utf-8"), encoding="utf-8")
            settings = {}

    changes: list[str] = []
    packages = settings.setdefault("packages", [])
    if not isinstance(packages, list):
        packages = []
        settings["packages"] = packages
        changes.append("Reset invalid Pi packages setting to a list")

    if not _has_package(packages, PACKAGE_SOURCE):
        packages.append(PACKAGE_SOURCE)
        changes.append(f"Added Pi package '{PACKAGE_SOURCE}'")

    if changes:
        settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    return changes


def _has_package(packages: list[Any], source: str) -> bool:
    for package in packages:
        if package == source:
            return True
        if isinstance(package, dict) and package.get("source") == source:
            return True
    return False
