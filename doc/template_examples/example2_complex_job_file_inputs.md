# Example 2: Complex Job with File Inputs and Dependencies

**Context**: Step 2 of competitive_research - has file input from previous step, has dependencies

**Rendered Output**:

---

Name: competitive_research.primary_research
Description: Analyze competitors' self-presentation

## Overview

This is step 2 of 4 in the **competitive_research** workflow.

**Job**: Systematic competitive analysis workflow

## Prerequisites

This step requires completion of the following step(s):
- `/competitive_research.identify_competitors`

Please ensure these steps have been completed before proceeding.

## Instructions

# Primary Research

## Objective
Analyze competitors' self-presentation from their official channels.

## Task
Review each competitor and document their messaging.

## Inputs

### Required Files

This step requires the following files from previous steps:
- `competitors.md` (from step `identify_competitors`)
  Location: `work/[branch-name]/competitors.md`

Make sure to read and use these files as context for this step.

## Work Branch Management

All work for this job should be done on a dedicated work branch:

1. **Check current branch**:
   - If already on a work branch for this job (format: `work/competitive_research-[instance]-[date]`), continue using it
   - If on main/master, create a new work branch

2. **Create work branch** (if needed):
   ```bash
   git checkout -b work/competitive_research-[instance]-$(date +%Y%m%d)
   ```
   Replace `[instance]` with a descriptive identifier (e.g., `acme`, `q1-launch`, etc.)

3. **All outputs go in the work directory**:
   - Create files in: `work/[branch-name]/`
   - This keeps work products organized and reviewable

## Output Requirements

Create the following output(s) in the work directory:
- `work/[branch-name]/primary_research.md`
- `work/[branch-name]/competitor_profiles/` (directory)

Ensure all outputs are:
- Well-formatted and complete
- Committed to the work branch
- Ready for review or use by subsequent steps

## Completion

After completing this step:

1. **Commit your work**:
   ```bash
   git add work/[branch-name]/
   git commit -m "competitive_research: Complete primary_research step"
   ```

2. **Verify outputs**: Confirm all required files have been created

3. **Inform the user**:
   - Step 2 of 4 is complete
   - Outputs created: primary_research.md, competitor_profiles/
   - Ready to proceed to next step: `/competitive_research.secondary_research`

## Next Step

To continue the workflow, run:
```
/competitive_research.secondary_research
```

---

## Context Files

- Job definition: `.deepwork/jobs/competitive_research/job.yml`
- Step instructions: `.deepwork/jobs/competitive_research/steps/primary_research.md`
