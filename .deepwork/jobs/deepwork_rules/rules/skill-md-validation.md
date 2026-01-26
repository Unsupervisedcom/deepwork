---
name: SKILL.md Validation
trigger: "**/SKILL.md"
compare_to: base
---
A SKILL.md file has been created or modified. Please validate that it follows the required format:

## Required Structure

The file MUST have valid YAML frontmatter at the start, enclosed between `---` markers:

```markdown
---
name: my-skill-name
description: A description of what this skill does
---

# Rest of the skill documentation...
```

## Validation Checklist

1. **YAML Frontmatter**: Verify the file starts with `---` followed by valid YAML and ends with `---`

2. **`name` field** (required):
   - Must be present in the frontmatter
   - Must contain only lowercase letters, numbers, and hyphens (`a-z`, `0-9`, `-`)
   - Must be 64 characters or fewer
   - Example valid names: `my-skill`, `code-review-2`, `lint`
   - Example invalid names: `My Skill` (uppercase/spaces), `skill_name` (underscores), `SKILL` (uppercase)

3. **`description` field** (required):
   - Must be present in the frontmatter
   - Must be 1024 characters or fewer
   - Should clearly describe what the skill does

## What to Check

For the modified file: {trigger_files}

1. Parse the YAML frontmatter and verify it is valid YAML
2. Check that `name` exists and matches the pattern `^[a-z0-9-]+$` with max length 64
3. Check that `description` exists and is at most 1024 characters
4. Report any validation errors to the user

If the file does not pass validation, help the user fix the issues.
