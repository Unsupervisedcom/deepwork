"""Install/sync deprecation commands for DeepWork CLI.

# DEPRECATION NOTICE: Remove after June 1st, 2026.
# These commands exist only for backwards compatibility with users who
# have DeepWork installed globally via brew or uv. By June 1st, 2026,
# all users should have migrated to the Claude plugin distribution model
# and these commands can be safely deleted.
"""

import json
from pathlib import Path

import click

_DEPRECATION_MESSAGE = """
╔══════════════════════════════════════════════════════════════════════╗
║                     DEEPWORK DISTRIBUTION CHANGE                   ║
╚══════════════════════════════════════════════════════════════════════╝

DeepWork is no longer installed as a standalone CLI tool — it is now
distributed as a Claude Code plugin.

I have auto-installed the DeepWork plugin in this project for you,
but you must now uninstall the global CLI install you have previously done.

To uninstall, try BOTH of the following to make sure it is fully removed:

  brew uninstall deepwork
  uv tool uninstall deepwork

(It's safe to run both — one will succeed and the other will simply
report that it's not installed.)

Once uninstalled, DeepWork will continue to work automatically as a
Claude Code plugin whenever you use Claude in a project with DeepWork
configured.
"""


def _install_plugin_config() -> None:
    """Write marketplace and plugin configuration to .claude/settings.json.

    Merges the DeepWork plugin marketplace and plugin entries into the
    project's existing Claude settings without overwriting other config.
    """
    settings_path = Path(".claude") / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing settings or start fresh
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            settings = {}
    else:
        settings = {}

    # Merge extraKnownMarketplaces
    marketplaces = settings.setdefault("extraKnownMarketplaces", {})
    marketplaces["deepwork-plugins"] = {
        "source": {
            "source": "github",
            "repo": "Unsupervisedcom/deepwork",
        }
    }

    # Merge enabledPlugins
    plugins = settings.setdefault("enabledPlugins", {})
    plugins["deepwork@deepwork-plugins"] = True
    plugins["learning-agents@deepwork-plugins"] = True

    settings_path.write_text(json.dumps(settings, indent=2) + "\n")


def _run_install_deprecation() -> None:
    """Shared implementation for both install and sync commands.

    # DEPRECATION NOTICE: Remove after June 1st, 2026.
    """
    _install_plugin_config()
    click.echo(_DEPRECATION_MESSAGE)


# DEPRECATION NOTICE: Remove after June 1st, 2026.
@click.command(hidden=True)
def install() -> None:
    """(Deprecated) Install DeepWork — now distributed as a Claude plugin."""
    _run_install_deprecation()


# DEPRECATION NOTICE: Remove after June 1st, 2026.
@click.command(hidden=True)
def sync() -> None:
    """(Deprecated) Sync DeepWork — now distributed as a Claude plugin."""
    _run_install_deprecation()
