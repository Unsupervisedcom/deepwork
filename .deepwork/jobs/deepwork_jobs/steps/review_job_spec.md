# Review Job Specification

## Objective

Review the `job.yml` created in the define step against the DTD quality criteria using a sub-agent for unbiased evaluation, then iterate on fixes until all criteria pass.

## Why This Step Exists

The define step focuses on understanding user requirements and creating a job specification. This review step ensures the specification meets quality standards before implementation. Using a sub-agent provides an unbiased "fresh eyes" review that catches issues the main agent might miss after being deeply involved in the definition process.

## Task

Use a sub-agent to review the job.yml against all 9 DTD quality criteria, then fix any failed criteria. Repeat until all criteria pass.

### Step 1: Read the Job Specification

Read the `job.yml` file created in the define step:

```
.deepwork/jobs/[job_name]/job.yml
```

Also read the DTD for reference:

```
.deepwork/dtds/job_spec.md
```

### Step 2: Spawn Review Sub-Agent

Use the Task tool to spawn a sub-agent that will provide an unbiased review:

```
Task tool parameters:
- subagent_type: "general-purpose"
- model: "haiku"
- description: "Review job.yml against DTD"
- prompt: [see below]
```

**Sub-agent prompt template:**

```
Review this job.yml against the following 9 quality criteria from the DTD.

For each criterion, respond with:
- PASS or FAIL
- If FAIL: specific issue and suggested fix

## job.yml Content

[paste the full job.yml content here]

## Quality Criteria

1. **Valid Identifier**: Job name must be lowercase with underscores, no spaces or special characters (e.g., `competitive_research`, `monthly_report`)

2. **Semantic Version**: Version must follow semantic versioning format X.Y.Z (e.g., `1.0.0`, `2.1.3`)

3. **Concise Summary**: Summary must be under 200 characters and clearly describe what the job accomplishes

4. **Rich Description**: Description must be multi-line and explain: the problem solved, the process, expected outcomes, and target users

5. **Changelog Present**: Must include a changelog array with at least the initial version entry

6. **Complete Steps**: Each step must have: id (lowercase_underscores), name, description, instructions_file, outputs (at least one), and dependencies array

7. **Valid Dependencies**: Dependencies must reference existing step IDs with no circular references

8. **Input Consistency**: File inputs with `from_step` must reference a step that is in the dependencies array

9. **Output Paths**: Outputs must be valid filenames or paths (e.g., `report.md` or `reports/analysis.md`)

## Response Format

Respond with a structured evaluation:

### Overall: [X/9 PASS]

### Criterion Results

1. Valid Identifier: [PASS/FAIL]
   [If FAIL: Issue and fix]

2. Semantic Version: [PASS/FAIL]
   [If FAIL: Issue and fix]

[... continue for all 9 criteria ...]

### Summary of Required Fixes

[List any fixes needed, or "No fixes required - all criteria pass"]
```

### Step 3: Review Sub-Agent Findings

Parse the sub-agent's response:

1. **Count passing criteria** - How many of the 9 criteria passed?
2. **Identify failures** - List specific criteria that failed
3. **Note suggested fixes** - What changes does the sub-agent recommend?

### Step 4: Fix Failed Criteria

For each failed criterion, edit the job.yml to address the issue:

**Common fixes by criterion:**

| Criterion | Common Issue | Fix |
|-----------|-------------|-----|
| Valid Identifier | Spaces or uppercase | Convert to lowercase_underscores |
| Semantic Version | Missing or invalid format | Set to `"1.0.0"` or fix format |
| Concise Summary | Too long or vague | Shorten to <200 chars, be specific |
| Rich Description | Single line or missing context | Add multi-line explanation with problem/process/outcome/users |
| Changelog Present | Missing changelog | Add `changelog:` with initial version entry |
| Complete Steps | Missing required fields | Add id, name, description, instructions_file, outputs, dependencies |
| Valid Dependencies | Non-existent step or circular | Fix step ID reference or reorder dependencies |
| Input Consistency | from_step not in dependencies | Add the referenced step to dependencies array |
| Output Paths | Invalid characters or format | Use valid filename/path format |

### Step 5: Re-Run Review (If Needed)

If any criteria failed:

1. **Spawn a new sub-agent** with the updated job.yml content
2. **Review the new findings**
3. **Fix any remaining issues**
4. **Repeat until all 9 criteria pass**

### Step 6: Confirm Completion

When all 9 criteria pass:

1. **Announce success**: "All 9 DTD quality criteria pass."
2. **List what was validated**:
   - Valid Identifier
   - Semantic Version
   - Concise Summary
   - Rich Description
   - Changelog Present
   - Complete Steps
   - Valid Dependencies
   - Input Consistency
   - Output Paths
3. **Include the promise**: `<promise>Quality Criteria Met</promise>`
4. **Guide to next step**: "Run `/deepwork_jobs.implement` to generate the step instruction files."

## Example Review Cycle

```
Claude: Let me review the job.yml against the DTD quality criteria.

[Spawns sub-agent with haiku model]

Sub-agent response:
### Overall: 7/9 PASS

### Criterion Results
1. Valid Identifier: PASS
2. Semantic Version: PASS
3. Concise Summary: FAIL
   Issue: Summary is 245 characters, exceeds 200 char limit
   Fix: Shorten to "Competitive analysis workflow for product positioning"
4. Rich Description: PASS
5. Changelog Present: FAIL
   Issue: No changelog array present
   Fix: Add changelog with initial version entry
6. Complete Steps: PASS
7. Valid Dependencies: PASS
8. Input Consistency: PASS
9. Output Paths: PASS

### Summary of Required Fixes
1. Shorten summary to under 200 characters
2. Add changelog array with initial version

Claude: I found 2 issues. Let me fix them.

[Edits job.yml to shorten summary and add changelog]

Claude: Let me verify the fixes with another review.

[Spawns new sub-agent]

Sub-agent response:
### Overall: 9/9 PASS

### Summary of Required Fixes
No fixes required - all criteria pass

Claude: All 9 DTD quality criteria pass.

<promise>Quality Criteria Met</promise>

**Next step:** Run `/deepwork_jobs.implement` to generate the step instruction files.
```

## Quality Criteria

- **Sub-Agent Used**: A sub-agent was spawned to provide unbiased review (not just self-review)
- **All DTD Criteria Evaluated**: The sub-agent assessed all 9 quality criteria from the DTD
- **Findings Addressed**: All failed criteria were fixed by the main agent
- **Validation Loop Complete**: The review-fix cycle continued until all criteria passed
- **Promise Included**: The response includes `<promise>Quality Criteria Met</promise>` when complete

## Output

The validated `job.yml` file at `.deepwork/jobs/[job_name]/job.yml` that passes all 9 DTD quality criteria.
