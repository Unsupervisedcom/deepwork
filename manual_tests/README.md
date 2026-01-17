# Manual Hook/Rule Tests for Claude

This directory contains files designed to manually test different types of deepwork rules/hooks.
Each file exercises one specific rule style and includes instructions on how to trigger it.

## How to Run These Tests

**The best way to run these tests is as sub-agents using a fast model (e.g., haiku).**

This approach works because:
1. Sub-agents run in isolated contexts where changes can be detected
2. The Stop hook evaluates rules when the sub-agent completes
3. Using a fast model keeps test iterations quick and cheap

Example prompt to test a rule:
```
Use the Task tool with model: haiku to launch a sub-agent that:
1. Reads the trigger file
2. Adds a comment at the bottom
3. Does NOT edit the safety/expected file
4. Reports what happened
```

After the sub-agent returns, manually run the hook to verify:
```bash
echo '{}' | python -m deepwork.hooks.rules_check
```

## Test Folders Overview

| Folder | Rule Type | How to Trigger |
|--------|-----------|----------------|
| `test_trigger_safety_mode/` | Trigger/Safety | Edit `.py` WITHOUT editing `_doc.md` |
| `test_set_mode/` | Set (Bidirectional) | Edit `_source.py` WITHOUT `_test.py` (or vice versa) |
| `test_pair_mode/` | Pair (Directional) | Edit `_trigger.py` WITHOUT `_expected.md` |
| `test_command_action/` | Command Action | Edit `.txt` to trigger automatic line append |
| `test_multi_safety/` | Multiple Safety | Edit `.py` WITHOUT any of the safety files |

## Corresponding Rules

The rules for these tests are defined in `.deepwork/rules/`:
- `manual-test-trigger-safety.md`
- `manual-test-set-mode.md`
- `manual-test-pair-mode.md`
- `manual-test-command-action.md`
- `manual-test-multi-safety.md`

## Usage

1. Open a Claude Code session in this repository
2. Edit one of the test files as described
3. The corresponding rule should fire
4. Use `<promise>Rule Name</promise>` to acknowledge the rule

## Testing Checklist

- [ ] Trigger/Safety: Rule fires when source edited alone, suppressed when both edited
- [ ] Set Mode: Rule fires from either direction when one file edited alone
- [ ] Pair Mode: Rule fires when trigger edited alone, NOT when expected edited alone
- [ ] Command Action: Command runs automatically and appends line to file
- [ ] Multi-Safety: Rule fires only when ALL safety files are missing
