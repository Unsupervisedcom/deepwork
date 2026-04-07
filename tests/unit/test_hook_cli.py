"""Tests for hook CLI command.

Validates requirements: DW-REQ-005, DW-REQ-005.3.
"""

import types
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from deepwork.cli.hook import hook


class TestHookCLI:
    """Tests for the `deepwork hook` CLI command."""

    def test_hook_with_simple_name_imports_from_hooks_package(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.3.4).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Test that a simple hook name resolves to deepwork.hooks.<name>."""
        mock_module = types.ModuleType("deepwork.hooks.my_hook")
        mock_module.main = MagicMock(return_value=0)  # type: ignore[attr-defined]

        runner = CliRunner()
        with patch("importlib.import_module", return_value=mock_module) as mock_import:
            runner.invoke(hook, ["my_hook"])

        mock_import.assert_called_once_with("deepwork.hooks.my_hook")
        mock_module.main.assert_called_once()

    def test_hook_with_dotted_name_uses_full_module_path(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.3.3).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Test that a dotted hook name is treated as a full module path."""
        mock_module = types.ModuleType("custom.hooks.check")
        mock_module.main = MagicMock(return_value=0)  # type: ignore[attr-defined]

        runner = CliRunner()
        with patch("importlib.import_module", return_value=mock_module) as mock_import:
            runner.invoke(hook, ["custom.hooks.check"])

        mock_import.assert_called_once_with("custom.hooks.check")

    def test_hook_module_not_found_prints_error(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.3.6, DW-REQ-005.3.10).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Test that a missing hook module prints a friendly error."""
        runner = CliRunner()
        with patch("importlib.import_module", side_effect=ModuleNotFoundError("No module")):
            result = runner.invoke(hook, ["nonexistent_hook"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "not found" in (
            result.output + getattr(result, "stderr", "")
        )

    def test_hook_module_without_main_prints_error(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.3.9, DW-REQ-005.3.10).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Test that a hook module without main() prints an error."""
        mock_module = types.ModuleType("deepwork.hooks.no_main")
        # No main attribute

        runner = CliRunner()
        with patch("importlib.import_module", return_value=mock_module):
            result = runner.invoke(hook, ["no_main"])

        assert result.exit_code != 0

    def test_hook_main_return_value_becomes_exit_code(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.3.8).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Test that the return value of main() is passed to sys.exit."""
        mock_module = types.ModuleType("deepwork.hooks.exiter")
        mock_module.main = MagicMock(return_value=42)  # type: ignore[attr-defined]

        runner = CliRunner()
        with patch("importlib.import_module", return_value=mock_module):
            result = runner.invoke(hook, ["exiter"])

        # sys.exit(42) should result in non-zero exit code
        assert result.exit_code == 42

    def test_hook_main_returning_zero_succeeds(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.3.8).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Test that main() returning 0 results in exit code 0."""
        mock_module = types.ModuleType("deepwork.hooks.good_hook")
        mock_module.main = MagicMock(return_value=0)  # type: ignore[attr-defined]

        runner = CliRunner()
        with patch("importlib.import_module", return_value=mock_module):
            result = runner.invoke(hook, ["good_hook"])

        assert result.exit_code == 0

    def test_hook_unexpected_exception_prints_error(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.3.11).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Test that an unexpected exception in the hook is caught and reported."""
        mock_module = types.ModuleType("deepwork.hooks.crasher")
        mock_module.main = MagicMock(side_effect=RuntimeError("boom"))  # type: ignore[attr-defined]

        runner = CliRunner()
        with patch("importlib.import_module", return_value=mock_module):
            result = runner.invoke(hook, ["crasher"])

        assert result.exit_code != 0

    def test_hook_requires_hook_name_argument(self) -> None:
        # THIS TEST VALIDATES A HARD REQUIREMENT (DW-REQ-005.3.2).
        # YOU MUST NOT MODIFY THIS TEST UNLESS THE REQUIREMENT CHANGES
        """Test that invoking hook without an argument fails."""
        runner = CliRunner()
        result = runner.invoke(hook, [])

        assert result.exit_code != 0
        assert "Missing argument" in result.output
