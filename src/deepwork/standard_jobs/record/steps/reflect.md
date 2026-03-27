# Reflect on the process

## Objective

Analyze the recorded process to identify efficiency improvements, stumbling blocks, and recommendations that should be incorporated into the automated workflow.

## Task

Read both the observation log and the process document, then produce a reflection that identifies what went well, what was painful, and what could be improved when this process runs as an automated workflow.

### Process

1. **Review the raw observations**
   - Re-read the observation log, paying attention to:
     - Places where the user hesitated or backtracked
     - Workarounds or manual steps that felt tedious
     - Steps that took disproportionately long
     - Implicit knowledge the user relied on

2. **Identify stumbling blocks**
   - What steps were error-prone or confusing?
   - Where did the user need to retry or course-correct?
   - What external dependencies caused delays or friction?
   - What implicit knowledge would an AI agent lack?

3. **Identify efficiency improvements**
   - Which steps could be parallelized?
   - Where could templates or defaults reduce manual input?
   - Are there steps that could be combined or eliminated?
   - Could any manual lookups be automated with tools?

4. **Formulate recommendations**
   - For each improvement, describe the concrete change to make in the automated workflow
   - For each stumbling block, describe how to mitigate it (better instructions, validation, fallback)
   - Prioritize by impact: what changes would save the most time or prevent the most errors?

## Output Format

### reflection.md

An analysis with actionable recommendations for the automated workflow.

**Structure**:
```markdown
# Process Reflection: [process_name]

## Summary
[1-2 sentences on the overall quality of the process and the biggest opportunities]

## Stumbling Blocks

### 1. [Block title]
- **What happened**: [Describe the specific issue observed]
- **Impact**: [How it affected the process — time lost, errors, rework]
- **Mitigation**: [How to prevent or handle this in the automated workflow]

[Repeat for each stumbling block]

## Efficiency Improvements

### 1. [Improvement title]
- **Current state**: [How the step works now]
- **Proposed change**: [Specific change to make]
- **Expected benefit**: [Time saved, errors prevented, or quality improved]

[Repeat for each improvement]

## Recommendations for Automated Workflow

### Step-level recommendations
| Step | Recommendation | Priority |
|------|---------------|----------|
| [step name] | [what to change] | [high/medium/low] |

### Workflow-level recommendations
- [Any structural changes — reordering, parallelization, new steps, removed steps]

## Implicit Knowledge to Encode
- [Things the user knew that an AI agent would need to be told explicitly]
- [Domain conventions, naming patterns, or unwritten rules]
```

## Quality Criteria

- Each improvement is specific and explains how to implement it in the automated workflow
- Pain points and failure-prone steps from the recording are identified with mitigation strategies
- Insights reference specific observations from the recording, not generic advice
- Implicit knowledge that an AI agent would need is surfaced and documented
- Recommendations are prioritized by impact

## Context

This reflection is the bridge between "what happened" and "what the automated workflow should do." The generated DeepWork job should be better than the raw recording — incorporating the lessons learned here. Focus on actionable insights that translate directly into better step instructions, validation checks, or workflow structure.
