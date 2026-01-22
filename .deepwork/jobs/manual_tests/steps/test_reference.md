# Manual Hook/Rule Tests Reference

This document contains the test matrix and reference information for all manual hook/rule tests.

## Why Sub-Agents?

**All tests MUST be run in sub-agents, not by the main agent directly.**

This approach works because:
1. Sub-agents run in isolated contexts where file changes can be detected
2. The Stop hook **automatically** evaluates rules when the sub-agent completes
3. Sub-agents report via **magic strings** that the main agent checks to determine pass/fail
4. Using a fast model (e.g., haiku) keeps test iterations quick and cheap

## Magic String Detection

Sub-agents are instructed to output specific strings:
- `TASK_START: <task name>` - ALWAYS output at the beginning of the response
- `HOOK_FIRED: <rule name>` - Output if a DeepWork hook blocks them

**How detection works:**
- Sub-agent ALWAYS outputs `TASK_START:` at the beginning of their response
- If a hook fires and blocks them, they get another turn and can output `HOOK_FIRED:`
- Main agent checks:
  - `TASK_START:` present + no `HOOK_FIRED:` → hook did NOT fire
  - `HOOK_FIRED:` present → hook fired
  - Neither → timeout (hook is blocking infinitely)

## Task Tool Parameters

All sub-agent Task calls MUST include:
- `model: "haiku"` - Use the fast model to minimize cost and latency
- `max_turns: 5` - Prevent infinite hangs (limits to ~5 API round-trips)

**Timeout handling:**
- If a sub-agent hits the max_turns limit in a "should NOT fire" test → Test FAILED (timeout indicates unexpected blocking)
- If a sub-agent hits the max_turns limit in a "should fire" test → Test PASSED (timeout confirms hook is blocking)

## Critical Rules

1. **NEVER edit test files from the main agent** - always spawn a sub-agent to make edits
2. **NEVER manually run the rules_check command** - hooks fire automatically when sub-agents return
3. **SET Task parameters** - use `model: "haiku"` and `max_turns: 5` on every Task call
4. **CHECK the magic strings** - look for `TASK_START:` (always present) and `HOOK_FIRED:` (present if hook fired)
5. **REVERT between tests** - use `git reset HEAD manual_tests/ && git checkout -- manual_tests/` to reset files

## Parallel vs Serial Execution

**"Should NOT fire" tests CAN run in parallel:**
- These tests edit BOTH trigger AND safety files (completing the rule requirements)
- Even though `git status` shows changes from all sub-agents, each rule only matches its own scoped file patterns
- Since the safety file is edited, the rule won't fire regardless of other changes
- No cross-contamination possible
- Check each sub-agent's response: `TASK_START:` present + no `HOOK_FIRED:` = PASS
- **Revert all changes after these tests complete** before running "should fire" tests

**"Should fire" tests MUST run serially with git reverts between each:**
- These tests deliberately edit ONLY the trigger file (not the safety)
- If multiple run in parallel, sub-agent A's hook will see changes from sub-agent B
- This causes cross-contamination: A gets blocked by rules triggered by B's changes
- Run one at a time, reverting between each test
- Check each sub-agent's response: `HOOK_FIRED:` present OR timeout = PASS

## Test Matrix

Each test has two cases: one where the rule SHOULD fire, and one where it should NOT.

| Test | Should Fire | Should NOT Fire | Rule Name |
|------|-------------|-----------------|-----------|
| **Trigger/Safety** | Edit `.py` only | Edit `.py` AND `_doc.md` | Manual Test: Trigger Safety |
| **Set Mode** | Edit `_source.py` only | Edit `_source.py` AND `_test.py` | Manual Test: Set Mode |
| **Pair Mode** | Edit `_trigger.py` only | Edit `_trigger.py` AND `_expected.md` | Manual Test: Pair Mode |
| **Pair Mode (reverse)** | -- | Edit `_expected.md` only (should NOT fire) | Manual Test: Pair Mode |
| **Command Action** | Edit `.txt` -> log appended | -- (always runs) | Manual Test: Command Action |
| **Multi Safety** | Edit `.py` only | Edit `.py` AND any safety file | Manual Test: Multi Safety |
| **Infinite Block Prompt** | Edit `.py` (always blocks) | Provide `<promise>` tag | Manual Test: Infinite Block Prompt |
| **Infinite Block Command** | Edit `.py` (command fails) | Provide `<promise>` tag | Manual Test: Infinite Block Command |
| **Created Mode** | Create NEW `.yml` file | Modify EXISTING `.yml` file | Manual Test: Created Mode |

## Test Folders

| Folder | Rule Type | Description |
|--------|-----------|-------------|
| `test_trigger_safety_mode/` | Trigger/Safety | Basic conditional: fires unless safety file also edited |
| `test_set_mode/` | Set (Bidirectional) | Files must change together (either direction) |
| `test_pair_mode/` | Pair (Directional) | One-way: trigger requires expected, but not vice versa |
| `test_command_action/` | Command Action | Automatically runs command on file change |
| `test_multi_safety/` | Multiple Safety | Fires unless ANY of the safety files also edited |
| `test_infinite_block_prompt/` | Infinite Block (Prompt) | Always blocks with prompt; only promise can bypass |
| `test_infinite_block_command/` | Infinite Block (Command) | Command always fails; tests if promise skips command |
| `test_created_mode/` | Created (New Files Only) | Fires ONLY when NEW files are created, not when existing modified |

## Corresponding Rules

Rules are defined in `.deepwork/rules/`:
- `manual-test-trigger-safety.md`
- `manual-test-set-mode.md`
- `manual-test-pair-mode.md`
- `manual-test-command-action.md`
- `manual-test-multi-safety.md`
- `manual-test-infinite-block-prompt.md`
- `manual-test-infinite-block-command.md`
- `manual-test-created-mode.md`

## Results Tracking Template

Use this template to track test results:

| Test Case | Fires When Should | Does NOT Fire When Shouldn't |
|-----------|:-----------------:|:----------------------------:|
| Trigger/Safety | [ ] | [ ] |
| Set Mode | [ ] | [ ] |
| Pair Mode (forward) | [ ] | [ ] |
| Pair Mode (reverse - expected only) | -- | [ ] |
| Command Action | [ ] | -- |
| Multi Safety | [ ] | [ ] |
| Infinite Block Prompt | [ ] | [ ] |
| Infinite Block Command | [ ] | [ ] |
| Created Mode | [ ] | [ ] |
