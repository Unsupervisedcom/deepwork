# Learning Log Folder Structure

Session-level agent interaction logs are stored in `.deepwork/tmp/agent_sessions/`. These directories track which LearningAgents were used and what issues were found during learning cycles.

## Directory Layout

```
.deepwork/tmp/agent_sessions/
└── <session_id>/
    └── <agent_id>/
        ├── needs_learning_as_of_timestamp      # Flag: learning needed (auto-created by hook)
        ├── learning_last_performed_timestamp    # When learning was last run on this conversation
        ├── agent_used                           # Name of the LearningAgent (auto-created by hook)
        └── <brief-name>.issue.yml               # Issue files (created during learning cycle)
```

## Files

### needs_learning_as_of_timestamp

Created automatically by the post-Task hook whenever a LearningAgent is used. The file body contains a single ISO 8601 timestamp indicating when the agent was last invoked. This file serves as a flag: its presence means the session transcript has not yet been processed for learnings.

Deleted by `incorporate_learnings` after all issues in the folder have been processed.

### learning_last_performed_timestamp

Updated by `incorporate_learnings` after processing issues in this conversation. Contains a single ISO 8601 timestamp. Used by the `identify` skill to skip already-processed portions of the transcript — if this file exists, identification starts scanning from that point forward rather than re-reading the entire transcript.

### agent_used

Created automatically by the post-Task hook. Contains the name of the LearningAgent that was used in this session (matching the folder name under `.deepwork/learning-agents/`). This links the session's agent_id back to the LearningAgent definition so learning skills can look up the agent's instructions and knowledge.

### *.issue.yml

Issue files created during the `identify` and `report_issue` skills. See `issue_yml_format.md` for the full schema. These files progress through statuses: `identified` → `investigated` → `learned`.

## Lifecycle

1. **Agent used**: Post-Task hook creates `needs_learning_as_of_timestamp` and `agent_used`
2. **Session ends**: Stop hook detects `needs_learning_as_of_timestamp` files and suggests running a learning cycle
3. **Learning cycle** (`/learning-agents learn`):
   a. `identify` reads transcripts and creates `*.issue.yml` files with status `identified`
   b. `investigate_issues` researches each issue and updates status to `investigated`
   c. `incorporate_learnings` integrates learnings into the agent and updates status to `learned`
   d. `needs_learning_as_of_timestamp` is deleted
   e. `learning_last_performed_timestamp` is updated in this folder

## Notes

- The `session_id` comes from Claude Code's session identifier
- The `agent_id` is the unique agent ID assigned by Claude Code when spawning a Task
- The `.deepwork/tmp/` directory is intended for transient working files and can be gitignored
- Transcript files referenced by issues are Claude Code's own session transcripts (typically at `~/.claude/projects/.../sessions/<session_id>/transcript.jsonl`)
