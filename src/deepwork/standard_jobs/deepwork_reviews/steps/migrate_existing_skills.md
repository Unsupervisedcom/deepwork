# Migrate Existing Review Skills

## Objective

Find any existing skills in the project (not from installed plugins) that perform review-like functions, convert each into a `.deepreview` rule, and remove the original skill — preserving a backup copy.

## Task

### 1. Identify candidate skills

Search the project for skill definitions that appear to be about code review, linting, quality checks, or similar review functions. Look in:

- `.claude/skills/` — Claude Code custom skills
- `.gemini/skills/` — Gemini CLI custom skills
- Any other skill directories the project may have

**Only target skills that belong to the project itself** — do not touch skills that come from installed plugins (e.g., the `deepwork` skill, `review` skill, or `configure_reviews` skill from the DeepWork plugin). Plugin-provided skills live in plugin directories (e.g., inside a `.claude-plugin/` parent or a cloned plugin repo) and should be left alone. When in doubt, check whether the skill directory is inside a plugin directory.

A skill is a candidate for migration if it:
- Reviews, lints, or checks code quality
- Enforces coding standards or conventions
- Validates documentation, configs, or other files
- Performs any kind of automated review that could be expressed as a `.deepreview` rule

If no candidate skills are found, report that in the output and finish — no migration needed.

### 2. For each candidate skill

#### a. Analyze the skill

Read the skill's `SKILL.md` (or equivalent definition file) thoroughly. Understand:
- What files does it review? (These become `match.include` patterns)
- What does it check for? (This becomes `review.instructions`)
- Does it review files individually or together? (This determines `strategy`)
- Does it need context beyond the changed files? (This determines `additional_context`)

#### b. Create the `.deepreview` rule

Translate the skill into a `.deepreview` rule. Prefer the top-level `.deepreview` file unless the original skill was explicitly scoped to a subdirectory (e.g., only reviewed files under `src/`). In that case, place the rule in a `.deepreview` file at that subdirectory root.

- Use a descriptive rule name derived from the skill name
- Write clear, complete review instructions that capture everything the skill was doing
- Choose the appropriate strategy (`individual`, `matches_together`, or `all_changed_files`)
- If the skill's review instructions exceed roughly 200 words, put them in a file under `.deepwork/review/` and reference it with `instructions: { file: ... }`

#### c. Back up the skill

Before deleting the skill, copy it to `.deepwork/tmp/migrated_skills/`. Preserve the full directory structure. For example, if deleting `.claude/skills/python_review/SKILL.md`, copy it to `.deepwork/tmp/migrated_skills/.claude/skills/python_review/SKILL.md`.

#### d. Delete the original skill

Remove the skill directory from its original location.

### 3. Validate

- Ensure all `.deepreview` rules are valid YAML with all required fields
- Ensure each backup exists in `.deepwork/tmp/migrated_skills/`
- Ensure the original skill directories have been removed

## Output

### deepreview_files

All `.deepreview` files that were created or modified during migration.

### migrated_skill_backups

All backup copies of deleted skills in `.deepwork/tmp/migrated_skills/`. If no skills were migrated, this output should contain a single file `.deepwork/tmp/migrated_skills/NONE.md` stating that no review-like skills were found.

## Quality Criteria

- Every identified review-like skill has a corresponding `.deepreview` rule
- Each rule's instructions faithfully capture the intent and coverage of the original skill
- Match patterns make sense for the file types the original skill targeted
- The strategy choice (individual vs matches_together) is appropriate for the review type
- All original skills have been backed up before deletion
- No plugin-provided skills were touched
