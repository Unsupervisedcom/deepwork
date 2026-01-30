---
name: Keep Experts Focused
last_updated: 2025-01-30
summarized_result: |
  Broad experts like "Rails" or "JavaScript" become too large and unfocused.
  Better to create specific experts like "Rails ActiveJob" or "React Hooks".
---

## Context

When initially designing the experts system, we considered creating broad,
comprehensive experts that would cover entire technology stacks.

## Investigation

Testing showed that broad experts:
- Generated overwhelming amounts of content
- Struggled to provide specific, actionable guidance
- Made it difficult to know which expert to invoke
- Led to duplication across multiple broad experts

## Resolution

Adopted a principle of focused experts with clear boundaries:
- Each expert covers a specific domain or technology subset
- The discovery_description clearly indicates scope
- Topics dive deep rather than wide
- Learnings capture domain-specific insights

## Key Takeaway

An expert should be narrow enough that you can articulate its scope in 1-2
sentences. If you can't, it's probably too broad.
