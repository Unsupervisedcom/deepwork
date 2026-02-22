# REQ-002: Configuration Discovery

## Overview

DeepWork Reviews configuration files (`.deepreview`) can be placed anywhere within a project directory tree, similar to `.gitignore` files. The discovery system walks the project directory to find all `.deepreview` files, parses each one, and produces a flat list of review rules with their source directories preserved. Each file's glob patterns apply relative to the directory containing that file.

## Requirements

### REQ-002.1: File Discovery

1. The system MUST provide a `find_deepreview_files(project_root)` function that returns a list of `.deepreview` file paths.
2. The function MUST search `project_root` and all its subdirectories recursively.
3. The function MUST only return files named exactly `.deepreview` (no other extensions or prefixes).
4. The function MUST NOT traverse directories that are typically excluded from version control (e.g., `.git/`, `node_modules/`, `__pycache__/`).
5. The function MUST return paths sorted by depth (deepest files first), then alphabetically within the same depth.
6. If no `.deepreview` files are found, the function MUST return an empty list.

### REQ-002.2: Scope Boundaries

1. The discovery MUST be bounded to the `project_root` directory and its descendants.
2. The discovery MUST NOT traverse above `project_root`.
3. The `project_root` SHOULD be the git repository root, but the system MUST NOT require it to be a git repository for discovery purposes.

### REQ-002.3: Rule Loading

1. The system MUST provide a `load_all_rules(project_root)` function that discovers all `.deepreview` files and parses each into `ReviewRule` objects.
2. Each `.deepreview` file MUST be parsed and validated according to REQ-001.
3. The `source_dir` of each `ReviewRule` MUST be set to the parent directory of the `.deepreview` file it was parsed from.
4. If a `.deepreview` file fails to parse (invalid YAML, schema validation failure, or missing instructions file), the error MUST be reported but MUST NOT prevent other `.deepreview` files from being processed.
5. `load_all_rules()` MUST return both the successfully parsed rules and a list of errors (file path + error message).
6. Rules from different `.deepreview` files MUST be independent — a rule from `src/.deepreview` does not interact with or override a rule from the root `.deepreview`.

### REQ-002.4: Symlinks and Special Files

1. The discovery MUST follow the default behavior of the underlying directory traversal (do not follow symlinks by default).
2. The system MUST skip unreadable directories or files and continue discovery.
