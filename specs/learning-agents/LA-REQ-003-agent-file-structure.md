# LA-REQ-003: Agent File Structure and Knowledge Base

## Overview

Each LearningAgent has a well-defined file structure under `.deepwork/learning-agents/` that stores its core knowledge, topic documentation, experience-based learnings, and per-agent learning cycle customization. A corresponding Claude Code agent file in `.claude/agents/` provides the runtime integration.

## Requirements

### LA-REQ-003.1: Agent Root Directory

Each LearningAgent MUST reside in `.deepwork/learning-agents/<agent-name>/` where `<agent-name>` uses dashes for word separation (e.g., `rails-activejob`, `data-pipeline`).

### LA-REQ-003.2: Folder Name as Source of Truth

The folder name under `.deepwork/learning-agents/` MUST be the authoritative source of truth for the agent's name. All references to the agent (in session tracking, Claude agent files, skills) MUST use this folder name.

### LA-REQ-003.3: Core Knowledge File -- Required

Each agent MUST have a `core-knowledge.md` file at the agent root directory. This file is REQUIRED for the agent to function.

### LA-REQ-003.4: Core Knowledge File -- Format

The `core-knowledge.md` file MUST be plain markdown with no YAML frontmatter. It MUST be written in second person ("You should...", "You are an expert on...") because it is injected as the agent's system instructions.

### LA-REQ-003.5: Core Knowledge File -- Content Structure

The `core-knowledge.md` file SHOULD be structured as:
1. Identity statement ("You are an expert on...")
2. Core concepts and terminology
3. Common patterns and best practices
4. Pitfalls to avoid
5. Decision frameworks

### LA-REQ-003.6: Topics Directory

Each agent MUST have a `topics/` subdirectory for conceptual reference material about areas within the agent's domain.

### LA-REQ-003.7: Topic File Format

Each topic file in `topics/` MUST be a markdown file with YAML frontmatter containing:
- `name` (REQUIRED): Human-readable topic name
- `keywords` (OPTIONAL): Array of topic-specific search terms
- `last_updated` (OPTIONAL): Date in YYYY-MM-DD format

The body MUST contain detailed documentation about the topic area.

### LA-REQ-003.8: Topic File Naming

Topic filenames MUST use dashes and be descriptively named (e.g., `retry-handling.md`). The `.md` extension is REQUIRED.

### LA-REQ-003.9: Learnings Directory

Each agent MUST have a `learnings/` subdirectory for experience-based incident post-mortems.

### LA-REQ-003.10: Learning File Format

Each learning file in `learnings/` MUST be a markdown file with YAML frontmatter containing:
- `name` (REQUIRED): Descriptive name of the learning
- `last_updated` (OPTIONAL): Date in YYYY-MM-DD format
- `summarized_result` (OPTIONAL but RECOMMENDED): 1-3 sentence summary of the key takeaway

The body SHOULD contain sections: Context, Investigation, Resolution, and Key Takeaway.

### LA-REQ-003.11: Learning File Naming

Learning filenames MUST use dashes and be descriptively named. The `.md` extension is REQUIRED.

### LA-REQ-003.12: Topics vs Learnings Distinction

Topics MUST document conceptual reference material (how things work -- patterns, APIs, conventions, decision frameworks). Learnings MUST document incident post-mortems of specific mistakes (what went wrong and why -- debugging narratives where the context matters for understanding the lesson).

### LA-REQ-003.13: Additional Learning Guidelines Directory

Each agent MUST have an `additional_learning_guidelines/` subdirectory containing:
- `README.md` -- explaining each file's purpose
- `issue_identification.md` -- extra guidance for the identify step
- `issue_investigation.md` -- extra guidance for the investigate step
- `learning_from_issues.md` -- extra guidance for the incorporate step

### LA-REQ-003.14: Additional Learning Guidelines -- Dynamic Inclusion

Each additional learning guideline file MUST be dynamically included (via `!` backtick syntax) in the corresponding learning cycle skill's Context section. Empty files MUST result in no additional guidance (default behavior).

### LA-REQ-003.15: Claude Code Agent File

Each LearningAgent MUST have a corresponding `.claude/agents/<agent-name>.md` file with:
- YAML frontmatter containing `name` (human-readable display name) and `description` (concise invocation description, 2-3 sentences max)
- Dynamic context injection for `core-knowledge.md`
- A Topics section with dynamic listing of available topic files
- A Learnings section referencing the learnings directory

### LA-REQ-003.16: Agent Name Consistency

The Claude Code agent filename (`.claude/agents/<agent-name>.md`) MUST match the LearningAgent folder name under `.deepwork/learning-agents/`.

### LA-REQ-003.17: Discovery Description Location

The agent's discovery description (used by Claude Code to decide whether to invoke this agent) MUST reside in the `.claude/agents/<agent-name>.md` frontmatter `description` field, NOT in the `core-knowledge.md` file.

### LA-REQ-003.18: Knowledge Injection at Invocation Time

Both topics and learnings MUST be injected into the agent's prompt at invocation time via the Claude Code agent file. Topics and learnings MUST NOT be baked into the `core-knowledge.md` file.
