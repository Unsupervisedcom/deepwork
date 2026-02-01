---
name: experts.define
description: "Create a workflow.yml by gathering requirements through structured questions"

---

# experts.define

**Step 1/3** in **new_workflow** workflow

> Create a new multi-step DeepWork workflow with spec definition, review, and implementation


## Instructions

**Goal**: Create a workflow.yml by gathering requirements through structured questions

# Define Workflow Specification

## Objective

Create a `workflow.yml` specification file that defines a new DeepWork workflow by understanding the user's requirements through interactive questioning.

## Task

Guide the user through defining a workflow specification by asking structured questions. The output is **only** the `workflow.yml` file - step instruction files are created in the `implement` step.

### Phase 1: Understand the Workflow Purpose

Ask structured questions to understand the workflow:

1. **Overall goal** - What complex task are they trying to accomplish? What domain (research, marketing, development, reporting)?

2. **Success criteria** - What's the final deliverable? Who is the audience? What quality matters most?

3. **Major phases** - What are the distinct stages from start to finish? Any dependencies between phases?

4. **Expert context** - Which expert should this workflow belong to? Existing one or create new?

### Phase 2: Detect Document-Oriented Workflows

Check for document-focused patterns in the user's description:
- Keywords: "report", "summary", "document", "monthly", "quarterly", "for stakeholders"
- Final deliverable is a specific document type
- Recurring documents with consistent structure

**If detected**, offer to create a doc spec:
1. Inform the user: "This workflow produces a specific document type. I recommend defining a doc spec first."
2. Ask if they want to create a doc spec, use existing one, or skip

**If creating a doc spec**, gather:
- Document name and purpose
- Target audience and frequency
- Quality criteria (3-5, focused on the output document itself)
- Document structure (sections, required elements)

Create at `.deepwork/doc_specs/[doc_spec_name].md`.

### Phase 3: Define Each Step

For each major phase, gather:

1. **Purpose** - What does this step accomplish? What are inputs and outputs?

2. **Inputs**:
   - User-provided parameters (e.g., topic, target audience)?
   - Files from previous steps?

3. **Outputs**:
   - What files does this step produce?
   - Format (markdown, YAML, JSON)?
   - Where to save? (Use meaningful paths like `competitive_research/analysis.md`)
   - Does this output have a doc spec?

4. **Dependencies** - Which previous steps must complete first?

5. **Process** - Key activities? Quality checks needed?

6. **Agent Delegation** - Should this step run via a specific expert? Use `agent: experts` for domain-specific expertise.

#### Output Path Guidelines

- Place outputs in main repo, not dot-directories
- Use workflow name as top-level folder for workflow-specific outputs
- Include dates for periodic outputs that accumulate (monthly reports)
- Omit dates for current-state outputs that get updated in place
- Use `_dataroom` folders for supporting materials

### Phase 4: Validate the Workflow

After gathering all step information:

1. **Review the flow** - Summarize the complete workflow, show how outputs feed into next steps
2. **Check for gaps** - Undefined inputs? Unused outputs? Circular dependencies?
3. **Confirm details** - Workflow name (lowercase_underscores), summary (max 200 chars), description (detailed), version (1.0.0)
4. **Step ID uniqueness** - Step IDs must be unique within the expert, across all workflows

### Phase 5: Create the Workflow

Determine the expert and create the directory structure:

```bash
mkdir -p .deepwork/experts/[expert_name]/workflows/[workflow_name]/steps
```

Create `workflow.yml` at `.deepwork/experts/[expert_name]/workflows/[workflow_name]/workflow.yml`.

**Validation rules**:
- Workflow name: lowercase, underscores, no spaces (must match folder name)
- Version: semantic versioning (1.0.0)
- Summary: under 200 characters
- Step IDs: unique within the expert, lowercase with underscores
- Dependencies must reference existing steps
- File inputs with `from_step` must be in dependencies
- At least one output per step

## Output

**File**: `.deepwork/experts/[expert_name]/workflows/[workflow_name]/workflow.yml`

After creating the file, the next step will review it against quality criteria.


### Workflow Context

Guide the user through creating a new DeepWork workflow by:
1. Understanding their workflow requirements through interactive questioning
2. Creating a validated workflow.yml specification
3. Reviewing the spec against quality criteria
4. Generating step instruction files and syncing skills


## Required Inputs

**User Parameters** - Gather from user before starting:
- **workflow_purpose**: What complex task are you trying to accomplish?


## Work Branch

Use branch format: `deepwork/experts-new_workflow-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/experts-new_workflow-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `.deepwork/experts/{expert_name}/workflows/{workflow_name}/workflow.yml`

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## On Completion

1. Verify outputs are created
2. Inform user: "new_workflow step 1/3 complete, outputs: .deepwork/experts/{expert_name}/workflows/{workflow_name}/workflow.yml"
3. **Continue workflow**: Use Skill tool to invoke `/experts.review_workflow_spec`

---

**Reference files**: `.deepwork/experts/experts/workflows/new_workflow/workflow.yml`, `.deepwork/experts/experts/workflows/new_workflow/steps/define.md`