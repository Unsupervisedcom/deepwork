# Manual Hook/Rule Tests

This directory contains files designed to test different types of DeepWork rules/hooks.

## How to Run These Tests

**Use the `/manual_tests` job to run these tests.**

```
/manual_tests
```

This job automates the test execution process, ensuring:
1. All tests run in **sub-agents** (required for hooks to fire automatically)
2. "Should NOT fire" tests run in **parallel** for efficiency
3. "Should fire" tests run **serially** with git reverts between each to prevent cross-contamination
4. Hooks fire **automatically** when sub-agents complete (never manually triggered)

## Why Use the Job?

Running these tests correctly requires specific patterns:
- **Sub-agents are mandatory** - the main agent cannot trigger hooks by editing files directly
- **Hooks must fire automatically** - manually running `rules_check` defeats the purpose
- **Serial execution with reverts** - "should fire" tests must not run in parallel

The `/manual_tests` job enforces all these requirements and guides you through the process.

## Test Folders

| Folder | Rule Type |
|--------|-----------|
| `test_trigger_safety_mode/` | Basic trigger/safety conditional |
| `test_set_mode/` | Bidirectional file pairing |
| `test_pair_mode/` | One-way directional pairing |
| `test_command_action/` | Automatic command execution |
| `test_multi_safety/` | Multiple safety files |
| `test_infinite_block_prompt/` | Infinite blocking with prompt |
| `test_infinite_block_command/` | Infinite blocking with command |
| `test_created_mode/` | New file creation detection |

## Corresponding Rules

Rules are defined in `.deepwork/rules/manual-test-*.md`
