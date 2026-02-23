# REVIEW-REQ-008: Get Configured Reviews MCP Tool

## Overview

The `get_configured_reviews` MCP tool allows agents to query which review rules are configured in a project without running the full review pipeline. It returns rule metadata (name, description, defining file) and optionally filters to rules matching a given file list.

## Requirements

### REVIEW-REQ-008.1: Tool Registration

1. The tool MUST be registered as `get_configured_reviews` on the MCP server.
2. The tool MUST accept an optional `only_rules_matching_files` parameter (list of file paths).
3. The tool MUST return a list of rule summaries (see REVIEW-REQ-008.2).

### REVIEW-REQ-008.2: Rule Summary

1. Each entry in the returned list MUST include `name` (str) — the rule name from the `.deepreview` file.
2. Each entry MUST include `description` (str) — the rule's description field.
3. Each entry MUST include `defining_file` (str) — a relative path to the `.deepreview` file with line number (e.g., `.deepreview:1`).

### REVIEW-REQ-008.3: File Filtering

1. When `only_rules_matching_files` is provided, the tool MUST return only rules whose include/exclude patterns match at least one of the provided files.
2. When `only_rules_matching_files` is omitted (None), the tool MUST return all configured rules.

### REVIEW-REQ-008.4: Error Handling

1. The tool MUST handle discovery errors gracefully — if some `.deepreview` files are invalid, valid rules from other files MUST still be returned.
2. Discovery errors MUST NOT cause the tool to raise an exception.
