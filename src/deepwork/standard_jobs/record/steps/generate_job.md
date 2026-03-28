# Generate DeepWork job

## Objective

Launch the `deepwork_jobs/new_job` workflow to create a complete DeepWork job definition, using the process document and reflection as context to drive the definition.

## Task

Start the existing `deepwork_jobs/new_job` workflow as a nested workflow. Use the process document and reflection to provide informed answers during the job definition process rather than starting from scratch.

### Process

1. **Read the inputs**
   - Read `process_document.md` to understand the steps, tools, inputs, and outputs
   - Read `reflection.md` to understand improvements and stumbling blocks to incorporate

2. **Prepare the goal**
   - Synthesize a clear goal statement from the process document summary and the reflection recommendations
   - The goal should describe what the automated job will do, incorporating the efficiency improvements

3. **Start the nested workflow**
   - Call `start_workflow` with:
     - `job_name`: `"deepwork_jobs"`
     - `workflow_name`: `"new_job"`
     - `goal`: the synthesized goal from above
   - Follow the `new_job` workflow's instructions as they come

4. **Use the process document to drive definition**
   - When the `new_job` define step asks about the workflow's purpose, draw from the process document summary
   - When asked about steps, map from the process document's step list — but incorporate reflection recommendations (reordering, parallelization, new validation steps)
   - When asked about inputs/outputs, use the process document's data flow
   - When asked about quality reviews, use the stumbling blocks from the reflection to define what to check
   - Encode implicit knowledge from the reflection into the `common_job_info_provided_to_all_steps_at_runtime`

5. **Confirm with the user**
   - Before finalizing, present the mapping: which recorded steps became which job steps, and what changes were made based on the reflection
   - Ask the user if the generated job captures their intent

6. **Record what was created**
   - After the nested workflow completes, write a brief confirmation file noting the job name and location

## Output Format

### job_created.md

A brief confirmation of what was generated.

**Structure**:
```markdown
# Job Created: [new_job_name]

## Location
`.deepwork/jobs/[new_job_name]/`

## Summary
[One-line summary of the generated job]

## Steps
1. [step_name] - [brief description]
2. [step_name] - [brief description]

## Changes from Recording
- [What was changed from the raw recording based on reflection insights]

## Next Steps
- Review the generated job.yml and step instruction files
- Run the job with `/deepwork [new_job_name]` to test it
- Use `/deepwork learn` after testing to refine the instructions
```

## Quality Criteria

- The nested `deepwork_jobs/new_job` workflow is started (not bypassed)
- The process document and reflection are used to inform the job definition
- Reflection improvements are incorporated into the job structure and step instructions
- The user confirms the generated job before finalizing
- A confirmation file documents what was created and what changed from the recording

## Context

This step bridges recording and automation. By deferring to the existing `new_job` workflow, we get the full quality gate process for job creation while using the recorded process and reflection as rich input context. The result should be a job that is better than a literal replay of the recording — it should incorporate the efficiency improvements and stumbling block mitigations from the reflection.
