# Document the process

## Objective

Synthesize everything observed during the conversation into a structured process document, then confirm key details with the user.

## Task

### 1. Draft from memory

Reflect on the entire conversation from the observe step. Write a first draft of the process document capturing every action, tool, decision, and outcome you observed.

If the conversation feels incomplete (e.g., compaction happened and you lost context), tell the user what you remember and ask them to fill in the gaps before drafting.

### 2. Clarify with the user

After drafting, use AskUserQuestion to confirm three things (ask all at once if possible):

1. **Purpose**: "What is the goal of this process? What does it accomplish?"
2. **Name**: "What would you call this process?" (suggest a name based on what you observed)
3. **Variable vs. fixed inputs**: "Which inputs change every time you run this, and which stay the same?"

### 3. Amend the document

Update the draft to incorporate the user's answers. Ensure the process name, purpose, and input classification are reflected throughout.

## Output format

### process_document.md

```markdown
# Process Document: [process_name]

## Purpose
[What this process accomplishes and who it serves, as confirmed by the user]

## Inputs
### Variable (change each invocation)
- [input]: [description]

### Fixed (same every time)
- [input]: [description]

## Tool Inventory
| Tool | Purpose | Required Access |
|------|---------|-----------------|
| [tool] | [what it's used for] | [setup needed] |

## Process Steps

### Step 1: [Step name]
- **Purpose**: [What this step accomplishes]
- **Type**: [User-interactive / Autonomous / Semi-autonomous]
- **Inputs**: [What enters this step]
- **Actions**:
  1. [Action]
  2. [Action]
- **Outputs**: [What this step produces]
- **Decision points**: [Any branching logic]

[Repeat for each step]

## Data Flow
[How outputs from one step feed into the next]

## External Dependencies
- [Services, APIs, credentials, or resources required]

## Implicit Knowledge
- [Things the user relied on that an AI agent would need to be told]
```

## Quality criteria

- All observed actions and tools are represented
- Steps are logically ordered with clear inputs, outputs, and decision points
- The document includes the process name, purpose, and variable vs. fixed inputs as confirmed by the user
