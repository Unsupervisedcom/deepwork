# Translate Product Issue to Engineering Issue

Transform the product issue into a distinct engineering issue with implementation plan,
test definitions (red/green states), and traceability links.

## Process

1. Fetch the product issue — extract user story, requirements, acceptance criteria, and constraints
2. Read agent.md to determine the engineering domain and build/test conventions; if missing, warn the user and recommend the `doctor` workflow
3. Draft the engineering issue:
   - Definitive implementation plan with actionable tasks
   - Red and green test state definitions for each requirement
   - Domain-appropriate schematics, code references, or configuration details
   - Every product requirement mapped to at least one task
4. Create the issue on the git platform, label as `engineering`, link to parent product issue

## Output Format

### .deepwork/tmp/engineering_issue.md

```markdown
# Engineering Issue: [Title]

## Parent Product Issue
- URL: [product_issue_url]
- User Story: [one-line summary]

## Implementation Plan

### Task 1: [task name]
- Requirement: Req [N] — [requirement summary]
- Description: [what to implement]
- Files: [expected files to create/modify]

## Test Definitions

| Test | Requirement | Red State (before) | Green State (after) |
|------|-------------|---------------------|---------------------|
| [test name] | Req [N] | [expected failure] | [expected pass] |

## Domain Context
- Engineering domain: [from agent.md]
- Build system: [from agent.md]
- Test framework: [from agent.md]
```

### .deepwork/tmp/engineering_issue_url.md

Single-line file containing the URL of the created engineering issue.
