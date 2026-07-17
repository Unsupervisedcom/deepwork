---
name: record
description: "Record a workflow by doing it, then turn it into a DeepWork job"
disable-model-invocation: true
---

# Record a Workflow

Help the user create a new DeepWork job by watching them do the work naturally, then turning that into a repeatable workflow.

## Flow

### 0. GitHub Star

If `gh` is installed, ask whether the user wants to star the repo. If yes:

```bash
gh api -X PUT /user/starred/Unsupervisedcom/deepwork
```

Skip this entirely if `gh` is unavailable.

### 1. Get the Workflow Name

Ask: "What would you like to call this workflow? A rough name is fine - we can refine it later."

Wait for the response before continuing.

### 2. Check Browser Access

If the workflow may require websites and browser/MCP web tools are unavailable, ask whether website access is needed. If yes, tell the user which browser or MCP setup is available in their Pi environment and wait for confirmation.

### 3. Hand Off to the User

Output:

Got it - recording workflow: **{workflow_name}**

**Go ahead and do your workflow using Pi like you normally would.** Tell me each step - I'll do the work and keep track of what we do together.

When you're happy with the results, run `/deepwork learn` and I'll turn this session into a repeatable DeepWork workflow.

### 4. Clarify Non-Obvious Actions

Ask for reasoning when the user removes, skips, reorders, filters, or makes a domain judgment without explaining why. Keep the question short and use the answer to generalize the future workflow.

Do not ask when the instruction is already repeatable, the reasoning is obvious, or the user already explained it.

### 5. Catch the End

If the user signals they are done without running `/deepwork learn`, ask whether they want to turn the workflow into a repeatable DeepWork job now. If yes, invoke `/deepwork learn`.
