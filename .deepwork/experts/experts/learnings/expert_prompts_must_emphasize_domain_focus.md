---
name: Expert prompts must emphasize domain focus
last_updated: 2026-02-01
summarized_result: |
  When invoking experts for tasks like PR review, prompts must explicitly tell
  experts to ONLY comment on their domain and not provide generic feedback.
  Without this, experts provide overlapping generic reviews instead of unique
  specialized perspectives.
---

## Context

During a PR review using the `/review_pr` job, both the `deepwork-jobs` and `experts` experts were invoked to review changes to the experts system implementation. The expectation was that each expert would bring their unique domain knowledge to identify issues that generalist reviewers might miss.

## Problem

Both experts provided similar generic code review feedback. They identified the same issues (redundant exception handling, unused variables) rather than focusing on aspects specific to their domains:

- The `deepwork-jobs` expert should have focused on how the experts system integrates with jobs, skill generation patterns, and hook systems
- The `experts` expert should have focused on expert.yml schema design, topic/learning structure, and evolution strategies

Instead, both provided overlapping feedback on general code quality issues.

## Resolution

Updated the expert prompts in the `review_pr` job steps to explicitly emphasize domain focus:

```
IMPORTANT: Only comment on aspects that fall within your area of expertise.
Do not provide general code review feedback on things outside your domain -
other experts will cover those areas. Use your specialized knowledge to
identify issues that a generalist reviewer might miss.
```

Also added:
- "Your domain: [brief description from discovery_description]" to remind experts of their focus
- Request for feedback "from your expert perspective" throughout the prompt
- Quality criteria including "Feedback is focused on each expert's specific domain of expertise"

## Key Takeaway

When designing job steps that invoke experts, the prompt must explicitly constrain experts to their domain. Without this, experts default to providing generic assistance rather than specialized insight. The value of the experts system comes from each expert contributing unique perspective - overlapping generic reviews wastes the multi-expert approach.
