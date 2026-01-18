#!/usr/bin/env python3
"""
Validate YAML files against their declared JSON Schema.

Looks for a $schema declaration at the top of YAML files and validates
the file content against that schema. The schema can be a URL or a local path.

Exit codes:
    0 - Validation passed (or no schema declared)
    1 - Validation failed (outputs JSON with failure details)
    2 - Error fetching/loading schema
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

try:
    import yaml
except ImportError:
    print(json.dumps({
        "status": "error",
        "message": "PyYAML is not installed. Run: pip install pyyaml"
    }))
    sys.exit(2)

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError
except ImportError:
    print(json.dumps({
        "status": "error",
        "message": "jsonschema is not installed. Run: pip install jsonschema"
    }))
    sys.exit(2)


def load_yaml_file(file_path: str) -> tuple[dict | list | None, str | None]:
    """Load a YAML file and return its contents."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
        return content, None
    except yaml.YAMLError as e:
        return None, f"Invalid YAML syntax: {e}"
    except FileNotFoundError:
        return None, f"File not found: {file_path}"
    except Exception as e:
        return None, f"Error reading file: {e}"


def extract_schema_reference(content: dict) -> str | None:
    """Extract the $schema reference from YAML content."""
    if not isinstance(content, dict):
        return None
    return content.get("$schema")


def fetch_schema_from_url(url: str) -> tuple[dict | None, str | None]:
    """Fetch a JSON Schema from a URL."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "yaml-schema-validator/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            schema_content = response.read().decode("utf-8")

        # Try to parse as JSON first, then YAML
        try:
            return json.loads(schema_content), None
        except json.JSONDecodeError:
            try:
                return yaml.safe_load(schema_content), None
            except yaml.YAMLError as e:
                return None, f"Invalid schema format at URL: {e}"

    except urllib.error.URLError as e:
        return None, f"Failed to fetch schema from URL: {e}"
    except Exception as e:
        return None, f"Error fetching schema: {e}"


def load_schema_from_path(schema_path: str, yaml_file_path: str) -> tuple[dict | None, str | None]:
    """Load a JSON Schema from a local file path."""
    # Resolve relative paths relative to the YAML file's directory
    path = Path(schema_path)
    if not path.is_absolute():
        yaml_dir = Path(yaml_file_path).parent
        path = yaml_dir / path

    path = path.resolve()

    if not path.exists():
        return None, f"Schema file not found: {path}"

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try to parse as JSON first, then YAML
        try:
            return json.loads(content), None
        except json.JSONDecodeError:
            try:
                return yaml.safe_load(content), None
            except yaml.YAMLError as e:
                return None, f"Invalid schema format: {e}"

    except Exception as e:
        return None, f"Error reading schema file: {e}"


def load_schema(schema_ref: str, yaml_file_path: str) -> tuple[dict | None, str | None]:
    """Load a schema from either a URL or local path."""
    if schema_ref.startswith(("http://", "https://")):
        return fetch_schema_from_url(schema_ref)
    else:
        return load_schema_from_path(schema_ref, yaml_file_path)


def validate_against_schema(content: dict, schema: dict) -> list[dict]:
    """Validate content against a JSON Schema and return list of errors."""
    validator = Draft7Validator(schema)
    errors = []

    for error in sorted(validator.iter_errors(content), key=lambda e: e.path):
        error_info = {
            "message": error.message,
            "path": "/" + "/".join(str(p) for p in error.absolute_path) if error.absolute_path else "/",
            "schema_path": "/" + "/".join(str(p) for p in error.absolute_schema_path) if error.absolute_schema_path else "/",
        }

        # Add the failing value if it's simple enough to display
        if error.instance is not None and not isinstance(error.instance, (dict, list)):
            error_info["value"] = error.instance

        errors.append(error_info)

    return errors


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Usage: validate_yaml_schema.py <file.yaml>"
        }))
        sys.exit(2)

    file_path = sys.argv[1]

    # Load the YAML file
    content, error = load_yaml_file(file_path)
    if error:
        print(json.dumps({
            "status": "error",
            "file": file_path,
            "message": error
        }))
        sys.exit(2)

    # Check for $schema reference
    schema_ref = extract_schema_reference(content)
    if not schema_ref:
        # No schema declared - pass silently
        print(json.dumps({
            "status": "pass",
            "file": file_path,
            "message": "No $schema declared, skipping validation"
        }))
        sys.exit(0)

    # Load the schema
    schema, error = load_schema(schema_ref, file_path)
    if error:
        print(json.dumps({
            "status": "error",
            "file": file_path,
            "schema": schema_ref,
            "message": error
        }))
        sys.exit(2)

    # Validate
    errors = validate_against_schema(content, schema)

    if not errors:
        print(json.dumps({
            "status": "pass",
            "file": file_path,
            "schema": schema_ref,
            "message": "Validation passed"
        }))
        sys.exit(0)
    else:
        print(json.dumps({
            "status": "fail",
            "file": file_path,
            "schema": schema_ref,
            "error_count": len(errors),
            "errors": errors
        }, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
