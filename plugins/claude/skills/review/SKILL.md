---
name: review
description: "Run DeepWork Reviews on the current branch — review changed files using .deepreview rules"
---

# DeepWork Review

Run automated code reviews on the current branch based on `.deepreview` config files.

## Routing

If the user is asking to **configure, create, or modify** review rules (e.g., "add a security review", "set up reviews for our API layer"), use the `configure_reviews` skill instead. This skill is for **running** reviews.

## How to Run

1. Run the review command:
   ```bash
   uvx deepwork review --instructions-for claude
   ```
   If the user asked to review specific files, pass them with `--files`:
   ```bash
   uvx deepwork review --instructions-for claude --files src/app.py --files src/lib.py
   ```
   For a glob pattern of files to review, expand it via the shell and pipe in:
   ```bash
   printf '%s\n' src/**/*.py | uvx deepwork review --instructions-for claude
   ```
2. The output will list review tasks to invoke in parallel. Each task has a Name, Agent, and prompt file. Launch all of them as parallel Task agents, passing each task's prompt file as the instruction.
3. Collect the results from all review agents.

## Acting on Results

For each finding from the review agents:

- **Obviously good changes with no downsides** (e.g., fixing a typo, removing an unused import, adding a missing null check): make the change immediately without asking.
- **Everything else** (refactors, style changes, architectural suggestions, anything with trade-offs): use AskUserQuestion to present the finding and ask the user whether to act on it. Be concise — quote the key finding and proposed change, don't dump the full review.

## Iterate

After making any changes, run the review again:

```bash
uvx deepwork review --instructions-for claude
```

Repeat the full cycle (run → act on results → run again) until a clean run produces no further actionable findings. Note that you don't have to run EVERY task the above outputs after the first time - you can just run the ones that match up to ones that had feedback last time. If you made very large changes, it may be a good idea to run the full reviews set.
