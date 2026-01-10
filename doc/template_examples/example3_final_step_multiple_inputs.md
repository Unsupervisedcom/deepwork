# Example 3: Final Step with Multiple File Inputs

**Context**: Step 4 of competitive_research (final step) - has multiple file inputs, multiple dependencies

**Rendered Output**:

---

Name: competitive_research.comparative_report
Description: Create detailed comparison matrix

## Overview

This is step 4 of 4 in the **competitive_research** workflow.

**Job**: Systematic competitive analysis workflow

## Prerequisites

This step requires completion of the following step(s):
- `/competitive_research.primary_research`
- `/competitive_research.secondary_research`

Please ensure these steps have been completed before proceeding.

## Instructions

# Comparative Report

## Objective
Create a comprehensive comparison matrix of all competitors.

## Task
Synthesize findings from primary and secondary research into a structured comparison.

## Deliverables
1. Comparison matrix showing feature-by-feature analysis
2. Strengths and weaknesses document highlighting key insights

## Inputs

### Required Files

This step requires the following files from previous steps:
- `primary_research.md` (from step `primary_research`)
  Location: `work/[branch-name]/primary_research.md`
- `secondary_research.md` (from step `secondary_research`)
  Location: `work/[branch-name]/secondary_research.md`

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
- `work/[branch-name]/comparison_matrix.md`
- `work/[branch-name]/strengths_weaknesses.md`

Ensure all outputs are:
- Well-formatted and complete
- Committed to the work branch
- Ready for review or use by subsequent steps

## Completion

After completing this step:

1. **Commit your work**:
   ```bash
   git add work/[branch-name]/
   git commit -m "competitive_research: Complete comparative_report step"
   ```

2. **Verify outputs**: Confirm all required files have been created

3. **Inform the user**:
   - Step 4 of 4 is complete
   - Outputs created: comparison_matrix.md, strengths_weaknesses.md
   - This is the final step - the job is complete!

## Workflow Complete

This is the final step in the competitive_research workflow. All outputs should now be complete and ready for review.

Consider:
- Reviewing all work products in `work/[branch-name]/`
- Creating a pull request to merge the work branch
- Documenting any insights or learnings

---

## Context Files

- Job definition: `.deepwork/jobs/competitive_research/job.yml`
- Step instructions: `.deepwork/jobs/competitive_research/steps/comparative_report.md`
