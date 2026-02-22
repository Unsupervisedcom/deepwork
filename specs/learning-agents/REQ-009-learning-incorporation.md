# REQ-009: Learning Incorporation

## Overview

The `incorporate-learnings` skill takes investigated issues and integrates the lessons learned into the LearningAgent's knowledge base. It decides the best incorporation strategy for each issue, updates the appropriate files, and manages session tracking state.

## Requirements

### REQ-009.1: Skill Visibility

The `incorporate-learnings` skill MUST NOT be directly invocable by the user (`user-invocable: false`). It MUST only be invoked programmatically by the `learn` skill via a Task.

### REQ-009.2: Input Argument

The skill MUST accept a single argument: the path to the session log folder (e.g., `.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/`).

### REQ-009.3: Agent Context Loading

The skill MUST dynamically load:
- The agent name from `$ARGUMENTS/agent_used`
- Additional incorporation guidelines from `.deepwork/learning-agents/<agent-name>/additional_learning_guidelines/learning_from_issues.md`

### REQ-009.4: Unknown Agent Handling

If the `agent_used` file reads "unknown" or is missing, the skill MUST stop and report an error indicating the session folder is missing required metadata.

### REQ-009.5: Issue Discovery

The skill MUST find all issue files with `status: investigated` in the session folder.

### REQ-009.6: No Investigated Issues

If no investigated issues are found, the skill MUST report that finding and skip to Step 5 (session tracking update). The skill MUST still update tracking files even when there are no issues to incorporate.

### REQ-009.7: Knowledge Base Reading

Before incorporating any issue, the skill MUST read the current state of the agent's knowledge:
- `.deepwork/learning-agents/<agent-name>/core-knowledge.md`
- All files in `.deepwork/learning-agents/<agent-name>/topics/`
- All files in `.deepwork/learning-agents/<agent-name>/learnings/`

### REQ-009.8: Incorporation Strategy Priority

The skill MUST evaluate incorporation options in this priority order:
1. **Amend existing content** (highest priority): If a closely related file already exists in the knowledge base covering the same area, edit that file rather than creating a new one
2. **Update core-knowledge.md**: For universal one-liners -- fundamental knowledge expressible in 1-2 sentences
3. **Add a new topic**: When the issue reveals a conceptual area needing 1+ paragraphs of reference material
4. **Add a new learning**: When the narrative context of how the issue unfolded is needed to understand the resolution
5. **Do nothing**: When the issue would be hard to prevent or is extremely unlikely to recur

### REQ-009.9: Amend Existing Content

When amending existing content, the skill MUST edit the relevant existing file (topic or learning) rather than creating a new file. The skill MUST NOT create duplicates of existing knowledge.

### REQ-009.10: Core Knowledge Updates

When updating `core-knowledge.md`, the skill MUST keep additions concise (1-2 sentences). Detailed content MUST be moved to topics or learnings instead.

### REQ-009.11: New Topic File Format

When creating a new topic, the file MUST follow the format specified in REQ-003.7, including YAML frontmatter with `name`, optional `keywords`, and `last_updated` set to today's date.

### REQ-009.12: New Learning File Format

When creating a new learning, the file MUST follow the format specified in REQ-003.10, including YAML frontmatter with `name`, `last_updated` set to today's date, and `summarized_result`. The body MUST include Context, Investigation, Resolution, and Key Takeaway sections.

### REQ-009.13: Cross-Reference for Learnings

When adding a learning entry, the skill SHOULD also add a brief note to a related topic with a reference to the learning.

### REQ-009.14: No Duplicate Knowledge

Before adding new content, the skill MUST check existing knowledge base files to avoid duplicating information that already exists.

### REQ-009.15: No Content Removal

The skill MUST NOT remove existing content from the knowledge base unless it is directly contradicted by new evidence from the investigation.

### REQ-009.16: Status Update to Learned

For each incorporated issue, the skill MUST update the issue file to change `status: investigated` to `status: learned`.

### REQ-009.17: Delete Needs Learning Flag

The skill MUST delete the `needs_learning_as_of_timestamp` file from the session folder if it exists, regardless of whether any issues were incorporated.

### REQ-009.18: Update Learning Timestamp

The skill MUST write the current UTC timestamp (ISO 8601 format) to `learning_last_performed_timestamp` in the session folder, regardless of whether any issues were incorporated.

### REQ-009.19: Tracking Update Always Runs

The session tracking updates (REQ-009.17 and REQ-009.18) MUST always execute, even if no investigated issues were found or if all issues resulted in "do nothing" decisions.

### REQ-009.20: Last Updated Date

When creating or updating topic or learning files, the `last_updated` field MUST be set to today's date in YYYY-MM-DD format.

### REQ-009.21: Summary Output

The skill MUST output a summary containing:
- Total issues processed
- For each issue: the filename and action taken (updated core-knowledge, created topic, created learning, amended existing file, or could not incorporate with reason)

### REQ-009.22: Allowed Tools

The skill MUST only use the following tools: Read, Grep, Glob, Edit, Write.
