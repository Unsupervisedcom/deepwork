# Manual Hook/Rule Tests for Claude

This directory contains files designed to manually test different types of deepwork rules/hooks.
Each test must verify BOTH that the rule fires when it should AND does not fire when it shouldn't.

## How to Run These Tests

**The best way to run these tests is as sub-agents using a fast model (e.g., haiku).**

This approach works because:
1. Sub-agents run in isolated contexts where changes can be detected
2. The Stop hook evaluates rules when the sub-agent completes
3. Using a fast model keeps test iterations quick and cheap

### Parallel vs Serial Execution

**Important:** All sub-agents share the same git working directory. This affects which tests can run in parallel.

**"Should NOT fire" tests CAN run in parallel:**
- These tests edit both trigger AND safety files (completing the rule requirements)
- Even though `git status` shows changes from all sub-agents, each rule only matches its own scoped file patterns
- Since the safety file is edited, the rule won't fire regardless of other changes
- No cross-contamination possible
- **Revert all changes after these tests complete** before running "should fire" tests

**"Should fire" tests MUST run serially with git reverts between each:**
- These tests deliberately edit only the trigger file (not the safety)
- If multiple run in parallel, sub-agent A's hook will see changes from sub-agent B
- This causes cross-contamination: A gets blocked by rules triggered by B's changes
- Run one at a time, reverting between each test

### Verification Commands

After each sub-agent returns, run the hook to verify:
```bash
echo '{}' | python -m deepwork.hooks.rules_check
```

Then revert changes before the next test:
```bash
git checkout -- manual_tests/
```

## Test Matrix

Each test has two cases: one where the rule SHOULD fire, and one where it should NOT.

| Test | Should Fire | Should NOT Fire | Rule Name |
|------|-------------|-----------------|-----------|
| **Trigger/Safety** | Edit `.py` only | Edit `.py` AND `_doc.md` | Manual Test: Trigger Safety |
| **Set Mode** | Edit `_source.py` only | Edit `_source.py` AND `_test.py` | Manual Test: Set Mode |
| **Pair Mode** | Edit `_trigger.py` only | Edit `_trigger.py` AND `_expected.md` | Manual Test: Pair Mode |
| **Pair Mode (reverse)** | — | Edit `_expected.md` only (should NOT fire) | Manual Test: Pair Mode |
| **Command Action** | Edit `.txt` → log appended | — (always runs) | Manual Test: Command Action |
| **Multi Safety** | Edit `.py` only | Edit `.py` AND any safety file | Manual Test: Multi Safety |
| **Infinite Block Prompt** | Edit `.py` (always blocks) | Provide `<promise>` tag | Manual Test: Infinite Block Prompt |
| **Infinite Block Command** | Edit `.py` (command fails) | Provide `<promise>` tag | Manual Test: Infinite Block Command |
| **Created Mode** | Create NEW `.yml` file | Modify EXISTING `.yml` file | Manual Test: Created Mode |
| **Claude Runtime** | Edit `.py` → Claude invoked | Claude returns `allow` | Manual Test: Claude Runtime |

## Test Results Tracking

| Test Case | Fires When Should | Does NOT Fire When Shouldn't |
|-----------|:-----------------:|:----------------------------:|
| Trigger/Safety | ☐ | ☐ |
| Set Mode | ☐ | ☐ |
| Pair Mode (forward) | ☐ | ☐ |
| Pair Mode (reverse - expected only) | — | ☐ |
| Command Action | ☐ | — |
| Multi Safety | ☐ | ☐ |
| Infinite Block Prompt | ☐ | ☐ |
| Infinite Block Command | ☐ | ☐ |
| Created Mode | ☐ | ☐ |
| Claude Runtime | ☐ | ☐ |

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
| `test_claude_runtime/` | Claude Runtime | Invokes Claude Code in headless mode instead of returning prompt |

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
- `manual-test-claude-runtime.md`
