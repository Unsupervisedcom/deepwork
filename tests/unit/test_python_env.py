"""Unit tests for Python environment management."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from deepwork.utils.python_env import PythonEnvironment


class TestPythonEnvironment:
    """Tests for PythonEnvironment class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        env = PythonEnvironment({})
        assert env.manager == "uv"
        assert env.version == "3.11"
        assert env.venv_path == Path(".venv")

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = {
            "manager": "system",
            "version": "3.12",
            "venv_path": "custom_venv"
        }
        env = PythonEnvironment(config)
        assert env.manager == "system"
        assert env.version == "3.12"
        assert env.venv_path == Path("custom_venv")

    def test_detect_existing_venv(self, tmp_path):
        """Test detection of existing .venv directory."""
        venv = tmp_path / ".venv" / "bin"
        venv.mkdir(parents=True)
        (venv / "python").touch()

        result = PythonEnvironment.detect_existing(tmp_path)
        assert result == tmp_path / ".venv"

    def test_detect_existing_venv_alternative_names(self, tmp_path):
        """Test detection of venv with alternative names."""
        venv = tmp_path / "venv" / "bin"
        venv.mkdir(parents=True)
        (venv / "python").touch()

        result = PythonEnvironment.detect_existing(tmp_path)
        assert result == tmp_path / "venv"

    def test_detect_no_existing_venv(self, tmp_path):
        """Test detection returns None when no venv exists."""
        result = PythonEnvironment.detect_existing(tmp_path)
        assert result is None

    def test_setup_with_skip(self, tmp_path):
        """Test skip mode returns True without creating venv."""
        env = PythonEnvironment({"manager": "skip"})
        assert env.setup(tmp_path) is True

    def test_setup_with_uv(self, tmp_path, mocker):
        """Test creating venv using uv."""
        mocker.patch("shutil.which", return_value="/usr/bin/uv")
        mock_run = mocker.patch("subprocess.run", return_value=Mock(returncode=0))

        env = PythonEnvironment({"manager": "uv", "version": "3.11"})
        result = env.setup(tmp_path)

        assert result is True
        # Should call uv init first (since pyproject.toml doesn't exist), then uv venv
        assert mock_run.call_count == 2
        
        # First call should be uv init
        first_call_args = mock_run.call_args_list[0][0][0]
        assert first_call_args[0] == "uv"
        assert first_call_args[1] == "init"
        assert "--no-workspace" in first_call_args
        
        # Second call should be uv venv
        second_call_args = mock_run.call_args_list[1][0][0]
        assert second_call_args[0] == "uv"
        assert second_call_args[1] == "venv"
        assert "--python" in second_call_args
        assert "3.11" in second_call_args

    def test_setup_with_uv_existing_pyproject(self, tmp_path, mocker):
        """Test creating venv using uv when pyproject.toml already exists."""
        # Create existing pyproject.toml
        (tmp_path / "pyproject.toml").write_text("[project]\nname = \"test\"\n")
        
        mocker.patch("shutil.which", return_value="/usr/bin/uv")
        mock_run = mocker.patch("subprocess.run", return_value=Mock(returncode=0))

        env = PythonEnvironment({"manager": "uv", "version": "3.11"})
        result = env.setup(tmp_path)

        assert result is True
        # Should only call uv venv (not uv init since pyproject.toml exists)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "uv"
        assert args[1] == "venv"
        assert "--python" in args
        assert "3.11" in args


    def test_setup_with_uv_not_found(self, tmp_path, mocker):
        """Test error when uv is not found."""
        mocker.patch("shutil.which", return_value=None)

        env = PythonEnvironment({"manager": "uv"})
        with pytest.raises(RuntimeError, match="uv not found"):
            env.setup(tmp_path)

    def test_setup_with_system_python(self, tmp_path, mocker):
        """Test creating venv using system Python."""
        mocker.patch("shutil.which", return_value="/usr/bin/python3")
        mock_run = mocker.patch("subprocess.run", return_value=Mock(returncode=0))

        env = PythonEnvironment({"manager": "system"})
        result = env.setup(tmp_path)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "/usr/bin/python3"
        assert args[1] == "-m"
        assert args[2] == "venv"

    def test_setup_with_system_python_not_found(self, tmp_path, mocker):
        """Test error when system Python is not found."""
        mocker.patch("shutil.which", return_value=None)

        env = PythonEnvironment({"manager": "system"})
        with pytest.raises(RuntimeError, match="Python not found"):
            env.setup(tmp_path)

    def test_setup_with_invalid_manager(self, tmp_path):
        """Test setup with invalid manager returns False."""
        env = PythonEnvironment({"manager": "invalid"})
        result = env.setup(tmp_path)
        assert result is False

    def test_install_package_with_uv(self, tmp_path, mocker):
        """Test installing package with uv."""
        mock_run = mocker.patch("subprocess.run", return_value=Mock(returncode=0))

        env = PythonEnvironment({"manager": "uv"})
        result = env.install_package("pytest", tmp_path)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["uv", "pip", "install", "pytest"]

    def test_install_package_with_system(self, tmp_path, mocker):
        """Test installing package with system Python."""
        venv_dir = tmp_path / ".venv" / "bin"
        venv_dir.mkdir(parents=True)

        mock_run = mocker.patch("subprocess.run", return_value=Mock(returncode=0))

        env = PythonEnvironment({"manager": "system"})
        result = env.install_package("pytest", tmp_path)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert str(tmp_path / ".venv" / "bin" / "pip") in args[0]
        assert args[1] == "install"
        assert args[2] == "pytest"

    def test_install_package_failure(self, tmp_path, mocker):
        """Test package installation failure."""
        mock_run = mocker.patch("subprocess.run", return_value=Mock(returncode=1))

        env = PythonEnvironment({"manager": "uv"})
        result = env.install_package("pytest", tmp_path)

        assert result is False
