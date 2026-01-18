#!/usr/bin/env python3
"""
Validate YAML and JSON files against their declared JSON Schema.

This script first performs a quick text search for $schema in the file.
Only if a schema reference is found does it fully parse the file and validate.

Supported file types: .yml, .yaml, .json

Exit codes:
    0 - Validation passed (or no schema declared)
    1 - Validation failed (outputs JSON with failure details)
    2 - Error fetching/loading schema
"""

import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    import jsonschema
    from jsonschema import Draft7Validator
except ImportError:
    print(json.dumps({
        "status": "error",
        "message": "jsonschema is not installed. Run: pip install jsonschema"
    }))
    sys.exit(2)


# Pattern to quickly detect $schema in file content without full parsing
# Matches both JSON ("$schema": "...") and YAML ($schema: ...)
SCHEMA_PATTERN = re.compile(
    r'''["']?\$schema["']?\s*[:=]\s*["']?([^"'\s,}\]]+)''',
    re.IGNORECASE
)


def quick_detect_schema(file_path: str) -> str | None:
    """
    Quickly scan file for $schema declaration without full parsing.
    Returns the schema reference if found, None otherwise.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Read first 4KB - schema should be near the top
            content = f.read(4096)

        match = SCHEMA_PATTERN.search(content)
        if match:
            return match.group(1).rstrip("'\"")
        return None

    except Exception:
        return None


def parse_file(file_path: str) -> tuple[dict | list | None, str | None]:
    """Parse a YAML or JSON file and return its contents."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if suffix == ".json":
            return json.loads(content), None
        elif suffix in (".yml", ".yaml"):
            if yaml is None:
                return None, "PyYAML is not installed. Run: pip install pyyaml"
            return yaml.safe_load(content), None
        else:
            # Try JSON first, then YAML
            try:
                return json.loads(content), None
            except json.JSONDecodeError:
                if yaml:
                    return yaml.safe_load(content), None
                return None, f"Unsupported file type: {suffix}"

    except json.JSONDecodeError as e:
        return None, f"Invalid JSON syntax: {e}"
    except yaml.YAMLError as e:
        return None, f"Invalid YAML syntax: {e}"
    except FileNotFoundError:
        return None, f"File not found: {file_path}"
    except Exception as e:
        return None, f"Error reading file: {e}"


def extract_schema_reference(content: dict) -> str | None:
    """Extract the $schema reference from parsed content."""
    if not isinstance(content, dict):
        return None
    return content.get("$schema")


def fetch_schema_from_url(url: str) -> tuple[dict | None, str | None]:
    """Fetch a JSON Schema from a URL."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "schema-validator/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            schema_content = response.read().decode("utf-8")

        # Try to parse as JSON first, then YAML
        try:
            return json.loads(schema_content), None
        except json.JSONDecodeError:
            if yaml:
                try:
                    return yaml.safe_load(schema_content), None
                except yaml.YAMLError as e:
                    return None, f"Invalid schema format at URL: {e}"
            return None, "Invalid JSON schema format at URL"

    except urllib.error.URLError as e:
        return None, f"Failed to fetch schema from URL: {e}"
    except Exception as e:
        return None, f"Error fetching schema: {e}"


def load_schema_from_path(schema_path: str, source_file_path: str) -> tuple[dict | None, str | None]:
    """Load a JSON Schema from a local file path."""
    # Resolve relative paths relative to the source file's directory
    path = Path(schema_path)
    if not path.is_absolute():
        source_dir = Path(source_file_path).parent
        path = source_dir / path

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
            if yaml:
                try:
                    return yaml.safe_load(content), None
                except yaml.YAMLError as e:
                    return None, f"Invalid schema format: {e}"
            return None, "Invalid JSON schema format"

    except Exception as e:
        return None, f"Error reading schema file: {e}"


def load_schema(schema_ref: str, source_file_path: str) -> tuple[dict | None, str | None]:
    """Load a schema from either a URL or local path."""
    if schema_ref.startswith(("http://", "https://")):
        return fetch_schema_from_url(schema_ref)
    else:
        return load_schema_from_path(schema_ref, source_file_path)


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
            "message": "Usage: validate_schema.py <file.yaml|file.json>"
        }))
        sys.exit(2)

    file_path = sys.argv[1]

    # Step 1: Quick detection - scan for $schema without parsing
    quick_schema = quick_detect_schema(file_path)
    if not quick_schema:
        # No schema found in quick scan - pass without full parsing
        print(json.dumps({
            "status": "pass",
            "file": file_path,
            "message": "No $schema declared, skipping validation"
        }))
        sys.exit(0)

    # Step 2: Schema detected - now do full parsing
    content, error = parse_file(file_path)
    if error:
        print(json.dumps({
            "status": "error",
            "file": file_path,
            "message": error
        }))
        sys.exit(2)

    # Get the actual schema reference from parsed content
    schema_ref = extract_schema_reference(content)
    if not schema_ref:
        # Quick scan found something but it wasn't actually a $schema field
        print(json.dumps({
            "status": "pass",
            "file": file_path,
            "message": "No $schema declared, skipping validation"
        }))
        sys.exit(0)

    # Step 3: Load the schema
    schema, error = load_schema(schema_ref, file_path)
    if error:
        print(json.dumps({
            "status": "error",
            "file": file_path,
            "schema": schema_ref,
            "message": error
        }))
        sys.exit(2)

    # Step 4: Validate
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
