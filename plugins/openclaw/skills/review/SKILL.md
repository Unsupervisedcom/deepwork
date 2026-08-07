---
name: review
description: "Run DeepWork Reviews in OpenClaw using `.deepreview` rules"
---

# DeepWork Review

Run project reviews using DeepWork review rules.

## How to Run

1. Call `deepwork__get_configured_reviews` first and summarize the active rules for the user.
2. Call `deepwork__get_review_instructions`.
3. Launch the returned review tasks as parallel OpenClaw sub-agents with `sessions_spawn`.
4. Spawn all requested review sub-agents before waiting, keep instruction paths workspace-relative, and do not set `timeoutSeconds` unless you must use `0`.
5. Collect the findings and apply obvious low-risk fixes immediately.
6. For anything with tradeoffs, summarize the finding and ask the user how they want to proceed.

## Iterate

After making changes:

1. Run `deepwork__get_review_instructions` again.
2. Re-run only the review tasks that still matter, unless the change set was large enough to justify a full rerun.
3. Repeat until the review run is clean or the user explicitly chooses to stop.
