"""Unit tests for XDG utilities."""

import os
from pathlib import Path

import pytest

from deepwork.utils.xdg import (
    ensure_global_jobs_dir,
    get_global_jobs_dir,
    get_xdg_config_home,
)


class TestXDGUtilities:
    """Test XDG Base Directory utilities."""

    def test_get_xdg_config_home_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_xdg_config_home returns $XDG_CONFIG_HOME when set."""
        test_path = "/custom/config"
        monkeypatch.setenv("XDG_CONFIG_HOME", test_path)

        result = get_xdg_config_home()

        assert result == Path(test_path)

    def test_get_xdg_config_home_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_xdg_config_home returns ~/.config by default."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

        result = get_xdg_config_home()

        assert result == Path.home() / ".config"

    def test_get_global_jobs_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_global_jobs_dir returns correct path."""
        test_config = "/test/config"
        monkeypatch.setenv("XDG_CONFIG_HOME", test_config)

        result = get_global_jobs_dir()

        assert result == Path(test_config) / "deepwork" / "jobs"

    def test_ensure_global_jobs_dir_creates_directory(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test ensure_global_jobs_dir creates the directory if it doesn't exist."""
        test_config = tmp_path / "config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(test_config))

        result = ensure_global_jobs_dir()

        assert result.exists()
        assert result.is_dir()
        assert result == test_config / "deepwork" / "jobs"

    def test_ensure_global_jobs_dir_idempotent(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test ensure_global_jobs_dir is idempotent."""
        test_config = tmp_path / "config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(test_config))

        # Call twice
        result1 = ensure_global_jobs_dir()
        result2 = ensure_global_jobs_dir()

        assert result1 == result2
        assert result1.exists()
