---
name: "Manual Test: Command Action"
trigger: manual_tests/test_command_action/test_command_action.txt
action:
  command: echo "$(date '+%Y-%m-%d %H:%M:%S') - Command triggered by edit to {file}" >> manual_tests/test_command_action/test_command_action_log.txt
  run_for: each_match
compare_to: prompt
prompt_runtime: send_to_stopping_agent
---

# Manual Test: Command Action

This rule automatically appends a timestamped log entry when the
test file is edited. No agent prompt is shown - the command runs
automatically.

## This tests:

The command action feature where rules can execute shell commands
instead of prompting the agent. The command should be idempotent.
