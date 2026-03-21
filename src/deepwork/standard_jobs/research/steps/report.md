# Write Research Report

## Objective

Produce the final `README.md` research report with inline citations and key takeaways. Create a `bibliography.md` if external sources were cited. Create a project symlink if applicable.

## Task

### Process

1. **Read all inputs**

   - Read `research/[topic_slug]/scope.md` for metadata (type, depth, project, question)
   - Read `research/[topic_slug]/analysis.md` for synthesized findings and insights
   - Read `research/[topic_slug]/sources.md` for source details and URLs

2. **Write README.md**

   Structure the report as a polished, standalone document:

   - **Overview**: Research metadata (type, depth, project, date)
   - **Research Question**: Clear statement of what was investigated
   - **Findings**: Organized into logical sections, each citing sources with inline markdown links
   - **Key Takeaways**: 3-5 actionable conclusions drawn from the analysis
   - **Related**: Links to bibliography, project files, or external resources

   Write for the target audience (researcher and project stakeholders). Be concise — the analysis file has detailed reasoning; the README is the polished deliverable.

3. **Create bibliography.md (conditional)**

   Only create this file if external sources were cited:
   - Group sources by category (academic, industry reports, news, documentation, etc.)
   - Each entry: title, author/publisher, URL, access date, 1-2 sentence annotation
   - Consistent citation format throughout

4. **Create project symlink (if applicable)**

   If scope.md specifies a project tag:

   ```bash
   mkdir -p projects/[ProjectName]/research
   ln -s ../../../research/[topic_slug] projects/[ProjectName]/research/[topic_slug]
   ```

   Verify the symlink resolves correctly.

## Output Format

### README.md

**Location**: `research/[topic_slug]/README.md`

```markdown
# Research: [Topic Name]

## Overview

**Type**: [science | business | competitive | market | technical]
**Depth**: [quick | deep]
**Project**: [#ProjectTag or N/A]
**Date**: [YYYY-MM-DD]

## Research Question

[Clear statement of what this research aimed to answer]

## Findings

### [Finding Area 1]

[Findings with inline citations like [Source Title](url). Draw from the analysis
to present a clear narrative.]

### [Finding Area 2]

[Findings with inline citations]

[Organize into as many sections as needed to cover the research question]

## Key Takeaways

1. [Actionable takeaway grounded in the findings]
2. [Actionable takeaway]
3. [Actionable takeaway]
4. [Optional additional takeaway]
5. [Optional additional takeaway]

## Related

- [Bibliography](bibliography.md)
- [Links to related research, project files, or external resources]
```

### bibliography.md

**Location**: `research/[topic_slug]/bibliography.md` (only if sources were cited)

```markdown
# Bibliography: [Topic Name]

## Sources

### Academic

1. **[Title]** — [Author/Publisher]
   - URL: [link]
   - Accessed: [YYYY-MM-DD]
   - [1-2 sentence annotation describing relevance]

### Industry Reports

1. **[Title]** — [Author/Publisher]
   - URL: [link]
   - Accessed: [YYYY-MM-DD]
   - [Annotation]

### News & Analysis

[Same format, repeat for each category]
```

## Quality Criteria

- All findings cite sources with inline markdown links
- Key takeaways section has 3-5 actionable conclusions
- Report follows a clear structure: overview, question, findings, takeaways, related
- Bibliography exists if external sources were cited, with categorized annotated entries
- If a project was specified, symlink exists at `projects/[ProjectName]/research/[topic_slug]`
- Sources in bibliography are organized by category (academic, industry, news, etc.)
- Each bibliography entry has a 1-2 sentence annotation

## Context

This is the final step of the **research** workflow. The README.md is the primary deliverable — it should stand on its own as a useful document. The bibliography provides provenance for verification. The project symlink ensures the research is discoverable from the project directory.
