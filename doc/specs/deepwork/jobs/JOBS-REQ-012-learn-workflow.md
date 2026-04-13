# JOBS-REQ-012: Learn Workflow

## Overview

The `learn` workflow in the `deepwork_jobs` standard job analyzes conversation history to extract learnings from DeepWork job executions. It improves job instructions with generalizable insights, captures run-specific learnings in AGENTS.md files, and creates preventive automation (DeepSchemas and DeepReview rules) to prevent recurring issues.

## Requirements

### JOBS-REQ-012.1: Learning Classification

1. The learn workflow MUST classify each identified learning as either **generalizable** (applicable to future runs of the same job) or **bespoke** (specific to the current run/context).
2. Generalizable learnings MUST be applied to job instruction files.
3. Bespoke learnings MUST be captured in an AGENTS.md file in the deepest common folder that would contain all future work on the topic.

### JOBS-REQ-012.2: Prevention Opportunity Evaluation

1. The learn workflow MUST evaluate whether DeepSchemas or DeepReview rules could prevent issues encountered during the session.
2. If prevention opportunities exist, the workflow SHOULD create the corresponding DeepSchemas or DeepReview rules.
3. If no prevention opportunities are found, the workflow MUST state why none were identified.

### JOBS-REQ-012.3: Step Arguments

1. The learn workflow MUST accept a `deepschemas` step argument for outputting created DeepSchema files.
2. The learn workflow MUST accept a `deepreviews` step argument for outputting created DeepReview rule files.

### JOBS-REQ-012.4: Process Requirements

1. The workflow MUST enforce that generalizable learnings are applied to job instructions ("Generalizable Learnings Applied").
2. The workflow MUST enforce that bespoke learnings are captured in AGENTS.md ("Bespoke Learnings Captured").
3. The workflow MUST enforce that prevention opportunities are evaluated ("Prevention Opportunities Evaluated").
