# Gather Sources (Deep)

## Objective

Collect at least 8 diverse sources from the selected research platforms, extracting key findings, URLs, and reliability assessments for each.

## Task

### Process

1. **Read inputs**

   - Read `scope.md` for the research question, sub-questions, type, and search strategy
   - Read `platforms.md` for the platform execution plan and query approach

2. **Execute platform-specific gathering**

   Follow the execution plan from platforms.md. For each platform:

   **Local (WebSearch/WebFetch)**:
   - Formulate 5-8 search queries derived from sub-questions
   - Use WebSearch to find relevant pages
   - Use WebFetch to extract content from promising URLs
   - Record URL, title, key findings, and source type

   **Gemini Deep Research** (browser automation):
   - Navigate to Gemini and activate Deep Research mode
   - Enter the research question from scope.md
   - Answer any clarifying questions Gemini asks
   - Review and approve the research plan
   - Wait for completion and extract findings with source links
   - Save raw output as `sources_gemini.md`

   **ChatGPT Deep Research** (browser automation):
   - Open ChatGPT and use research/browse mode
   - Enter the research question
   - Answer clarifications and approve the plan
   - Extract findings with citations
   - Save raw output as `sources_chatgpt.md`

   **Grok** (browser automation):
   - Open Grok and enter the research question
   - Extract findings, especially real-time and social context
   - Save raw output as `sources_grok.md`

   **Perplexity** (browser automation):
   - Open Perplexity and enter the research question
   - Extract findings with numbered inline citations
   - Save raw output as `sources_perplexity.md`

   **Parallel mode (2+ platforms)**:
   - Open each platform in separate browser tabs
   - Enter the same research question in each
   - Allow all platforms to research simultaneously
   - Save platform-specific outputs, then consolidate

3. **Consolidate and deduplicate**

   After gathering from all platforms:
   - Merge findings from all platform-specific source files
   - Deduplicate sources (same URL from multiple platforms)
   - Note which platform found which source
   - Highlight areas of agreement (high confidence) and disagreement (needs verification)

4. **Assess source reliability**

   For each source, assign a reliability level:
   - **high**: Peer-reviewed, official documentation, established news outlets
   - **medium**: Industry blogs, well-known tech publications, company pages
   - **low**: Forums, social media, unverified claims

5. **Build coverage matrix**

   Map which sources address which sub-questions to identify coverage gaps.

6. **Write sources.md**

## Output Format

### sources.md

**Location**: `research/[topic_slug]/sources.md`

```markdown
# Sources: [Topic Name]

**Depth**: deep
**Platforms Used**: [comma-separated list]
**Sources gathered**: [count]
**Date**: [YYYY-MM-DD]

## Cross-Platform Summary

**Platform agreement**: [Topics where platforms converge]
**Unique findings**: [Notable discoveries from individual platforms]
**Conflicts**: [Areas of disagreement between platforms]

---

## Source 1: [Title]

- **URL**: [link]
- **Found by**: [platform(s)]
- **Author/Publisher**: [name or "Unknown"]
- **Date**: [published date or "Accessed YYYY-MM-DD"]
- **Type**: [academic | news | blog | docs | report | product | forum]
- **Reliability**: [high | medium | low]

### Key Findings

- [Finding relevant to the research question]
- [Another finding]

### Relevant Sub-Questions

- Addresses: [sub-question numbers from scope.md, e.g., 1, 3, 4]

---

[Repeat for each source, minimum 8]

## Coverage Matrix

| Sub-Question | Sources Addressing It |
|---|---|
| 1. [sub-question text] | Source 1, Source 3, Source 7 |
| 2. [sub-question text] | Source 2, Source 4 |
| ... | ... |

## Gaps

[Sub-questions with insufficient coverage, if any]
```

## Quality Criteria

- At least 8 sources gathered from diverse types (academic, news, docs, reports)
- Each source has a URL, key excerpt or finding, and reliability assessment
- Sources come from the platforms specified in platforms.md
- All sub-questions from scope.md are addressed by at least one source
- Coverage matrix shows which sub-questions each source addresses
- Cross-platform summary is present if multiple platforms were used
- For external platforms, raw output is preserved in platform-specific files

## Context

This is the primary data collection step of the **research** workflow. Source quality and diversity directly determine the quality of synthesis and final report. Prioritize breadth across sub-questions over depth on any single point — gaps can be noted for the synthesis step. Document enough detail that the synthesize step can work without re-visiting sources.
