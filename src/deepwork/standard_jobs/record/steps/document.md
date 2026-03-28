# Document the process

## Objective

Synthesize everything observed during the conversation into a structured process document, then confirm key details with the user.

## Task

### 1. Reconstruct the process

Reflect on the entire conversation from the observe step. If any compaction has happened, use `CLAUDE_CODE_SESSION_ID` to locate and read the session transcript (glob `~/.claude/projects/**/sessions/<session_id>/*.jsonl`) to recover what was lost before drafting.

Write a first draft of the process document capturing every action, tool, decision, and outcome you observed.

### 2. Clarify with the user

After drafting, use AskUserQuestion to address two things (combine into one question where possible):

1. **Remaining reasoning gaps**: Ask about any actions whose purpose you are still uncertain about after reviewing the conversation or transcript.
2. **Key facts** — only ask about items where you cannot answer from what was explicitly stated or clearly demonstrated during the observation:
   - **Purpose**: What is the goal of this process? What does it accomplish?
   - **Name**: What would you call this process? (suggest a name based on what you observed)
   - **Variable vs. fixed inputs**: Which inputs change every time you run this, and which stay the same?

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
