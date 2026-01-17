# Manual Hook/Rule Tests for Claude

This directory contains files designed to manually test different types of deepwork rules/hooks.
Each file exercises one specific rule style and includes instructions on how to trigger it.

## Test Files Overview

| File | Rule Type | How to Trigger |
|------|-----------|----------------|
| `test_trigger_safety_mode.py` | Trigger/Safety | Edit this file WITHOUT editing `test_trigger_safety_mode_doc.md` |
| `test_set_mode_source.py` | Set (Bidirectional) | Edit this file WITHOUT editing `test_set_mode_test.py` (or vice versa) |
| `test_pair_mode_trigger.py` | Pair (Directional) | Edit this file WITHOUT editing `test_pair_mode_expected.md` |
| `test_command_action.txt` | Command Action | Edit this file to trigger automatic line append |
| `test_multi_safety.py` | Multiple Safety Patterns | Edit this file WITHOUT editing ANY of the safety files |

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
