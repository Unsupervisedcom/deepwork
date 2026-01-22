# Hooks System Debugging History

This document records debugging sessions and findings for the DeepWork hooks system.

---

## 2026-01-22: Infinite Loop Bug in Command Rules

### Symptoms

The manual tests "Infinite Block Command - Should Fire (no promise)" were hanging infinitely. The sub-agents spawned to test these rules never returned, even with `max_turns: 5` configured.

### Investigation

The `rules_check.py` hook handles two types of rule actions:
1. **PROMPT rules**: Show instructions to the agent
2. **COMMAND rules**: Run a shell command (e.g., linting, type checking)

For **PROMPT rules**, there was existing logic to prevent infinite loops (lines 617-624 in `rules_check.py`):

```python
# For PROMPT rules, also skip if already QUEUED (already shown to agent).
# This prevents infinite loops when transcript is unavailable or promise
# tags haven't been written yet. The agent has already seen this rule.
if (
    existing
    and existing.status == QueueEntryStatus.QUEUED
    and rule.action_type == ActionType.PROMPT
):
    continue
```

However, for **COMMAND rules**, there was no equivalent protection. The flow was:

1. Agent edits file
2. Hook runs, command fails, status set to FAILED, blocks with error
3. Agent sees error, responds (without promise)
4. Hook runs again
5. Rule triggers (same files still modified)
6. Existing entry has status FAILED, but FAILED is not in skip conditions
7. Command runs again, fails again, blocks again
8. Go to step 3 → **infinite loop**

### Root Cause

The queue status checks only skipped rules with status PASSED or SKIPPED:

```python
if existing and existing.status in (
    QueueEntryStatus.PASSED,
    QueueEntryStatus.SKIPPED,
):
    continue
```

Command rules with FAILED status were not skipped, causing them to re-run on every hook invocation until a promise was provided. But without any way for the agent to know it was in a loop, the command would run infinitely.

### The Fix

Two-part fix in `rules_check.py`:

1. **Prevent re-running**: Skip COMMAND rules with FAILED status to prevent infinite loops:

```python
# For COMMAND rules with FAILED status, don't re-run the command.
# The agent has already seen the error.
if (
    existing
    and existing.status == QueueEntryStatus.FAILED
    and rule.action_type == ActionType.COMMAND
):
    continue
```

2. **Honor promises**: After processing results, check all FAILED queue entries and update to SKIPPED if the agent provided a promise:

```python
# Handle FAILED queue entries that have been promised
if promised_rules:
    promised_lower = {name.lower() for name in promised_rules}
    for entry in queue.get_all_entries():
        if (
            entry.status == QueueEntryStatus.FAILED
            and entry.rule_name.lower() in promised_lower
        ):
            queue.update_status(
                entry.trigger_hash,
                QueueEntryStatus.SKIPPED,
                ActionResult(
                    type="command",
                    output="Acknowledged via promise tag",
                    exit_code=None,
                ),
            )
```

This ensures that:
- A failing command only runs once per trigger
- The agent sees the error message once
- When the agent provides a `<promise>Rule Name</promise>` tag, the queue entry is properly updated to SKIPPED
- No infinite loop occurs

### Test Cases Affected

- `manual_tests/test_infinite_block_command/` - Tests a rule with `command: "false"` (always fails)
- The test verifies that the hook fires AND the sub-agent returns in reasonable time (doesn't hang)

### Key Learnings

1. **Any hook action that can block must have loop prevention**: Both PROMPT and COMMAND rules need mechanisms to prevent re-triggering infinitely.

2. **Queue status is the key to loop prevention**: The rules queue tracks what the agent has already seen. Rules should not re-trigger if they've already been shown to the agent (QUEUED for prompts, FAILED for commands).

3. **Symmetry in action handling**: When adding loop prevention for one action type, check if other action types need similar protection.

### Related Files

- `src/deepwork/hooks/rules_check.py` - Main hook implementation
- `src/deepwork/core/rules_queue.py` - Queue entry status definitions
- `.deepwork/rules/manual-test-infinite-block-command.md` - Test rule
- `manual_tests/test_infinite_block_command/` - Test files

---

*For the template and guidelines on documenting debugging sessions, see [AGENTS.md](./AGENTS.md).*
