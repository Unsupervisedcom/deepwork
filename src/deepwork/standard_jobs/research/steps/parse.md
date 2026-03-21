# Parse External Material

## Objective

Parse and clean external research material (markdown copies of deep research, research papers, web articles, etc.), extract metadata, and produce a normalized markdown document ready for filing into the notes system.

## Task

### Process

1. **Accept the material**

   The user provides research material in one of these forms:
   - **File path**: A local markdown file, PDF, or text file
   - **URL**: A web page to fetch and convert
   - **Pasted content**: Inline text provided directly

   Ask structured questions using the AskUserQuestion tool if the input format is unclear:
   - What is the source material? (file path, URL, or pasted content)
   - What topic slug should be used for organization?

2. **Retrieve the content**

   Based on the input type:
   - **File path**: Read the file directly
   - **URL**: Use WebFetch to retrieve the page content
   - **Pasted content**: Use the provided text as-is

3. **Extract metadata**

   Parse the material to extract:
   - **Title**: The research title or article headline
   - **Authors**: Author names if available
   - **Date**: Publication date or access date
   - **Source URL**: Original URL or "local file" if from a file
   - **Source type**: What kind of material (deep research output, academic paper, blog post, news article, documentation)
   - **Tags**: 3-5 descriptive tags for the content (e.g., `#machine-learning`, `#attention`, `#benchmarks`)

4. **Clean and normalize the content**

   - Remove HTML artifacts, broken formatting, navigation elements, ads
   - Fix broken links where possible
   - Preserve code blocks, tables, and structured data

   **CRITICAL: Preserve original formatting.** Do NOT reformat, rephrase, or restructure the author's content. Specifically:
   - Keep the original heading hierarchy — do not renumber or re-level headings
   - Keep special characters and notation (tree diagrams like `├──`/`└──`, arrows `→`, emoji markers, `§` prefixes) exactly as they appear
   - Keep the original structure of lists, tables, and code blocks
   - If the material contains multiple reports or sections, preserve ALL of them in full

   **CRITICAL: Never truncate or summarize away content.** The full original text must appear in the output. Do not replace sections with "see above" or "remaining content follows the same pattern." If the material is very large, that is fine — write the full content.

5. **Extract key findings**

   Write a summary section (3-5 bullet points) capturing the most important findings or contributions from the material. This helps with future discoverability.

6. **Consider companion data files**

   If the material contains structured data (catalogs, job lists, inventories, specifications), ask the user whether to extract it into a companion file (e.g., `jobs.yaml`, `data.csv`) alongside the main parsed.md. Structured data in YAML/JSON is easier to query with tools like `yq`/`jq` than embedded markdown.

7. **Write parsed.md**

   Create the output in a temporary location (`research/[topic_slug]/parsed.md`) with frontmatter metadata.

## Output Format

### parsed.md

**Location**: `research/[topic_slug]/parsed.md`

```markdown
---
title: "[Extracted or provided title]"
authors: "[Author names, comma-separated, or 'Unknown']"
date: "[YYYY-MM-DD publication or access date]"
source: "[URL or 'local file: /path/to/file']"
source_type: "[deep_research | academic_paper | blog_post | news_article | documentation | other]"
tags:
  - [tag1]
  - [tag2]
  - [tag3]
ingested: "[YYYY-MM-DD]"
slug: "[topic_slug]"
---

# [Title]

## Key Findings

- [Most important finding or contribution]
- [Second key finding]
- [Third key finding]
- [Optional: additional findings]

## Content

[Cleaned and normalized content from the original material.
All formatting preserved, HTML artifacts removed, headings normalized.]
```

**Concrete example**:

```markdown
---
title: "Attention Is All You Need — Revisited"
authors: "Vaswani, A., Shazeer, N., et al."
date: "2024-06-15"
source: "https://arxiv.org/abs/2406.12345"
source_type: "academic_paper"
tags:
  - machine-learning
  - transformers
  - attention-mechanisms
ingested: "2026-03-20"
slug: "attention-revisited"
---

# Attention Is All You Need — Revisited

## Key Findings

- Multi-head attention scales quadratically with sequence length, limiting context windows
- Linear attention variants achieve 90-95% of softmax quality at O(n) complexity
- Flash Attention 3 reduces memory overhead by 4x through kernel-level optimization

## Content

[Full cleaned paper/article content follows...]
```

## Quality Criteria

- Frontmatter includes title, authors (if available), date, source URL or origin, and tags
- Content is well-formatted markdown with no HTML artifacts or broken formatting
- A summary section extracts the key findings or contributions from the material
- Tags are descriptive and useful for future search
- Original content is preserved in full — no truncation, no summarization, no "see above" shortcuts
- Original formatting is preserved — special characters, tree diagrams, notation kept exactly as authored
- If structured data was extracted to a companion file, it is queryable and complete

## Context

This is the first step of the **ingest** workflow. The parsed output feeds into the **file** step, which places it in the user's notes directory with proper organization. Good metadata extraction here makes the material discoverable later. The same step is also invoked as a nested workflow by the **reproduce** workflow.
