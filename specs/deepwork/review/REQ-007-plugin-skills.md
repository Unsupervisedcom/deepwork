# REQ-007: Plugin Skills and Documentation

## Overview

DeepWork Reviews is delivered to users via the Claude Code plugin. The plugin ships two skills (`review` and `configure_reviews`) and a usage reference (`README_REVIEWS.md`). The `review` skill runs the review pipeline and acts on findings. The `configure_reviews` skill helps users create and modify `.deepreview` config files. The reference documentation is symlinked into the plugin directory so it is available at runtime.

## Requirements

### REQ-007.1: Review Skill

1. The plugin MUST include a `review` skill at `plugins/claude/skills/review/SKILL.md`.
2. The skill's YAML frontmatter MUST contain a `name` field set to `"review"`.
3. The skill's YAML frontmatter MUST contain a `description` field.
4. The skill MUST instruct the agent to run `uvx deepwork review --instructions-for claude` to generate review tasks.
5. The skill MUST instruct the agent to launch the generated review tasks in parallel.
6. The skill MUST instruct the agent to automatically apply findings that are obviously correct with no downsides (e.g., typo fixes, unused import removal).
7. The skill MUST instruct the agent to use AskUserQuestion for findings that involve trade-offs or subjective judgment.
8. The skill MUST instruct the agent to re-run the review after making changes, repeating until no further actionable findings remain.
9. The skill MUST route configuration requests (creating or modifying `.deepreview` files) to the `configure_reviews` skill.

### REQ-007.2: Configure Reviews Skill

1. The plugin MUST include a `configure_reviews` skill at `plugins/claude/skills/configure_reviews/SKILL.md`.
2. The skill's YAML frontmatter MUST contain a `name` field set to `"configure_reviews"`.
3. The skill's YAML frontmatter MUST contain a `description` field.
4. The skill MUST instruct the agent to read `README_REVIEWS.md` for the full configuration reference.
5. The skill MUST instruct the agent to look at existing `.deepreview` files and reuse rules/instructions where possible.
6. The skill MUST instruct the agent to test changes by running `deepwork review --instructions-for claude` and verifying the new rule appears in the output.

### REQ-007.3: Reference Documentation

1. The plugin MUST include `README_REVIEWS.md` at `plugins/claude/README_REVIEWS.md`.
2. This file MUST be a symlink to `../../README_REVIEWS.md` (the project root copy).
3. The symlink target MUST exist and be readable.
4. The `README_REVIEWS.md` MUST document the `.deepreview` configuration format, all review strategies, instruction variants (inline and file reference), agent personas, and CLI usage.
5. The documentation MUST recommend `.deepwork/review/` as the location for reusable instruction files.

### REQ-007.4: Skill Directory Conventions

1. Each skill MUST be in its own directory under `plugins/claude/skills/`.
2. Each skill directory MUST contain a `SKILL.md` file.
3. The `name` field in the YAML frontmatter MUST match the skill's directory name.
