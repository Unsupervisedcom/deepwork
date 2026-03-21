# Choose Research Platforms

## Objective

Select which AI research platforms to use for deep research and create an execution plan for the gather step.

## Task

### Process

1. **Read the scope**

   Read `scope.md` from the prior step to understand the research question, type, and depth.

2. **Present platform options**

   Ask structured questions using the AskUserQuestion tool with multiSelect enabled to let the user choose one or more platforms:

   - **Local only** — Use Claude's built-in WebSearch and WebFetch tools. Fast, stays in session.
   - **Gemini Deep Research** — Comprehensive web crawling via Chrome. Best for broad topic coverage and discovering sources. Note: Gemini asks clarifying questions and shows a research plan before starting.
   - **ChatGPT Deep Research** — Thorough investigation with citations. Good for structured analysis and academic topics. Note: ChatGPT may ask clarifying questions before starting.
   - **Grok** — Real-time information and social media context via X/Twitter. Best for current events and public sentiment.
   - **Perplexity** — Research with inline citations and source quality indicators. Good for fact-checking and well-sourced summaries.

   **Parallel research**: If 2+ platforms are selected, research runs in parallel across all of them and results are cross-validated in the gather step.

3. **Verify browser availability**

   If any external platform is selected (not "Local only"):
   - Check that browser automation tools are available
   - If not available, warn the user and suggest falling back to "Local only"
   - Ask the user what browser tools they have if unclear

4. **Write platforms.md**

   Document the selection and create an execution plan for the gather step.

## Output Format

### platforms.md

**Location**: `research/[topic_slug]/platforms.md`

```markdown
# Platform Execution Plan: [Topic Name]

**Date**: [YYYY-MM-DD]
**Mode**: [single | parallel]

## Selected Platforms

### [Platform Name]
- **Role**: [What this platform contributes — e.g., "broad source discovery", "academic focus"]
- **Query approach**: [How to query this platform for best results]
- **Expected output**: [What kind of sources/findings to extract]

[Repeat for each selected platform]

## Execution Order

1. [First platform and why it goes first]
2. [Second platform, if applicable]

## Cross-Validation Plan

[If parallel mode: how to compare findings across platforms]
[If single: "N/A — single platform mode"]
```

## Quality Criteria

- At least one platform is selected
- If external platforms are selected, browser automation availability is confirmed
- Execution plan provides clear guidance for the gather step
- Platform selection is appropriate for the research type and topic
- Selection is confirmed by the user via AskUserQuestion

## Context

This step only runs in the **deep** workflow. The **quick** workflow skips platform selection entirely and uses local tools only. The platform execution plan directly guides the gather step's source collection strategy.

**Clarifying questions flow**: When using Gemini or ChatGPT for deep research, these platforms follow a two-phase approach: (1) they analyze the query and may ask clarifying questions, then (2) they present a research plan for approval. The gather step handles this interaction — document it in the execution plan so the gather step knows what to expect.
