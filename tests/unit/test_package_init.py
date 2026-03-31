"""Tests for deepwork package __init__.py lazy imports and jobs.mcp.__init__.py."""

from unittest.mock import MagicMock, patch

import pytest


class TestDeepworkInit:
    """Tests for the deepwork package lazy attribute access."""

    def test_version_is_accessible(self) -> None:
        """Test that __version__ is directly accessible."""
        import deepwork

        assert isinstance(deepwork.__version__, str)
        assert len(deepwork.__version__) > 0

    def test_author_is_accessible(self) -> None:
        """Test that __author__ is directly accessible."""
        import deepwork

        assert isinstance(deepwork.__author__, str)

    def test_lazy_import_job_definition(self) -> None:
        """Test that JobDefinition is lazily importable via __getattr__."""
        import deepwork

        # This triggers __getattr__ -> imports from deepwork.jobs.parser
        cls = deepwork.JobDefinition
        from deepwork.jobs.parser import JobDefinition

        assert cls is JobDefinition

    def test_lazy_import_parse_error(self) -> None:
        """Test that ParseError is lazily importable via __getattr__."""
        import deepwork

        cls = deepwork.ParseError
        from deepwork.jobs.parser import ParseError

        assert cls is ParseError

    def test_lazy_import_parse_job_definition(self) -> None:
        """Test that parse_job_definition is lazily importable via __getattr__."""
        import deepwork

        func = deepwork.parse_job_definition
        from deepwork.jobs.parser import parse_job_definition

        assert func is parse_job_definition

    def test_unknown_attribute_raises_attribute_error(self) -> None:
        """Test that accessing an unknown attribute raises AttributeError."""
        import deepwork

        with pytest.raises(AttributeError, match="has no attribute"):
            _ = deepwork.this_does_not_exist


class TestMCPInit:
    """Tests for deepwork.jobs.mcp.__init__.py lazy import."""

    @patch("deepwork.jobs.mcp.server.create_server")
    def test_create_server_delegates_to_server_module(self, mock_cs: MagicMock) -> None:
        """Test that create_server in __init__ delegates to server.create_server."""
        mock_cs.return_value = "mock_server"

        from deepwork.jobs.mcp import create_server

        result = create_server(project_root="/tmp", platform="claude")

        mock_cs.assert_called_once_with(project_root="/tmp", platform="claude")
        assert result == "mock_server"

    @patch("deepwork.jobs.mcp.server.create_server")
    def test_create_server_passes_args_and_kwargs(self, mock_cs: MagicMock) -> None:
        """Test that positional and keyword args are forwarded correctly."""
        mock_cs.return_value = "server"

        from deepwork.jobs.mcp import create_server

        create_server("arg1", key="val")

        mock_cs.assert_called_once_with("arg1", key="val")
