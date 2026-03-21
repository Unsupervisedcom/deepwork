# Gather Sources (Quick)

## Objective

Rapidly collect at least 3 relevant sources using only local tools (WebSearch and WebFetch) to address the research question defined in the scope.

## Task

### Process

1. **Read the scope**

   Read `research/[topic_slug]/scope.md` for the research question, sub-questions, type, and search strategy.

2. **Formulate search queries**

   Derive 3-5 targeted search queries from the research question and sub-questions. Prioritize queries that are likely to surface high-value sources quickly:
   - Lead with the most specific query (main research question)
   - Follow with queries targeting individual sub-questions
   - Include a query for recent developments or reviews

3. **Execute local search**

   For each query:
   - Use WebSearch to find relevant pages
   - Use WebFetch to extract content from the most promising URLs
   - Prioritize official documentation, reputable news, and established publications
   - Skip sources that are paywalled, low-quality, or tangential

4. **Document sources**

   For each source, record:
   - Title and URL
   - Key findings relevant to the research question
   - Source type and basic reliability assessment

5. **Write sources.md**

   This is a streamlined format — less detail than the deep gather but enough for the summarize step.

## Output Format

### sources.md

**Location**: `research/[topic_slug]/sources.md`

```markdown
# Sources: [Topic Name]

**Depth**: quick
**Platforms Used**: local (WebSearch/WebFetch)
**Sources gathered**: [count]
**Date**: [YYYY-MM-DD]

---

## Source 1: [Title]

- **URL**: [link]
- **Author/Publisher**: [name or "Unknown"]
- **Date**: [published or accessed date]
- **Type**: [academic | news | blog | docs | report | product | forum]
- **Reliability**: [high | medium | low]

### Key Findings

- [Finding relevant to the research question]
- [Another finding]

---

[Repeat for each source, minimum 3]

## Coverage Notes

**Addressed sub-questions**: [which sub-questions from scope.md have coverage]
**Gaps**: [any sub-questions with no sources, if applicable]
```

## Quality Criteria

- At least 3 sources gathered with URLs and key findings
- Sources are directly relevant to the research question in scope.md
- Each source has a URL, findings, and reliability assessment
- Coverage notes indicate which sub-questions are addressed

## Context

This step runs only in the **quick** workflow. Unlike the research workflow's gather step which uses multi-platform research and requires 8+ sources, this step uses only local tools (WebSearch/WebFetch) for speed. The output feeds directly into the summarize step, which combines synthesis and reporting into one step. Prioritize relevance and quality over quantity.
