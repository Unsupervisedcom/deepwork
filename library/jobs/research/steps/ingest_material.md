# Ingest Research Material

## Objective

Import external research material by running the **ingest** workflow as a nested workflow. This step is the entry point for the **reproduce** workflow — it ensures the research material is properly parsed, cleaned, and filed before reproducibility analysis begins.

## Task

### Process

1. **Collect material information**

   The user provides:
   - **material**: A file path, URL, or pasted content to ingest
   - **topic_slug**: A short slug for organizing the material

   If not already provided, ask structured questions using the AskUserQuestion tool:
   - What research material do you want to analyze for reproduction? (file path, URL, or paste it)
   - What short slug should we use? (e.g., `gpt4-scaling-laws`, `attention-benchmarks`)

2. **Start the nested ingest workflow**

   Use the DeepWork MCP tools to start the `ingest` workflow as a nested workflow:

   ```
   Call start_workflow with:
     job_name: "research"
     workflow_name: "ingest"
     goal: "Ingest [material description] for reproducibility analysis"
     session_id: [your session ID]
   ```

   This pushes the `ingest` workflow onto the stack. Follow its steps:
   - **parse**: Will parse and clean the material, extract metadata
   - **file**: Will file it into `$NOTES_RESEARCH_DIR`

   Complete both steps of the nested workflow by following the instructions returned by each step.

3. **Record the ingested path**

   After the nested `ingest` workflow completes, record where the material was filed. Write a simple reference file that the `analyze` step can use to find the ingested content.

## Output Format

### ingested_path

A reference file pointing to the ingested material.

**Location**: `research/[topic_slug]/ingested_path.md`

```markdown
# Ingested Material Reference

**Topic**: [topic_slug]
**Filed to**: [absolute path to the filed note from the ingest workflow]
**Ingested**: [YYYY-MM-DD]

## Source Material

- **Type**: [file | url | pasted]
- **Original location**: [file path, URL, or "inline"]

## Key Findings (from ingest)

[Copy the key findings extracted during the parse step — these seed the reproducibility analysis]
```

## Quality Criteria

- Nested ingest workflow completes successfully (both parse and file steps)
- Ingested path reference points to a real file that exists
- Key findings from the parse step are captured for the analyze step

## Context

This is the first step of the **reproduce** workflow. It uses the **nested workflow pattern** — starting the `ingest` workflow within this step. This means the material goes through the same parse → file pipeline as standalone ingestion, ensuring consistency. The `analyze` step that follows reads the ingested material to identify reproducible claims.
