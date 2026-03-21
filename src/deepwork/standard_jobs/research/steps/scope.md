# Define Research Scope

## Objective

Define the research question, classify the research type and depth level, and detect whether this research is associated with an existing project. Output a `scope.md` file that guides all subsequent steps in both the **research** and **quick** workflows.

## Task

### Process

1. **Gather inputs using structured questions**

   Ask structured questions using the AskUserQuestion tool to collect any inputs not already provided:

   - **Topic**: The research question or subject. Get a clear, specific statement.
   - **Type**: One of: science, business, competitive, market, technical.
   - **Depth**: One of:
     - **Quick** — Local web search summary, 3+ sources, concise output
     - **Standard** — Multi-source web research, 5+ diverse sources, synthesized analysis
     - **Deep** — Thorough investigation, 8+ sources, multi-platform with browser automation
   - **Project** (optional): An associated project tag (e.g., `#Catalyst`, `#Meze`).

2. **Detect project association**

   Check if the topic relates to a known project:
   - Look for `projects/README.md` or `PROJECTS.yaml` for active project tags
   - If the user provided a project tag, validate it exists
   - If no tag provided, check if the topic keywords match a project description
   - If a match is found, confirm with the user

3. **Generate the topic slug**

   Create a filesystem-safe slug from the topic:
   - Lowercase, hyphens for spaces, no special characters
   - Keep it short but descriptive (e.g., `nix-remote-builders`, `transformer-attention`)

4. **Formulate sub-questions**

   Break the main research question into 3-5 sub-questions that collectively cover the topic. These guide source gathering and synthesis.

5. **Draft search strategy**

   Based on the type and depth, outline what kinds of sources to seek:

   | Research Type | Priority Sources |
   |---|---|
   | science | Academic papers, preprints, review articles, research institutions |
   | business | Industry reports, company filings, business news, analyst coverage |
   | competitive | Competitor websites, product reviews, pricing, feature comparisons |
   | market | Market size reports, consumer surveys, trend analysis, demographic data |
   | technical | Official docs, benchmarks, architecture posts, GitHub repos, RFCs |

6. **Create the research directory and scope file**

   - Create `research/[topic_slug]/` directory
   - Write `research/[topic_slug]/scope.md`

## Output Format

### scope.md

**Location**: `research/[topic_slug]/scope.md`

```markdown
# Research Scope: [Topic Name]

**Slug**: [topic_slug]
**Type**: [science | business | competitive | market | technical]
**Depth**: [quick | standard | deep]
**Project**: [#ProjectTag or N/A]
**Date**: [YYYY-MM-DD]

## Research Question

[Clear, specific statement of what this research aims to answer]

## Sub-Questions

1. [Specific sub-question that addresses one facet of the main question]
2. [Another sub-question]
3. [Another sub-question]
4. [Optional additional sub-question]
5. [Optional additional sub-question]

## Search Strategy

**Source types to prioritize**: [based on research type]

**Depth guidance**:
- Minimum sources: [3 for quick, 5 for standard, 8 for deep]
- Source diversity: [what kinds of sources to include]
- Platform approach: [local only for quick, user-selected for deep]

## Project Context

[If associated with a project: why this research matters to the project's goals.
If N/A: "No project association"]
```

**Concrete example**:

```markdown
# Research Scope: Transformer Attention Mechanisms

**Slug**: transformer-attention
**Type**: science
**Depth**: deep
**Project**: #LLMResearch
**Date**: 2026-03-20

## Research Question

What are the current state-of-the-art alternatives to standard multi-head attention in transformer architectures, and what are their trade-offs?

## Sub-Questions

1. What attention variants have been proposed since the original transformer paper?
2. How do linear attention mechanisms compare to softmax attention on benchmarks?
3. What are the memory and compute scaling characteristics of each variant?
4. Which attention mechanisms are being adopted in production systems?

## Search Strategy

**Source types to prioritize**: Academic papers (arXiv, conference proceedings), benchmark results, engineering blog posts

**Depth guidance**:
- Minimum sources: 8
- Source diversity: academic papers, benchmark comparisons, engineering blogs, documentation
- Platform approach: Gemini Deep Research + local WebSearch

## Project Context

Feeds into #LLMResearch architecture decision. Results inform the attention mechanism selection.
```

## Quality Criteria

- Topic is clearly defined as a specific, answerable research question
- Type is one of the five valid categories
- Depth level is set and appropriate for the question
- Topic slug is filesystem-safe and descriptive
- Sub-questions collectively cover the main question (3-5 questions)
- Search strategy is tailored to the type and depth
- Project association is validated if provided

## Context

This is the foundation step for both **research** and **quick** workflows. The scope file guides every downstream step — gather uses it to know what to search for, synthesize uses it to know what question to answer, and report uses it to structure the output. A well-defined scope prevents wasted effort in later steps.
