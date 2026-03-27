# Reflect on the process

## Objective

Analyze the process document to identify efficiency improvements, stumbling blocks, and recommendations for the automated workflow.

## Task

### 1. Review the process document

Read `process_document.md` and look for:
- Steps that were error-prone or required backtracking
- Workarounds or manual steps that felt tedious
- Steps that took disproportionately long
- Implicit knowledge that an AI agent would lack
- External dependencies that caused friction

### 2. Identify stumbling blocks

For each pain point, describe what happened, its impact, and how to mitigate it in the automated workflow.

### 3. Identify efficiency improvements

Look for:
- Steps that could be parallelized
- Places where templates or defaults could reduce manual input
- Steps that could be combined or eliminated
- Manual lookups that could be automated

### 4. Prioritize recommendations

Rank by impact: what changes would save the most time or prevent the most errors?

## Output format

### reflection.md

```markdown
# Process Reflection: [process_name]

## Summary
[1-2 sentences on the biggest opportunities]

## Stumbling Blocks

### 1. [Block title]
- **What happened**: [Specific issue from the process document]
- **Impact**: [Time lost, errors, rework]
- **Mitigation**: [How to handle this in the automated workflow]

## Efficiency Improvements

### 1. [Improvement title]
- **Current state**: [How the step works now]
- **Proposed change**: [Specific change]
- **Expected benefit**: [Time saved, errors prevented]

## Recommendations for Automated Workflow

| Step | Recommendation | Priority |
|------|---------------|----------|
| [step] | [change] | [high/medium/low] |

## Implicit Knowledge to Encode
- [Things an AI agent would need to be told explicitly]
```

## Quality criteria

- Each improvement is specific and explains how to implement it in the automated workflow
- Pain points are identified with mitigation strategies
- Insights reference specific details from the process document, not generic advice
