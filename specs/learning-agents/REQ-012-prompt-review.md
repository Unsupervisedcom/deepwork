# REQ-012: Prompt Review

## Overview

The `prompt-review` skill reviews a prompt or instruction file against Anthropic prompt engineering best practices and provides structured, actionable feedback. It is a standalone skill independent of the learning cycle.

## Requirements

### REQ-012.1: Skill Invocation

The skill MUST be user-invocable via `/learning-agents:prompt-review <path>`. If no path argument is provided, the skill MUST ask the user which file to review.

### REQ-012.2: Best Practices Fetch

The skill MUST attempt to fetch current Anthropic prompt engineering guidance from `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview` using WebFetch. If the fetch fails, the skill MUST proceed using built-in knowledge of Anthropic prompt engineering best practices.

### REQ-012.3: File Reading

The skill MUST read the file at the specified path. If the path is relative, it MUST be resolved from the current working directory. If the file does not exist, the skill MUST inform the user and stop.

### REQ-012.4: Prompt Context Determination

Before evaluating, the skill MUST identify the prompt context type:
- **Standalone system prompt**: The file is the complete prompt
- **Instruction chunk / skill file**: The file is injected into a larger prompt context
- **Template with variables**: The file contains placeholders or templates filled at runtime

### REQ-012.5: Evaluation Criteria

The skill MUST evaluate the file against all of the following criteria:
1. Clarity and Specificity
2. Structure and Formatting
3. Role and Identity Prompting
4. Examples and Demonstrations
5. Handling Ambiguity and Edge Cases
6. Output Format Specification
7. Composability (for instruction chunks)
8. Conciseness and Signal-to-Noise Ratio
9. Variable and Placeholder Usage
10. Task Decomposition

### REQ-012.6: Per-Criterion Assessment

For each of the 10 evaluation criteria, the skill MUST assess whether the prompt follows it well, partially, or poorly.

### REQ-012.7: Output Format

The skill MUST produce a review in the following structure:
- Prompt type classification
- Overall grade (A through F)
- One-sentence quality summary
- Strengths list (specific, with explanations)
- Issues found (each with severity, related criterion, location, problem description, and recommendation)
- Summary of recommendations table (priority, description, effort)

### REQ-012.8: Grading Rubric

The skill MUST use the following grading scale:
- **A**: Follows nearly all best practices. Minor improvements only. Production-ready.
- **B**: Follows most best practices. A few notable gaps. Effective but could be stronger.
- **C**: Misses several important practices. Will work but likely produces inconsistent results.
- **D**: Significant issues. Missing structure, clarity, or key prompt engineering patterns.
- **F**: Fundamentally flawed. Needs a rewrite to be effective.

### REQ-012.9: Issue Severity Levels

Each issue found MUST be classified with a severity level: Critical, High, Medium, or Low.

### REQ-012.10: Actionable Recommendations

Every recommendation MUST point to a concrete line or section in the file and explain exactly what to change. Recommendations SHOULD include before/after examples when helpful.

### REQ-012.11: Allowed Tools

The skill MUST only use the following tools: Read, Glob, Grep, WebFetch.
