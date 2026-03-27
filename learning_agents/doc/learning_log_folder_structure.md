# Learning Log Folder Structure

Session-level agent interaction logs are stored in `.deepwork/tmp/agent_sessions/`. These directories track which LearningAgents were used and what issues were found during learning cycles.

## Directory Layout

```
.deepwork/tmp/agent_sessions/
└── <session_id>/
    ├── <agent_id>/                              # Subagent sessions (created by post-Task hook)
    │   ├── conversation_transcript.jsonl        # Symlink to subagent transcript
    │   ├── needs_learning_as_of_timestamp       # Flag: learning needed
    │   ├── learning_last_performed_timestamp    # When learning was last run
    │   ├── agent_used                           # Name of the LearningAgent
    │   └── <brief-name>.issue.yml               # Issue files (created during learning cycle)
    └── top-level/                               # Top-level agent sessions (--agent flag, created by Stop hook)
        ├── conversation_transcript.jsonl        # Symlink to session transcript
        ├── needs_learning_as_of_timestamp       # Flag: learning needed
        ├── learning_last_performed_timestamp    # When learning was last run
        ├── agent_used                           # Name of the LearningAgent
        └── <brief-name>.issue.yml               # Issue files (created during learning cycle)
```

Subagent sessions use the Claude Code-assigned `agent_id` as the directory name. Top-level agent sessions (started with `claude --agent <name>`) use the fixed name `top-level`.

## Files

### conversation_transcript.jsonl

A symlink to the agent's Claude Code transcript. For subagent sessions, points to `~/.claude/projects/<project-hash>/<session_id>/subagents/agent-<agent_id>.jsonl` (created by post-Task hook). For top-level agent sessions, points directly to the session transcript at `transcript_path` (created by Stop hook).

The symlink is only created if the transcript file exists at hook execution time.

### needs_learning_as_of_timestamp

Created automatically by the post-Task hook (subagent sessions) or Stop hook (top-level agent sessions) whenever a LearningAgent is used. The file body contains a single ISO 8601 timestamp indicating when the agent was last invoked. This file serves as a flag: its presence means the session transcript has not yet been processed for learnings.

Deleted by `incorporate_learnings` after all issues in the folder have been processed.

### learning_last_performed_timestamp

Updated by `incorporate_learnings` after processing issues in this conversation. Contains a single ISO 8601 timestamp. Used by the `identify` skill to skip already-processed portions of the transcript — if this file exists, identification starts scanning from that point forward rather than re-reading the entire transcript.

### agent_used

Created automatically by the post-Task hook (subagent sessions) or Stop hook (top-level agent sessions). Contains the name of the LearningAgent that was used in this session (matching the folder name under `.deepwork/learning-agents/`). This links the session back to the LearningAgent definition so learning skills can look up the agent's instructions and knowledge.

### *.issue.yml

Issue files created during the `identify` and `report_issue` skills. See `issue_yml_format.md` for the full schema. These files progress through statuses: `identified` → `investigated` → `learned`.

### conversation_transcript.jsonl

Symlink to the agent's Claude Code transcript, created automatically by the post-Task hook. **THIS IS THE FILE TO READ TO SEE THE CONVERSATION ALL THE OTHER FILES REFER TO.**

## Lifecycle

1. **Agent used**: Post-Task hook (subagent) or Stop hook (top-level `--agent`) creates `needs_learning_as_of_timestamp`, `agent_used`, and `conversation_transcript.jsonl` symlink
2. **Session ends**: Stop hook detects `needs_learning_as_of_timestamp` files and suggests running a learning cycle
3. **Learning cycle** (`/learning-agents learn`):
   a. `identify` reads transcripts and creates `*.issue.yml` files with status `identified`
   b. `investigate_issues` researches each issue and updates status to `investigated`
   c. `incorporate_learnings` integrates learnings into the agent and updates status to `learned`
   d. `needs_learning_as_of_timestamp` is deleted
   e. `learning_last_performed_timestamp` is updated in this folder

## Notes

- The `session_id` comes from Claude Code's session identifier
- For subagent sessions, the `agent_id` is the unique agent ID assigned by Claude Code when spawning a Task
- For top-level agent sessions (started with `claude --agent <name>`), the directory name is `top-level` instead of an agent_id
- The `.deepwork/tmp/` directory is intended for transient working files and can be gitignored
