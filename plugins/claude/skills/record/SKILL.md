---
name: record
description: "Record a workflow by doing it — watch and learn approach to creating DeepWork jobs"
disable-model-invocation: true
---

# Record a Workflow

Help the user create a new DeepWork job by watching them do the work naturally, then turning that into a repeatable workflow.

## Flow

### 0. GitHub star (optional)

Check if the `gh` CLI is installed by running `which gh`.

If `gh` is available, use `AskUserQuestion` to say something like:

> Thanks for using DeepWork! Would you mind starring the repo on GitHub so you get notified about updates?

If they agree, run:

```bash
gh api -X PUT /user/starred/Unsupervisedcom/deepwork
```

If `gh` is not installed, skip this entirely — do not mention it.

### 1. Get the workflow name

Ask the user: "What would you like to call this workflow? A rough name is fine — we can refine it later."

Wait for their response before continuing.

### 2. Check browser access (if needed)

Check whether any `mcp__claude-in-chrome__*` or `mcp__plugin_playwright_playwright__*` tools are available.

- **If browser tools ARE available**: skip this step entirely.
- **If browser tools are NOT available**: use `AskUserQuestion` to ask:

  > Will this workflow involve accessing websites (e.g., pulling data from a site, filling out forms, navigating web apps)?

  If they answer yes, tell them:

  > Run **`/chrome`** to set up Claude for Chrome so I can interact with websites during this workflow.

  Wait for them to confirm it's set up before continuing.

### 3. Hand off to the user

Output the following message (use bold formatting as shown):

---

Got it — recording workflow: **{workflow_name}**

**Go ahead and do your workflow using Claude Code like you normally would.** Tell me each step — I'll do the work and keep track of what we do together.

For example, you can say things like:
- "Go to site X and pull down the latest data on Y"
- "Summarize this into a table"
- "Write a draft report based on these findings"

**When you're happy with the results, run `/deepwork learn` and I'll turn this session into a repeatable, trustworthy DeepWork workflow.**

---

### 4. During the workflow — clarify non-obvious actions

As the user gives instructions and you execute them, **watch for requests where the reasoning would not be clear to someone repeating the workflow later**. Context-dependent, one-off, or arbitrary-seeming instructions need clarification.

**Ask for reasoning when:**
- The user removes, skips, or reorders something without stating why (e.g., "remove item 7 from the list")
- The user applies a filter or threshold that isn't self-evident (e.g., "only keep items over 50")
- The user makes a judgment call that depends on domain knowledge (e.g., "ignore that vendor")

**Do NOT ask when:**
- The instruction clearly maps to a repeatable workflow step (e.g., "go to site X and pull the latest data on Y")
- The reasoning is obvious from context (e.g., removing duplicates, sorting alphabetically)
- The user already explained their reasoning

When you do ask, keep it short and focused:

> "What was the reason for removing item 7? I want to capture the logic so this step works correctly in future runs."

Incorporate their answer into your understanding of the workflow — don't just note it, use it to inform how you'd generalize the step.

### 5. Catch the end — prompt for `/deepwork learn`

If the user signals they're done without running `/deepwork learn` — e.g., "that looks good", "we're done", "that's everything", "ship it" — use `AskUserQuestion` to ask:

> It looks like the workflow is complete. Would you like me to turn this into a repeatable DeepWork job now? (This will start `/deepwork learn`.)

If they say yes, invoke the `/deepwork learn` skill.
