"""YAML utilities for reading and writing configuration files."""

from pathlib import Path
from typing import Any, Optional

import yaml


class YAMLError(Exception):
    """Exception raised for YAML-related errors."""

    pass


def load_yaml(path: Path | str) -> Optional[dict[str, Any]]:
    """
    Load YAML file and return parsed data.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML data as dictionary, or None if file doesn't exist

    Raises:
        YAMLError: If YAML parsing fails
    """
    path_obj = Path(path)

    if not path_obj.exists():
        return None

    try:
        with open(path_obj, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                return {}
            if not isinstance(data, dict):
                raise YAMLError(f"YAML file must contain a dictionary, got {type(data).__name__}")
            return data
    except yaml.YAMLError as e:
        raise YAMLError(f"Failed to parse YAML file {path_obj}: {e}") from e
    except OSError as e:
        raise YAMLError(f"Failed to read YAML file {path_obj}: {e}") from e


def save_yaml(path: Path | str, data: dict[str, Any]) -> None:
    """
    Save data to YAML file.

    Args:
        path: Path to YAML file
        data: Dictionary to save as YAML

    Raises:
        YAMLError: If YAML serialization or file write fails
    """
    path_obj = Path(path)

    # Ensure parent directory exists
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path_obj, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    except yaml.YAMLError as e:
        raise YAMLError(f"Failed to serialize data to YAML: {e}") from e
    except OSError as e:
        raise YAMLError(f"Failed to write YAML file {path_obj}: {e}") from e


def validate_yaml_structure(data: dict[str, Any], required_keys: list[str]) -> None:
    """
    Validate that YAML data contains required keys.

    Args:
        data: Parsed YAML data
        required_keys: List of required keys

    Raises:
        YAMLError: If required keys are missing
    """
    if not isinstance(data, dict):
        raise YAMLError(f"Data must be a dictionary, got {type(data).__name__}")

    missing_keys = [key for key in required_keys if key not in data]

    if missing_keys:
        raise YAMLError(f"Missing required keys: {', '.join(missing_keys)}")
