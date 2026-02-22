# REQ-010: Filesystem and YAML Utilities

## Overview

DeepWork provides utility modules for safe filesystem operations, YAML loading/saving, and JSON Schema validation. These utilities underpin the core framework by providing consistent, safe file I/O with proper encoding, permission handling, and error reporting.

## Requirements

### REQ-010.1: File Permission Management

1. `fix_permissions()` MUST ensure user read and write permissions on files (minimum `S_IRUSR | S_IWUSR`).
2. `fix_permissions()` MUST preserve the executable bit on files if already set.
3. `fix_permissions()` MUST ensure user read, write, and execute permissions on directories (minimum `S_IRWXU`).
4. `fix_permissions()` MUST recursively fix permissions for all contents of a directory.

### REQ-010.2: Directory Management

1. `ensure_dir()` MUST create the directory and all parent directories if they do not exist.
2. `ensure_dir()` MUST NOT raise an error if the directory already exists.
3. `ensure_dir()` MUST return the Path object for the created or existing directory.

### REQ-010.3: Safe File Writing

1. `safe_write()` MUST create parent directories if they do not exist before writing.
2. `safe_write()` MUST write content using UTF-8 encoding.
3. `safe_write()` MUST overwrite existing files.

### REQ-010.4: Safe File Reading

1. `safe_read()` MUST return the file content as a string using UTF-8 encoding.
2. `safe_read()` MUST return `None` if the file does not exist.
3. `safe_read()` MUST raise `OSError` if the read fails for reasons other than the file not existing.

### REQ-010.5: Directory Copying

1. `copy_dir()` MUST recursively copy the source directory to the destination.
2. `copy_dir()` MUST use `dirs_exist_ok=True` to allow copying into an existing destination.
3. `copy_dir()` MUST fix permissions on the destination after copying (via `fix_permissions()`).
4. `copy_dir()` MUST raise `FileNotFoundError` if the source directory does not exist.
5. `copy_dir()` MUST raise `NotADirectoryError` if the source path is not a directory.
6. `copy_dir()` MUST support an optional `ignore_patterns` parameter (list of glob patterns) to exclude files/directories from copying.

### REQ-010.6: File Finding

1. `find_files()` MUST return all files matching a glob pattern in the given directory, sorted by path.
2. `find_files()` MUST return only files, not directories.
3. `find_files()` MUST raise `FileNotFoundError` if the directory does not exist.
4. `find_files()` MUST raise `NotADirectoryError` if the path is not a directory.

### REQ-010.7: YAML Loading

1. `load_yaml()` MUST parse a YAML file and return a dictionary.
2. `load_yaml()` MUST return `None` if the file does not exist.
3. `load_yaml()` MUST return an empty dict for an empty file.
4. `load_yaml()` MUST raise `YAMLError` if the parsed content is not a dictionary.
5. `load_yaml_from_string()` MUST parse a YAML string and return a dictionary.
6. `load_yaml_from_string()` MUST return `None` for empty content.

### REQ-010.8: YAML Saving

1. `save_yaml()` MUST serialize a dictionary to YAML and write to the specified file.
2. `save_yaml()` MUST create parent directories if they do not exist.
3. `save_yaml()` MUST use `default_flow_style=False` for readable block-style output.
4. `save_yaml()` MUST use `sort_keys=False` to preserve insertion order.

### REQ-010.9: YAML Structure Validation

1. `validate_yaml_structure()` MUST check that all specified required keys are present in the data dictionary.
2. Missing required keys MUST be reported in the validation result.

### REQ-010.10: JSON Schema Validation

1. `validate_against_schema()` MUST validate a data dictionary against a JSON Schema.
2. When validation fails, the system MUST raise `ValidationError` with the schema path and validation message extracted from the `jsonschema` library error.
3. The validation MUST use `jsonschema.validate()` under the hood.
