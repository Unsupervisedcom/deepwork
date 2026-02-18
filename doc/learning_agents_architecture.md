# LearningAgents Architecture

## Overview

LearningAgents are auto-improving AI sub-agents that accumulate domain knowledge across sessions. They are implemented as a Claude Code plugin (`learning_agents`) that adds hooks, skills, and agents to enable a closed-loop learning cycle: use an agent → track its sessions → identify mistakes → investigate root causes → incorporate learnings back into the agent.

This design is inspired by the "experts" system from PR #192 but restructured as a standalone Claude Code plugin with session-level issue tracking and automated learning workflows.

## Core Concepts

### LearningAgent
A sub-agent with a persistent knowledge base that improves over time. Defined in `.deepwork/learning-agents/<agent-name>/` with structured expertise, topics, and learnings. Each LearningAgent gets a corresponding `.claude/agents/` file that dynamically loads its current knowledge at invocation time.

### Learning Cycle
The feedback loop that makes agents improve:
1. **Use** — Agent is invoked via Task tool during normal work
2. **Track** — Post-Task hook records the session for later review
3. **Identify** — Transcript is reviewed for issues/mistakes
4. **Investigate** — Root causes are determined from transcript evidence
5. **Incorporate** — Learnings are folded back into the agent's knowledge base

### Session Logs
Temporary per-session records in `.deepwork/tmp/agent_sessions/` that track which LearningAgents were used and flag sessions needing learning. These are transient working files, not permanent records.

## Plugin Structure

```
learning_agents/
├── .claude-plugin/
│   └── plugin.json                        # Plugin manifest
├── skills/
│   ├── learning-agents/SKILL.md           # Dispatch skill (user-facing)
│   ├── create-agent/SKILL.md              # Create new LearningAgent
│   ├── learn/SKILL.md                     # Run learning cycle on all pending sessions
│   ├── identify/SKILL.md                  # [hidden] Find issues in a session transcript
│   ├── report-issue/SKILL.md              # [hidden] Create an issue file
│   ├── investigate-issues/SKILL.md        # [hidden] Research issue root causes
│   └── incorporate-learnings/SKILL.md     # [hidden] Integrate learnings into agent
├── scripts/
│   └── create_agent.sh                    # Setup script for new LearningAgent scaffolding
├── hooks/
│   ├── hooks.json                         # Hook configuration
│   ├── post_task.sh                       # After Task: track LearningAgent usage
│   └── session_stop.sh                    # On Stop: suggest learning cycle if needed
├── agents/
│   └── learning-agent-expert.md           # LearningAgentExpert — knows how LearningAgents work
└── doc/
    ├── learning_agent_file_structure.md    # Structure of .deepwork/learning-agents/
    ├── learning_agent_post_task_reminder.md # Reminder shown after LearningAgent use
    ├── issue_yml_format.md                # Issue file schema
    └── learning_log_folder_structure.md   # Structure of .deepwork/tmp/agent_sessions/
```

## Data Layout

### LearningAgent Definition (persistent, Git-tracked)

```
.deepwork/learning-agents/<agent-name>/
├── core-knowledge.md                  # Core expertise in second person (required)
├── topics/
│   └── <topic>.md                     # Detailed reference docs (frontmatter + body)
├── learnings/
│   └── <learning>.md                  # Experience-based insights (frontmatter + body)
└── additional_learning_guidelines/    # Per-agent learning cycle customization
    ├── README.md
    ├── issue_identification.md        # Extra guidance for identify step
    ├── issue_investigation.md         # Extra guidance for investigate step
    └── learning_from_issues.md        # Extra guidance for incorporate step
```

See `learning_agent_file_structure.md` for full schema details.

### Generated Agent File

```
.claude/agents/<agent-name>.md
```

Created by `create-agent`. Uses Claude Code's `!`command`` dynamic context injection to include the agent's current `core-knowledge.md` and a topic index at invocation time. Topics are listed as an index (filename + name from frontmatter) rather than included in full, keeping the agent prompt focused. Learnings are referenced by directory path with a note about their purpose — the agent can read individual files as needed. The `!`command`` syntax runs shell commands before the content is sent to Claude — the command output replaces the placeholder.

