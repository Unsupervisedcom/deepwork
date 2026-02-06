# Research Report Job Best Practices

Reference guide for designing DeepWork jobs that produce research reports, analytical documents, or similar investigative deliverables. Use this when defining jobs via the `define` step.

## The General Pattern

Most report-authoring jobs follow a five-phase structure. Not every job needs all five as separate steps, and some phases combine naturally, but understanding the full arc helps you design a job that doesn't skip critical work.

### 1. Connect

**Purpose**: Verify that the tools and data sources the job will rely on are actually accessible before any real work begins.

This step is about validating prerequisites, not doing research. Common activities:

- **Database connectivity**: Run a trivial query (`SELECT 1`, `SHOW TABLES`) to confirm credentials work and the schema is reachable.
- **Web search tools**: Confirm web search and browsing tools are enabled. If the job needs to read specific sites, verify they don't require login. If they do, get the user to authenticate (e.g., via Claude in Chrome) before proceeding.
- **API access**: Test API keys or tokens against a lightweight endpoint.
- **File access**: Confirm that input files, dashboards, or shared drives are readable.

**Why a separate step?** A failed connection discovered midway through analysis wastes all prior work. Catching it upfront is cheap. That said, for simple jobs where the data source is obvious and reliable (e.g., "search the web for X"), this can be folded into the Align step as a quick check rather than standing alone.

**Outputs**: A brief connectivity report or checklist confirming each source is accessible, plus any credentials or configuration notes for later steps.

### 2. Align

**Purpose**: Build enough understanding of the domain and the user's intent to scope the analysis correctly.

This is a cyclical step: do light research, then ask clarifying questions, then refine understanding, repeat. It ends when both the agent and user agree on what "done" looks like.

**The cycle**:

1. **Light grounding research** - Just enough to ask smart questions. Not deep analysis.
2. **Clarify with the user** - Surface ambiguities and propose scope boundaries.
3. **Repeat** until there's shared understanding.

**Example - Private data (SQL-centric)**:
- Run broad queries to get the lay of the land: total record counts, key column names, date ranges, apparent segmentation columns (e.g., `division`, `region`).
- Then ask the user: "I see 45,000 customer records across 3 divisions. Should we scope to a particular division? I'm defining churn as customers with no activity in 90 days - does that match your definition?"

**Example - Public data (web-centric)**:
- Do broad searches to see what's out there. Notice the shape of results: are they news articles, academic papers, industry reports? What subtopics keep appearing?
- Then ask the user: "Results split between fast-fashion trends and haute couture analysis. Which direction? Also, should we focus on the current season or look at multi-year trends?"

**Outputs**: A scoping document that captures the agreed-upon research questions, data sources, definitions, exclusions, and success criteria. This becomes the north star for the Analyze step.

### 3. Analyze

**Purpose**: The core research cycle. Query, record, synthesize, and deepen iteratively.

This is where most of the work happens. The key discipline is maintaining structured working files so that nothing gets lost and the narrative builds progressively.

**Working files to maintain**:

| File | Purpose |
|------|---------|
| Query log | Every query/search with its results. What did you ask, what came back. Keeps work auditable and reproducible. |
| Questions & Answers | Running list of research questions. As you find answers, record them. As answers suggest new questions, add those. This drives the iterative deepening. |
| Draft report | The evolving narrative. Updated as new findings emerge. Forces you to synthesize as you go rather than dumping data at the end. |

**The iterative deepening pattern**:

Analysis should deepen in layers, not stay shallow across many topics. Each answer should prompt "why?" or "what drives that?" questions:

- **Layer 1**: Top-level facts. "What was our AWS spend last month?" -> $10k. "How does that compare to prior month?" -> Up $1k.
- **Layer 2**: Decomposition. "What services drove the spend?" -> $8k EC2, $1k S3, $1k other. "Where was the increase?" -> All in EC2.
- **Layer 3**: Root causes. "Is our EC2 fleet well-utilized?" -> Many instances with attribute X are underutilized. "Are specific workloads driving the increase?" -> Yes, instances tagged `daily_sync_*` are up ~$2k.
- **Layer 4+**: Continue until you hit actionable findings or diminishing returns.

**When to stop deepening**: When additional queries aren't changing the narrative, or when you've answered the questions from the Align step to a sufficient depth. But make sure that any questions that a reasonable business person is likely to ask when looking at your output are answered.

**Outputs**: The working files above (query log, Q&A tracker, draft report), organized in the dataroom alongside the final output.

### 4. Review (Not a Separate Step)

Reviews are not a standalone phase but checkpoints woven into all the steps, especially the Analyze step. Use DeepWork's `reviews` mechanism in `job.yml` to define quality gates.

**Reviews to consider for the Analyze phase**:

