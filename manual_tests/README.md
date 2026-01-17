# Manual Hook/Rule Tests for Claude

This directory contains files designed to manually test different types of deepwork rules/hooks.
Each test must verify BOTH that the rule fires when it should AND does not fire when it shouldn't.

## How to Run These Tests

**The best way to run these tests is as sub-agents using a fast model (e.g., haiku).**

This approach works because:
1. Sub-agents run in isolated contexts where changes can be detected
2. The Stop hook evaluates rules when the sub-agent completes
3. Using a fast model keeps test iterations quick and cheap

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

## Test Results Tracking

| Test Case | Fires When Should | Does NOT Fire When Shouldn't |
|-----------|:-----------------:|:----------------------------:|
| Trigger/Safety | ☐ | ☐ |
| Set Mode | ☐ | ☐ |
| Pair Mode (forward) | ☐ | ☐ |
| Pair Mode (reverse - expected only) | — | ☐ |
| Command Action | ☐ | — |
| Multi Safety | ☐ | ☐ |

## Test Folders

| Folder | Rule Type | Description |
|--------|-----------|-------------|
| `test_trigger_safety_mode/` | Trigger/Safety | Basic conditional: fires unless safety file also edited |
| `test_set_mode/` | Set (Bidirectional) | Files must change together (either direction) |
| `test_pair_mode/` | Pair (Directional) | One-way: trigger requires expected, but not vice versa |
| `test_command_action/` | Command Action | Automatically runs command on file change |
| `test_multi_safety/` | Multiple Safety | Fires unless ANY of the safety files also edited |

## Corresponding Rules

Rules are defined in `.deepwork/rules/`:
- `manual-test-trigger-safety.md`
- `manual-test-set-mode.md`
- `manual-test-pair-mode.md`
- `manual-test-command-action.md`
- `manual-test-multi-safety.md`