Example structure:
```markdown
---
name: <agent-name>
description: "<discovery description>"
---

# Core Knowledge

!`cat .deepwork/learning-agents/<agent-name>/core-knowledge.md`

# Topics

Located in `.deepwork/learning-agents/<agent-name>/topics/`

!`for f in .deepwork/learning-agents/<agent-name>/topics/*.md; do [ -f "$f" ] || continue; desc=$(awk '/^---/{c++; next} c==1 && /^name:/{sub(/^name: *"?/,""); sub(/"$/,""); print; exit}' "$f"); echo "- $(basename "$f"): $desc"; done`

# Learnings

Learnings are incident post-mortems from past agent sessions capturing mistakes, root causes, and generalizable insights. Review them before starting work to avoid repeating past mistakes. Located in `.deepwork/learning-agents/<agent-name>/learnings/`.
```

### Session Logs (transient, gitignored)

```
.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/
├── needs_learning_as_of_timestamp      # Flag file (body = ISO 8601 timestamp)
├── learning_last_performed_timestamp   # When learning was last run on this conversation
├── agent_used                          # Body = LearningAgent folder name
└── <brief-name>.issue.yml              # Issues found during learning
```

See `learning_log_folder_structure.md` for full details.

## Hooks

### PostToolUse → Task (post_task.sh)

Fires after every `Task` tool call. The script:

1. Extracts the agent name from the Task's `tool_input`
2. Checks if a matching folder exists in `.deepwork/learning-agents/` — if not, exits silently
3. Creates `.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/needs_learning_as_of_timestamp` with current timestamp
4. Creates `.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/agent_used` with the agent name
5. Outputs the post-task reminder as feedback (contents of `learning_agent_post_task_reminder.md`)

**Hook config:**
```json
{
  "PostToolUse": [
    {
      "matcher": "Task",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/hooks/post_task.sh"
        }
      ]
    }
  ]
}
```

### Stop (session_stop.sh)

Fires when the main agent finishes responding. The script:

1. Searches for any `needs_learning_as_of_timestamp` files under `.deepwork/tmp/agent_sessions/`
2. If none found, exits silently (exit 0, no output)
3. If found, outputs feedback suggesting a learning cycle — does NOT block (exit 0 with stdout)

**Hook config:**
```json
{
  "Stop": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session_stop.sh"
        }
      ]
    }
  ]
}
```

## Skills

### User-Facing Skills

#### learning-agents (dispatch)
Entry point skill. Parses user intent and dispatches to the appropriate sub-skill:
- `/learning-agents create <name>` → invokes `create-agent`
- `/learning-agents learn` → invokes `learn`
- `/learning-agents report_issue <agent_id> <details>` → invokes `report-issue`

#### create-agent
Creates a new LearningAgent. The skill first invokes a setup script, then guides the user through filling in the content.

**Step 1 — Setup script (`scripts/create_agent.sh`)**

The skill invokes a bundled shell script that handles all the boilerplate:

1. Creates the LearningAgent directory structure:
   ```
   .deepwork/learning-agents/<agent-name>/
   ├── core-knowledge.md              # Stubbed with TODO placeholder
   ├── topics/                        # Empty directory
   ├── learnings/                     # Empty directory
   └── additional_learning_guidelines/
       ├── README.md                  # Explains each file's purpose
       ├── issue_identification.md    # Empty (customize for identify step)
       ├── issue_investigation.md     # Empty (customize for investigate step)
       └── learning_from_issues.md    # Empty (customize for incorporate step)
   ```

2. Creates the Claude Code agent frontmatter file at `.claude/agents/<agent-name>.md` with:
   - TODO entries for `name` and `description` in the frontmatter (to be filled in by the agent in step 2)
   - Body that uses `!`command`` dynamic includes to pull content from the LearningAgent directory at invocation time. Topics are included as an index (filename + name), not in full. Learnings are referenced by directory path:
   ```markdown
   ---
   name: TODO
   description: "TODO"
   ---

   # Core Knowledge

   !`cat .deepwork/learning-agents/<agent-name>/core-knowledge.md`

   # Topics

   Located in `.deepwork/learning-agents/<agent-name>/topics/`

   !`for f in .deepwork/learning-agents/<agent-name>/topics/*.md; do ...extract name from frontmatter...; echo "- $filename: $name"; done`

   # Learnings

   Learnings are incident post-mortems from past agent sessions. Located in `.deepwork/learning-agents/<agent-name>/learnings/`.
   ```

   This means the agent file never needs regeneration — it always reflects the latest knowledge at invocation time. Topics are indexed rather than fully included to keep the prompt focused.

**Step 2 — Fill in agent identity**

After the script runs, the skill prompts the user to describe what the agent is an expert in, then:
- Updates `core-knowledge.md` with the agent's expertise
- Updates the `.claude/agents/<agent-name>.md` frontmatter (`name` and `description`) to reflect the agent's domain

**Step 3 — Seed initial knowledge**

Fills in key files in the LearningAgent directory — initial topics and/or learnings if the user provides seed knowledge about the domain.

#### learn
Runs the full learning cycle on all sessions needing it. Workflow:
1. Uses `!`find ...`` to inject a list of all paths containing a `needs_learning_as_of_timestamp` file into the prompt
2. For each such folder, spawns a Task with the `LearningAgentExpert` agent using **Sonnet model** to run the `identify` skill
3. After identification completes, spawns a Task with the `LearningAgentExpert` to run `investigate-issues` then `incorporate-learnings` in sequence

### Hidden Skills (used by LearningAgentExpert during learning)

#### identify
Reviews a session transcript to find issues. Takes the session/agent_id folder path as an argument.
- Uses `!`cat ...`` to inject `learning_last_performed_timestamp` value into the prompt
- Reads the transcript and identifies mistakes, underperformance, or knowledge gaps
- Calls `report-issue` for each issue found
- If `learning_last_performed_timestamp` exists, starts scanning from that point

#### report-issue
Creates an `<brief-name>.issue.yml` file in the session's agent log folder. Sets initial status to `identified` with the issue description and observed timestamps. See `issue_yml_format.md` for the schema.

#### investigate-issues
Processes all `identified` issues in a session folder:
1. Finds issues with status `identified` (includes example bash command in skill prompt)
2. Uses `!`cat $0/agent_used`` to inject the agent name, then `!`cat`` to load the agent's instructions — avoiding extra round trips
3. Reads the agent's full expertise and knowledge
4. For each issue: reads relevant transcript sections, determines root cause, updates status to `investigated` with `investigation_report`

#### incorporate-learnings
Integrates investigated issues into the LearningAgent:
1. Finds issues with status `investigated` (includes example bash command)
2. For each issue, takes a learning action — one of:
   - **Update core knowledge**: Modify `core-knowledge.md` to address the knowledge gap
   - **Add a learning**: Create a new file in `learnings/` with the insight
   - **Add/update a topic**: Create or update a file in `topics/` with reference docs
   - **Update existing learning**: Amend an existing learning with new evidence
3. Updates issue status to `learned`
4. After all issues processed, deletes `needs_learning_as_of_timestamp`
5. Updates `learning_last_performed_timestamp` in the session log folder to current time

## Agents

### LearningAgentExpert

A standard (non-learning) agent defined in the plugin. Its prompt dynamically includes all the LearningAgent documentation via `!`cat ...``:

- `learning_agent_file_structure.md`
- `issue_yml_format.md`
- `learning_log_folder_structure.md`
- `learning_agent_post_task_reminder.md`

This agent is used by the `learn` skill to execute `identify`, `investigate-issues`, and `incorporate-learnings` sub-skills. It understands the full LearningAgent system and can work with any LearningAgent's files.

This is a **normal** agent (not a LearningAgent) because it ships with the plugin and should not evolve per-repo — it gets updated with the package.

## Design Decisions

### Why a Plugin (not a DeepWork Job)
LearningAgents are a cross-cutting concern that enhances any agent usage, not a specific multi-step workflow. A plugin can install hooks, skills, and agents in one unit. Jobs are for repeatable multi-step work products.

### Why `!`command`` Dynamic Includes
Static agent files go stale as learnings accumulate. By using Claude Code's `!`command`` dynamic context injection, the agent file always reflects the latest knowledge without requiring regeneration after every learning cycle. The shell commands run before content is sent to Claude, so Claude receives the actual data.

### Why Session-Level Issue Tracking
Issues are tied to specific transcripts for evidence. Storing them alongside session logs keeps the evidence linkage clear. Once learnings are incorporated, the session logs can be cleaned up without losing the persistent knowledge (which lives in the agent's `learnings/` directory).

### Why Sonnet for Learning Tasks
The `learn` skill spawns identification tasks using the Sonnet model. Transcript review is high-volume, pattern-matching work that doesn't require the most capable model. This keeps learning cycles fast and cost-effective.

### Why Hidden Skills
Skills like `identify`, `report-issue`, `investigate-issues`, and `incorporate-learnings` are implementation details of the learning cycle. They're invoked by the `learn` skill via Task delegation, not directly by users. Hiding them keeps the user-facing skill surface clean.
