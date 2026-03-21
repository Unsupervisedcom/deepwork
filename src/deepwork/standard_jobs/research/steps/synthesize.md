# Synthesize Findings

## Objective

Analyze the gathered sources to produce a structured analysis that directly answers the research question. Synthesize across sources rather than summarizing each individually.

## Task

### Process

1. **Read inputs**

   - Read `research/[topic_slug]/scope.md` for the research question and sub-questions
   - Read `research/[topic_slug]/sources.md` for all gathered findings and the coverage matrix

2. **Map findings to sub-questions**

   For each sub-question from the scope:
   - Use the coverage matrix to identify which sources address it
   - Note where sources agree, disagree, or are silent
   - Assess evidence strength:
     - **strong**: Multiple high-reliability sources agree
     - **moderate**: Some support but gaps or contradictions exist
     - **weak**: Single source or low reliability only

3. **Identify cross-cutting themes**

   Look for patterns that span multiple sub-questions and sources:
   - Recurring trends or concepts
   - Emerging consensus or paradigm shifts
   - Unexpected connections between sub-questions
   - Findings not anticipated in the original scope

4. **Document contradictions and gaps**

   - Where do sources disagree? What might explain the disagreement?
   - Which sub-questions have weak evidence coverage?
   - What important questions remain unanswered?

5. **Formulate key insights**

   Distill 3-5 key insights that:
   - Directly address the main research question
   - Are supported by evidence from multiple sources
   - Are actionable or decision-relevant
   - Include confidence levels based on evidence strength

6. **Draft preliminary takeaways**

   Based on the analysis, draft actionable recommendations:
   - What should the reader do with this information?
   - If project-associated, how does this affect the project?
   - What further research might be needed?

7. **Write analysis.md**

## Output Format

### analysis.md

**Location**: `research/[topic_slug]/analysis.md`

```markdown
# Analysis: [Topic Name]

**Date**: [YYYY-MM-DD]

## Research Question

[Restated from scope.md]

## Findings by Sub-Question

### 1. [Sub-Question from scope.md]

**Evidence strength**: [strong | moderate | weak]

[Synthesized answer drawing from multiple sources. Cite sources inline, e.g., "According to [Source Title](url), ..."]

### 2. [Sub-Question]

**Evidence strength**: [strong | moderate | weak]

[Synthesized answer]

[Repeat for all sub-questions]

## Cross-Cutting Themes

### [Theme 1: descriptive name]

[Description of the theme with references to which sub-questions and sources it spans]

### [Theme 2: descriptive name]

[Description]

## Contradictions and Gaps

- **[Topic]**: [Source A](url) argues X, while [Source B](url) argues Y. Possible explanation: [hypothesis]
- **Gap**: [Area where insufficient evidence was found]

## Key Insights

1. **[Insight statement]** (Confidence: [high | medium | low])
   [Explanation with source references]

2. **[Insight statement]** (Confidence: [high | medium | low])
   [Explanation]

3. **[Insight statement]** (Confidence: [high | medium | low])
   [Explanation]

[3-5 insights total]

## Preliminary Takeaways

- [Actionable recommendation based on the evidence]
- [Another recommendation]
- [Further research suggestion if applicable]
```

## Quality Criteria

- Directly addresses the research question and all sub-questions from scope.md
- Synthesizes across multiple sources rather than summarizing each individually
- Contradictions, gaps, and areas of disagreement are explicitly noted
- Key insights have confidence levels grounded in evidence strength
- All claims cite specific sources with inline markdown links
- Preliminary takeaways are actionable

## Context

This is the analytical core of the **research** workflow. The gather step collected raw material; this step transforms it into structured understanding. The report step that follows will present these insights to the reader, so the analysis must be rigorous enough to support clear, well-evidenced conclusions.
