# Additional Learning Guidelines

These files let you customize how the learning cycle works for this agent. Each file is automatically included in the corresponding learning skill. Leave empty to use default behavior, or add markdown instructions to guide the process.

## Files

- **issue_identification.md** — Included during the `identify` step. Use this to tell the reviewer what kinds of issues matter most for this agent, what to ignore, or domain-specific signals of mistakes.

- **issue_investigation.md** — Included during the `investigate-issues` step. Use this to guide root cause analysis — e.g., common root causes in this domain, which parts of the agent's knowledge to check first, or investigation heuristics.

- **learning_from_issues.md** — Included during the `incorporate-learnings` step. Use this to guide how learnings are integrated — e.g., preferences for topics vs learnings, naming conventions, or areas of core-knowledge that should stay concise.
