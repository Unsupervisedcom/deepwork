# Document the process

## Objective

Synthesize the raw observation log into a structured process document that captures all tools, steps, inputs, outputs, and decision points in a form suitable for automation.

## Task

Read the observation log from the observe step and transform it into a clean, structured process document. This document will be used both as a standalone reference and as input for generating a DeepWork job definition.

### Process

1. **Read the observation log**
   - Identify all distinct steps in the process
   - Note the tools and commands used at each step
   - Map the data flow: what outputs from one step feed into the next

2. **Normalize and structure**
   - Group related actions into logical steps (the raw log may have finer granularity than needed)
   - Name each step with a clear, descriptive title
   - Identify which steps require user input vs. which can run autonomously
   - Document decision points and branching logic

3. **Catalog tools and resources**
   - List every tool, command, API, or service used
   - Note the purpose of each tool in the context of this process
   - Flag any tools that require special access or configuration

4. **Define inputs and outputs for each step**
   - What information enters the step (user input, file from prior step, external data)
   - What the step produces (files, state changes, API calls)
   - What format each input/output is in

## Output Format

### process_document.md

A structured process document ready to inform job creation.

**Structure**:
```markdown
# Process Document: [process_name]

## Summary
[1-2 sentence description of what this process accomplishes and who it serves]

## Tool Inventory
| Tool | Purpose | Required Access |
|------|---------|-----------------|
| [tool name] | [what it's used for] | [any setup needed] |

## Process Steps

### Step 1: [Step name]
- **Purpose**: [What this step accomplishes]
- **Type**: [User-interactive / Autonomous / Semi-autonomous]
- **Inputs**:
  - [Input name]: [description] (source: [user / prior step / external])
- **Actions**:
  1. [Action description]
  2. [Action description]
- **Outputs**:
  - [Output name]: [description] (format: [markdown / JSON / etc.])
- **Decision points**: [Any branching logic or conditional actions]

[Repeat for each step]

## Data Flow
[Description or diagram of how data moves between steps]

## External Dependencies
- [Service, API, or resource this process depends on]
- [Access requirements or credentials needed]
```

## Quality Criteria

- Every action and tool from the observation log is represented in the process document
- Steps are logically ordered with clear inputs, outputs, and decision points for each
- All tools, commands, and external resources used are listed with their purpose
- The document distinguishes between user-interactive and autonomous steps
- Data flow between steps is explicit — no implicit handoffs

## Context

This document serves as the blueprint for the generated DeepWork job. The clearer and more structured it is, the better the generated job will be. Focus on making the process reproducible by someone (or an AI agent) who has never seen it before.
