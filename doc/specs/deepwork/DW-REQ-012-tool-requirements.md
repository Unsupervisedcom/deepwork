# DW-REQ-012: Tool Requirements Policy Enforcement

## Overview

The tool requirements system enforces RFC 2119-style policies on AI agent tool calls. Users define rules in `.deepwork/tool_requirements/*.yml` files. A PreToolUse hook checks these rules via an HTTP sidecar server using LLM-based semantic evaluation. Failed checks can be appealed via an MCP tool. Approved calls are cached with a TTL.

## DW-REQ-012.1: Policy File Format

1. Policy files MUST be YAML files located in `.deepwork/tool_requirements/` with a `.yml` extension.
2. Each policy file MUST be validated against the `tool_requirements_schema.json` JSON Schema.
3. The `tools` field MUST be a non-empty array of normalized tool names (e.g., `shell`, `write_file`, `edit_file`) or MCP tool names (e.g., `mcp__server__tool`).
4. The `requirements` field MUST be a mapping of requirement identifiers to objects containing a `rule` string (RFC 2119 statement) and an optional `no_exception` boolean (default: `false`).
5. The `match` field MAY be a mapping of tool_input parameter names to regex patterns for parameter-level filtering.
6. The `extends` field MAY be an array of policy file stems for inheritance.
7. The `summary` field MAY be a human-readable description of the policy.

## DW-REQ-012.2: Policy Discovery

1. The system MUST scan `.deepwork/tool_requirements/` for `*.yml` files (single-directory, no tree walk).
2. Files that fail to parse MUST be skipped with a warning logged — they MUST NOT prevent other policies from loading.
3. If the `.deepwork/tool_requirements/` directory does not exist, the system MUST return an empty policy list without error.

## DW-REQ-012.3: Policy Inheritance

1. When a policy lists `extends`, the system MUST merge parent requirements into the child.
2. Child requirements MUST override parent requirements with the same key.
3. Unknown parent names MUST be logged as warnings and skipped — they MUST NOT cause errors.
4. Circular inheritance MUST be detected and MUST NOT cause infinite loops.
5. Diamond inheritance (two parents sharing a common ancestor) MUST be handled correctly — the common ancestor's requirements MUST be included once.

## DW-REQ-012.4: Policy Matching

1. A policy MUST match a tool call if the tool's normalized name is in the policy's `tools` list.
2. If the policy has a `match` dict, the policy MUST match only when at least one parameter regex matches a value in `tool_input` (via `re.search`).
3. If the policy has no `match` dict, it MUST match all calls to the listed tools.
4. Multiple policies MAY match a single tool call; all matched requirements MUST be merged.
5. If the same requirement key appears in multiple matched policies, the first occurrence MUST win.
6. Invalid regex patterns in `match` MUST be skipped without error.

## DW-REQ-012.5: Requirement Evaluation

1. Requirements MUST be evaluated by an LLM evaluator (Haiku by default) that considers RFC 2119 keywords.
2. `MUST`/`MUST NOT` violations MUST always result in failure.
3. `SHOULD`/`SHOULD NOT` violations MUST result in failure only when the violation is clear and easily avoidable.
4. `MAY` requirements MUST always pass.
5. The evaluator MUST return a verdict for every requirement — requirements not evaluated MUST fail closed.
6. The evaluator MUST be encapsulated behind an abstract interface to allow implementation swapping.
7. Large `tool_input` values MUST be truncated to avoid exceeding LLM token limits.

## DW-REQ-012.6: Check Flow

1. When a tool call is checked, the system MUST first check the cache — if approved, it MUST allow immediately.
2. If no policies match the tool call, it MUST be allowed.
3. If evaluation passes all requirements, the result MUST be cached and the call MUST be allowed.
4. If any requirements fail, the response MUST include ALL failures (not one at a time).
5. Each failure MUST include the requirement ID and an explanation.
6. `no_exception` requirements MUST be labeled as such in the failure message.
7. The failure message MUST include instructions for how to appeal via the `appeal_tool_requirement` MCP tool.

## DW-REQ-012.7: Appeal Mechanism

1. The system MUST provide an `appeal_tool_requirement` MCP tool.
2. The tool MUST accept `tool_name`, `tool_input`, and `policy_justification` (a dict mapping failed check IDs to justification strings).
3. `no_exception` requirements MUST NOT be appealable — appeals for them MUST be rejected immediately.
4. For appealable requirements, the evaluator MUST re-evaluate considering the provided justifications.
5. If the appeal succeeds, the result MUST be cached so the retried tool call passes the hook.
6. If the appeal fails, the response MUST list all still-failing requirements.

## DW-REQ-012.8: Caching

1. Approved tool calls MUST be cached with a 1-hour TTL.
2. The cache key MUST be deterministic, derived from the tool name and tool input.
3. Expired cache entries MUST be evicted on lookup.
4. The cache MUST be in-memory within the sidecar server process.

## DW-REQ-012.9: PreToolUse Hook

1. The hook MUST fire on all PreToolUse events (empty matcher).
2. The hook MUST skip the `appeal_tool_requirement` MCP tool to prevent infinite loops (substring match on raw tool name).
3. If the sidecar is unreachable (port file missing or PID dead), the hook MUST deny with an error message instructing the user to restart the MCP server (fail-closed).
4. If communication with the sidecar fails, the hook MUST deny with an error message (fail-closed).
5. The hook MUST use `hookSpecificOutput.permissionDecision: "deny"` format for Claude Code PreToolUse events.
6. The hook MUST use the cross-platform wrapper system (`run_hook`, `HookInput`, `HookOutput`).

## DW-REQ-012.10: Sidecar HTTP Server

1. The sidecar MUST start as a daemon thread alongside the MCP server when policy files exist.
2. The sidecar MUST bind to `127.0.0.1` on a random port.
3. The sidecar MUST write a port file to `.deepwork/tmp/tool_req_sidecar/<PID>.json` containing `{"pid": <PID>, "port": <PORT>}`.
4. The sidecar MUST provide `POST /check` and `POST /appeal` endpoints.
5. The sidecar MUST clean up its port file and any session mapping files on exit.
6. Session IDs used in filenames MUST be validated against `^[a-zA-Z0-9_-]+$` to prevent path traversal.

## DW-REQ-012.11: Multi-Instance Support

1. When the first MCP tool call arrives with a `session_id`, the server MUST write a session mapping file at `.deepwork/tmp/tool_req_sidecar/session_<SESSION_ID>.json`.
2. The hook MUST look for a session-specific mapping file first, then fall back to scanning PID-keyed port files for live processes.
3. Stale port files (PID no longer alive) MUST be cleaned up during discovery.

## DW-REQ-012.12: Sidecar Startup Gating

1. The sidecar MUST NOT start if no `.deepwork/tool_requirements/` directory exists.
2. The sidecar MUST NOT start if the directory contains no `*.yml` files.
3. If sidecar startup fails, the MCP server MUST continue running — the failure MUST be logged as a warning.
