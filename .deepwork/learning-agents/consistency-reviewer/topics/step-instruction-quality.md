---
name: "Step Instruction Quality Patterns"
keywords:
  - step instructions
  - prompt quality
  - writing style
  - sections
  - output format
last_updated: "2026-02-18"
---

## Section Structure

Every step instruction file should follow this section order:

1. `# [Step Name]` — H1 heading matching the step's `name` field from job.yml
2. `## Objective` — single paragraph stating what the step achieves
3. `## Task` — detailed explanation, typically with a `### Process` subsection
4. `## Output Format` — subsection per output with code block templates
5. `## Quality Criteria` — bullet list matching or extending the review criteria from job.yml
6. `## Context` — narrative about the step's place in the workflow

## Writing Style Checklist

- Written for an AI agent (not a human developer)
- Professional, prescriptive, action-oriented tone
- Process substeps are numbered and concrete
- No vague instructions ("think carefully about...") — instead state what to do
- Output format sections include filled-in examples, not just empty templates
- No duplication of `common_job_info_provided_to_all_steps_at_runtime` content

## Quality Criteria Alignment

The Quality Criteria section in the instruction file should align with the `quality_criteria` map in the step's `reviews` configuration in job.yml. They don't need to be identical, but:
- Every criterion in job.yml should have a corresponding bullet in the instructions
- The instructions can include additional criteria beyond what the formal review checks
- Wording should be consistent between the two locations

## Common Instruction Anti-Patterns

- **Generic instructions**: "Write a good report" instead of specifying format, content requirements, and examples
- **Missing output format**: Step produces a file but doesn't describe its expected structure
- **Contradictory guidance**: Instruction says "keep it concise" but Quality Criteria says "be comprehensive"
- **Undeclared assumptions**: Instructions reference information from a prior step but the step doesn't declare the corresponding input
- **Placeholder content**: Leftover TODOs, stub sections, or template text that wasn't filled in