- **Query completeness**: Are the key research questions from the scoping document all addressed? Are queries recorded with their results?
- **Draft coherence**: Does the draft report tell a logical story? Are sections connected rather than isolated findings?
- **Depth adequacy**: Has the analysis gone deep enough on the important threads? Are there obvious follow-up questions left unasked?
- **Citation integrity**: Are claims in the draft backed by specific queries/sources from the query log?

**Reviews to consider for the Present phase** (see below):

- **Visual quality**: Charts render correctly, no overlapping text, readable at intended size.
- **Content accuracy**: Citations preserved from draft, numbers match source data, arguments are logically sound.
- **Audience fit**: Language, detail level, and framing match the intended audience (executives vs. engineers vs. clients).
- **Format compliance**: Output matches the requested format (PDF renders correctly, HTML is responsive, slides have consistent styling).

### 5. Present

**Purpose**: Transform the draft into a polished final deliverable.

The draft report from the Analyze step has the right content but may not be presentation-ready. This step focuses on the output experience.

**Common activities**:

- **Visualizations**: Generate charts, tables, or diagrams from the data. Fetch relevant images. Create infographics for key findings.
- **Formatting**: Convert to the final output format (PDF, HTML, slides, etc.). Apply styling and layout.
- **Narrative polish**: Tighten prose, add executive summary, ensure the document flows well for someone reading it cold.
- **Supporting materials**: Assemble appendices, data tables, methodology notes.

**This step often requires multiple review cycles.** Visual outputs have failure modes that text-only drafts don't: overlapping labels, truncated legends, broken page breaks, images that don't load. Build in quality gates for visual review.

**Outputs**: The final deliverable in its target format, plus any supporting materials.

## Translating This Into a Job Definition

### Step Structure Options

**Minimal (3 steps)** - For straightforward reports with known data sources:
1. `scope` - Combines Connect + Align. Verify access, clarify requirements.
2. `research` - The Analyze phase with built-in review gates.
3. `report` - The Present phase with visual/format review gates.

**Standard (4 steps)** - For most research reports:
1. `connect` - Verify data source access.
2. `scope` - Align on research questions and definitions.
3. `analyze` - Core research with iterative deepening.
4. `present` - Final deliverable production.

**Comprehensive (5+ steps)** - For complex, multi-source reports:
1. `connect` - Verify all data source access.
2. `scope` - Align on research questions.
3. `gather` - Collect raw data across all sources (query log output).
4. `analyze` - Synthesize findings, build narrative (draft report output).
5. `present` - Polish and format final deliverable.

### Output Organization

Follow the dataroom pattern from the define step guidelines:

```
operations/reports/2026-01/spending_analysis.md              # Final report
operations/reports/2026-01/spending_analysis_dataroom/        # Supporting materials
    query_log.md                                              # All queries and results
    questions_and_answers.md                                  # Research Q&A tracker
    raw_data/                                                 # Extracted data files
    charts/                                                   # Generated visualizations
    draft.md                                                  # Working draft (for audit trail)
```

### Quality Gate Design

Research reports benefit from **split reviews** that evaluate content and presentation separately:

```yaml
reviews:
  # Content review - is the analysis sound?
  - run_each: final_report.md
    quality_criteria:
      "Claims Cited": "Is every factual claim backed by a specific source or query from the dataroom?"
      "Questions Answered": "Are all research questions from the scoping document addressed?"
      "Depth": "Does the analysis go beyond surface-level observations to root causes or actionable insights?"

  # Presentation review - is the output polished?
  - run_each: final_report.md
    quality_criteria:
      "Readable Flow": "Does the document flow logically for someone reading it without prior context?"
      "Audience Fit": "Is the language and detail level appropriate for the intended audience?"
      "Visual Quality": "Do all charts, tables, and figures render correctly and add value?"
```

### Capability Considerations

Research jobs frequently need specialized tools. During the `define` step, ask about:

- **Database access**: What databases? What client tools or connection strings?
- **Web browsing**: Will sites require authentication? Is Claude in Chrome available?
- **File generation**: Does the final output need PDF/HTML rendering? What tools are available?
- **Data visualization**: What charting libraries or tools can the agent use?

## Anti-Patterns to Avoid

**Shallow breadth over deep analysis**: Covering 20 topics superficially is less valuable than covering 5 topics with layered depth. Design the Analyze step to encourage iterative deepening, not checklist completion.

**Skipping the scoping step**: Jumping straight into analysis without aligning on definitions and scope almost always leads to rework. "Analyze our churn" means very different things depending on how churn is defined.

**Query results only in memory**: If queries and their results aren't written to working files, they can't be reviewed, cited, or audited. The query log is not optional.

**Draft report written at the end**: The draft should evolve throughout the Analyze step, not be assembled from notes after all research is complete. Writing the narrative as you go reveals gaps in the analysis early.

**Conflating analysis with presentation**: Trying to produce a polished PDF while still figuring out the findings leads to wasted formatting work. Get the content right first, then make it pretty.
