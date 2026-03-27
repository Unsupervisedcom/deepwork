# JOBS-REQ-011: Record Standard Job

## Overview

The `record` standard job enables AI agents to observe a user performing a process, document it, reflect on improvements, and generate a reusable DeepWork job definition from the recording. It ships as a standard job bundled with the DeepWork package.

## Requirements

### JOBS-REQ-011.1: Job Structure

1. The `record` standard job MUST be located in `src/deepwork/standard_jobs/record/`.
2. The job MUST contain a valid `job.yml` that passes schema validation (see JOBS-REQ-002).
3. The job MUST define exactly four steps: `observe`, `document`, `reflect`, and `generate_job`.
4. The job MUST define a `record` workflow that sequences all four steps in order.

### JOBS-REQ-011.2: Observe Step

1. The `observe` step MUST accept two user-provided inputs: `process_name` and `process_description`.
2. The `observe` step MUST produce an `observation_log.md` output file.
3. The observation log MUST capture actions, tools used, decisions, and outcomes chronologically.

### JOBS-REQ-011.3: Document Step

1. The `document` step MUST consume `observation_log.md` from the `observe` step.
2. The `document` step MUST produce a `process_document.md` output file.
3. The process document MUST include a tool inventory, structured steps with inputs and outputs, and data flow.
4. The `document` step MUST have quality reviews validating complete coverage, clear structure, and tool inventory.

### JOBS-REQ-011.4: Reflect Step

1. The `reflect` step MUST consume both `observation_log.md` and `process_document.md` from prior steps.
2. The `reflect` step MUST produce a `reflection.md` output file.
3. The reflection MUST identify stumbling blocks with mitigation strategies and efficiency improvements with expected benefits.
4. The `reflect` step MUST have quality reviews validating actionable improvements, stumbling block identification, and evidence grounding.

### JOBS-REQ-011.5: Generate Job Step

1. The `generate_job` step MUST consume `process_document.md` and `reflection.md` from prior steps.
2. The `generate_job` step MUST produce a `job_created.md` confirmation file.
3. The `generate_job` step MUST defer to the `deepwork_jobs/new_job` workflow as a nested workflow for job creation.
4. The `generate_job` step MUST use the process document and reflection to inform the nested workflow rather than starting from scratch.
