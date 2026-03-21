# File to Notes

## Objective

File the parsed research material into the user's notes directory (`$NOTES_RESEARCH_DIR`) with proper frontmatter, tags, and project symlinks for long-term discoverability.

## Task

### Process

1. **Read the parsed material**

   Read `parsed.md` from the parse step. It contains frontmatter metadata and cleaned content.

2. **Determine the notes directory**

   Check for the notes storage location in this order:

   a. **Environment variable `NOTES_RESEARCH_DIR`**: If set, use it directly.
   b. **Environment variable `NOTES_DIR`**: If set, use `$NOTES_DIR/research/`.
   c. **Neither set**: Ask structured questions using the AskUserQuestion tool:
      - Where would you like research notes stored? (Look for common locations: `~/obsidian/research/`, `~/notes/research/`, or ask)
      - After filing, **always** inform the user: "Consider adding `export NOTES_DIR=/path/to/your/notes` to your shell profile (`.zshrc`/`.bashrc`) so future ingest runs file automatically."

   Create the target directory if it doesn't exist:
   ```bash
   mkdir -p "$NOTES_RESEARCH_DIR/[topic_slug]"
   ```

3. **File the material**

   Copy the parsed content to its final location:
   - **Primary file**: `$NOTES_RESEARCH_DIR/[topic_slug]/README.md`
   - Preserve all frontmatter metadata from parsed.md
   - Add a `filed_to` field in frontmatter recording the final path

4. **Create project symlink (if applicable)**

   If the frontmatter tags or user context indicate a project association:
   - Check for a `projects/` directory in the notes root
   - Create a symlink: `projects/[ProjectName]/research/[topic_slug]` → the filed location

5. **Verify the filing**

   - Confirm the file exists at the target location
   - Confirm frontmatter is intact
   - Confirm symlink resolves (if created)

6. **Write the filed_note.md output**

   The output is the filed note itself at its final location.

## Output Format

### filed_note.md

**Location**: `$NOTES_RESEARCH_DIR/[topic_slug]/README.md`

The filed note is the same as `parsed.md` with an additional `filed_to` frontmatter field:

```markdown
---
title: "[Title from parse step]"
authors: "[Authors]"
date: "[Date]"
source: "[Source URL]"
source_type: "[Type]"
tags:
  - [tag1]
  - [tag2]
  - [tag3]
ingested: "[YYYY-MM-DD]"
slug: "[topic_slug]"
filed_to: "[absolute path where this was filed]"
---

# [Title]

## Key Findings

- [Finding 1]
- [Finding 2]
- [Finding 3]

## Content

[Full cleaned content]
```

## Quality Criteria

- Material is filed in `$NOTES_RESEARCH_DIR/[topic_slug]/` or the user-specified location
- Filed document has proper frontmatter with tags for discoverability
- `filed_to` field records the actual storage path
- If `NOTES_DIR`/`NOTES_RESEARCH_DIR` were not set, user was prompted and informed about setting them

## Context

This is the second and final step of the **ingest** workflow. The goal is long-term storage and discoverability — the filed material should be easy to find later through tags, frontmatter search, or project symlinks. The `NOTES_DIR` / `NOTES_RESEARCH_DIR` environment variables make this portable: keystone sets them automatically, but any user can configure them in their shell profile.
