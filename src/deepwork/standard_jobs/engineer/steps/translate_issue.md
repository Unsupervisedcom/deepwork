# Translate Product Issue to Engineering Issue

## Objective

Read the product issue, extract its requirements, and create a distinct engineering issue
containing the implementation plan, test definitions, and traceability links.

## Task

Transform a high-level product issue (user story + requirements) into a concrete engineering
issue that an agent or engineer can execute against. The engineering issue is a separate
artifact — not a copy of the product issue.

### Process

1. **Read the product issue**
   - Fetch the product issue using its URL or identifier
   - Extract the user story and all functional requirements
   - Identify any acceptance criteria, constraints, or non-functional requirements
   - Note the product issue's labels, milestone, and assignees

2. **Read the repository's agent.md**
   - Determine the project's engineering domain from agent.md (or equivalent)
   - Understand the build, test, and deployment conventions
   - If agent.md does not exist, warn the user and recommend running the `doctor` workflow first

3. **Draft the engineering issue**
   - Write a definitive implementation plan with actionable tasks
   - Define expected red and green test states for each requirement
   - Include applicable schematics, CAD snippets, code references, or configuration details
   - Map every product requirement to at least one implementation task

4. **Create the engineering issue on the platform**
   - Create a new issue on the git platform (GitHub, Forgejo, etc.)
   - Label it with `engineering`
   - Link it to the parent product issue
   - Assign it to the same milestone if applicable

### Domain Adaptation

| Concept              | Software            | Hardware/CAD         | Firmware            | Docs               |
|----------------------|---------------------|----------------------|---------------------|---------------------|
| Implementation plan  | Code changes        | Design changes       | Register/driver map | Content outline     |
| Test definitions     | Unit/integration    | DRC/simulation       | HIL/unit test       | Link check/lint     |
| Schematics/snippets  | API contracts       | KiCad/FreeCAD refs   | Pinout diagrams     | IA diagrams         |

## Output Format

### .deepwork/tmp/engineering_issue.md

The engineering issue content, structured for both platform posting and step consumption.

**Structure**:
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

### Task 2: [task name]
...

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

A single-line file containing the URL of the created engineering issue.

**Structure**:
```
https://github.com/owner/repo/issues/123
```

## Quality Criteria

- Every product requirement maps to at least one implementation task
- Test definitions cover all requirements with explicit red/green states
- The engineering issue is self-contained enough to execute without re-reading the product issue
- The issue was created on the platform with proper labels and links
- Domain-specific conventions from agent.md are reflected in the plan
