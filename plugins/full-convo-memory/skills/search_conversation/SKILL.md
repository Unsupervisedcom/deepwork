---
name: search_conversation
description: "Search the current Claude Code session's jsonl transcript with jq — use when you need to recall something said earlier in this exact session (user messages, tool calls, prior decisions)."
---

# search_conversation

Runs `jq` against the jsonl transcript of the **current** Claude Code session and prints the matching lines. Useful for exact-string lookups against earlier turns (e.g. "what path did the user mention?", "what command did that tool return?") without rereading the whole conversation or spawning a semantic-search agent.

## How to invoke

Run the script directly with `Bash`. Everything you pass is forwarded to `jq` verbatim, so any `jq` flag or filter works.

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/search_conversation.sh [--log-file <path>] <jq-args...>
```

At least one `jq` argument is required — running with zero args prints usage and exits non-zero (this is a guard against accidentally dumping the entire transcript).

## What the script does for you

1. **Auto-detects the log file.** Resolution order:
   - `--log-file <path>` (explicit override, must be the first argument).
   - Sub-agent transcript, if `CLAUDE_CODE_AGENT_ID` and `CLAUDE_CODE_SESSION_ID` are both set: `~/.claude/projects/<encoded-cwd>/$CLAUDE_CODE_SESSION_ID/subagents/agent-$CLAUDE_CODE_AGENT_ID.jsonl`. This means if a sub-agent (Explore, Plan, custom) invokes the script, it will search **its own** transcript, not the parent's.
   - Top-level session transcript, if `CLAUDE_CODE_SESSION_ID` is set: `~/.claude/projects/<encoded-cwd>/$CLAUDE_CODE_SESSION_ID.jsonl`.
   - Fallback: the most-recently-modified `*.jsonl` file directly in `~/.claude/projects/<encoded-cwd>/`.

   (`<encoded-cwd>` is `$PWD` with every `/` replaced by `-`, matching Claude Code's on-disk layout.)

2. **Drops compaction-summary messages.** The script pre-filters with `jq 'select(.isCompactSummary != true)'`, so the synthetic "This session is being continued from a previous conversation…" entries that appear mid-file after a compaction never reach your `jq` filter. Everything else is untouched.

3. **Passes your args straight to `jq`.** Flags (`-r`, `-c`, `--arg`, `--slurp`, …), filters, or both — all forwarded verbatim.

4. **Appends a pointer line.** The final line of stdout names the exact log file path, so if `jq` finds nothing useful you can hand the file to an Explore agent for a semantic pass.

## Transcript shape

Each line is one JSON object representing a turn or tool event. Commonly-useful top-level fields:

- `type` — `"user"`, `"assistant"`, `"system"`, or `"tool_use"`-like variants.
- `message.role` — `"user"` / `"assistant"`.
- `message.content` — either a string or an array of content blocks (`{type: "text", text: "…"}`, `{type: "tool_use", …}`, `{type: "tool_result", …}`).
- `timestamp` — ISO-8601 string.
- `isCompactSummary` — present and `true` only on compaction-summary entries (already filtered out).

Because `message.content` is sometimes a string and sometimes an array, `(.message.content | tostring)` is the easiest way to text-match across both shapes.

## Examples

Find every user message:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/search_conversation.sh 'select(.type == "user")'
```

Case-insensitive substring search across every turn, printed as `<timestamp> <first 200 chars>`:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/search_conversation.sh -r \
  'select((.message.content | tostring) | test("plan mode"; "i"))
   | (.timestamp // "") + " " + (.message.content | tostring)[0:200]'
```

All assistant messages, piped to `head`:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/search_conversation.sh 'select(.type == "assistant") | .message.content' | head
```

Inspect an arbitrary transcript without touching env vars:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/search_conversation.sh --log-file ~/.claude/projects/-Users-me-proj/abcd.jsonl '.type' | sort -u
```

## When to prefer the Explore agent instead

`jq` only does exact / regex matching. If the user asks a fuzzy question ("when did we talk about the caching strategy?") and nothing obvious matches, use the log file path printed on the last line of the script's output and start an `Explore` sub-agent pointed at that file.
