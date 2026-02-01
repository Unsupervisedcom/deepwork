# Define Job Specification

## Objective

Create a `job.yml` specification file by thoroughly understanding the user's workflow requirements through structured questions.

## Task

Guide the user through defining a job specification by asking structured questions. **Do not attempt to create the specification without first fully understanding the user's needs.**

The output of this step is **only** the `job.yml` file. Step instruction files are created in the `implement` step.

### Step 1: Understand the Job Purpose

Ask structured questions to understand what the user wants to accomplish:

1. **What is the overall goal of this workflow?**
   - What complex task are they trying to accomplish?
   - What domain is this in? (e.g., research, marketing, development, reporting)

2. **What does success look like?**
   - What's the final deliverable or outcome?
   - Who is the audience for the output?

3. **What are the major phases?**
   - What are the distinct stages from start to finish?
   - Are there any dependencies between phases?

### Step 2: Detect Document-Oriented Workflows

Check for document-focused patterns in the user's description:
- Keywords: "report", "summary", "document", "monthly", "quarterly"
- Final deliverable is a specific document type
- Recurring documents with consistent structure

**If detected**, inform the user and ask if they want to:
- Create a doc spec for consistent document quality
- Use an existing doc spec from `.deepwork/doc_specs/`
- Skip doc spec and proceed with simple outputs

See the expert's documentation on doc specs for the full schema and examples.

### Step 3: Define Each Step

For each major phase, gather:

1. **Step Purpose**: What does this step accomplish?
2. **Inputs**: User parameters or files from previous steps
3. **Outputs**: Files or artifacts produced (see Work Product Guidelines below)
4. **Dependencies**: Which previous steps must complete first?
5. **Quality Criteria**: What makes a good vs. bad output?
6. **Agent Delegation**: Should this step run in a forked context?

#### Work Product Storage Guidelines

Job outputs belong in the main repository directory structure, not in dot-directories.

**Good patterns**:
```
competitive_research/competitors_list.md
operations/reports/2026-01/spending_analysis.md
```

**Avoid**:
```
.deepwork/outputs/report.md    # Hidden in dot-directory
output.md                       # Too generic
```

**Date in paths**: Include for periodic outputs (monthly reports), omit for living documents.

**Supporting materials**: Place in `_dataroom` folder as peer to final output:
```
operations/reports/2026-01/spending_analysis.md
operations/reports/2026-01/spending_analysis_dataroom/
    raw_data.csv
    notes.md
```

### Step 4: Validate the Workflow

After gathering all information:

1. **Review the flow** - Summarize and show how outputs feed into the next step
2. **Check for gaps** - Missing inputs, unused outputs, circular dependencies
3. **Confirm details** - Job name, summary (max 200 chars), description, version

### Step 5: Create the Job Specification

**First, create the directory structure**:
```bash
.deepwork/jobs/deepwork_jobs/make_new_job.sh [job_name]
```

**Then create `job.yml`** at `.deepwork/jobs/[job_name]/job.yml`

Refer to the expert for the complete job.yml schema. Key validation rules:
- Job name: lowercase, underscores only, no spaces
- Version: semantic versioning (start with 1.0.0)
- Summary: max 200 characters
- File inputs: `from_step` must be in dependencies
- At least one output per step

**Templates**:
- `.deepwork/jobs/deepwork_jobs/templates/job.yml.template` - Structure
- `.deepwork/jobs/deepwork_jobs/templates/job.yml.example` - Complete example

## Output

The validated `job.yml` file at `.deepwork/jobs/[job_name]/job.yml`.

After creating the file:
1. Inform the user that the specification is complete
2. Recommend they review the job.yml file
3. Tell them to run `/deepwork_jobs.review_job_spec` next
