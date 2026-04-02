"""Tests for the local Codex dev setup helper."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "setup_codex_local_dev.sh"


def _run_script(home: Path, plugin_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    if plugin_dir is not None:
        env["DEEPWORK_CODEX_PLUGIN_DIR"] = str(plugin_dir)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


class TestSetupCodexLocalDevScript:
    """Tests for scripts/setup_codex_local_dev.sh."""

    def test_updates_plugin_marketplace_and_codex_config(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()

        result = _run_script(tmp_path, plugin_dir)

        assert "changed" in result.stdout
        assert "Restart Codex" in result.stdout

        plugin_link = tmp_path / "plugins" / "deepwork"
        assert plugin_link.is_symlink()
        assert plugin_link.resolve() == plugin_dir.resolve()

        marketplace_path = tmp_path / ".agents" / "plugins" / "marketplace.json"
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        plugin = next(entry for entry in marketplace["plugins"] if entry["name"] == "deepwork")
        assert plugin["source"]["path"] == "./plugins/deepwork"

        config_path = tmp_path / ".codex" / "config.toml"
        config_text = config_path.read_text(encoding="utf-8")
        assert str(PROJECT_ROOT) in config_text
        assert '[mcp_servers.deepwork_current_repo]' in config_text
        assert 'trust_level = "trusted"' in config_text

    def test_second_run_is_no_op(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir()

        _run_script(tmp_path, plugin_dir)
        result = _run_script(tmp_path, plugin_dir)

        assert "no-op" in result.stdout
        assert "Restart Codex" not in result.stdout

    def test_updates_codex_config_even_without_plugin_bundle(self, tmp_path: Path) -> None:
        result = _run_script(tmp_path, tmp_path / "missing-plugin")

        assert "changed" in result.stdout
        assert "skipped plugin symlink and marketplace updates" in result.stdout

        config_path = tmp_path / ".codex" / "config.toml"
        config_text = config_path.read_text(encoding="utf-8")
        assert str(PROJECT_ROOT) in config_text
