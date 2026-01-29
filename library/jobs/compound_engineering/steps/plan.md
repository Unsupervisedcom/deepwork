# Create Implementation Plan

## Objective

Transform a feature idea or task description into a detailed, research-backed implementation plan that will guide systematic execution.

## Task

Work interactively with the user to refine their idea, research existing codebase patterns, optionally research external best practices, and produce a comprehensive implementation plan document.

**Philosophy**: Spend 80% of effort on planning to make the 20% execution smooth. A well-planned feature is easier to implement, review, and maintain.

### Phase 1: Idea Refinement

Start by understanding what the user wants to build. Ask clarifying questions to fill gaps in the requirement:

1. **Understand the Goal**
   - What problem does this solve?
   - Who is the user/customer?
   - What does success look like?

2. **Scope Definition**
   - What's in scope vs out of scope?
   - Are there related features that should be considered?
   - What are the constraints (time, technology, etc.)?

3. **Acceptance Criteria**
   - How will we know when it's done?
   - What are the must-have vs nice-to-have requirements?

Use the AskUserQuestion tool to gather this information interactively. Don't proceed until you have clear answers.

### Phase 2: Local Codebase Research

Before designing a solution, understand what already exists:

1. **Pattern Discovery**
   - Search for similar features in the codebase
   - Identify existing conventions (naming, structure, patterns)
   - Find reusable components or utilities

2. **Architecture Understanding**
   - Where does this feature fit in the existing architecture?
   - What components will need to be modified?
   - Are there existing abstractions to leverage?

3. **Test Pattern Analysis**
   - How are similar features tested?
   - What test utilities exist?
   - What's the expected test coverage?

**Use the Task tool** with `subagent_type: Explore` to research the codebase:

```
Prompt: "Search this codebase for patterns related to [feature]. Find:
1. Similar implementations we can learn from
2. Existing utilities or helpers we should reuse
3. Naming conventions and code structure patterns
4. Testing patterns used for similar features"
```

### Phase 3: Prior Learnings Check

Check if relevant learnings exist from previous work:

1. **Search docs/solutions/**
   - Look for related problem categories
   - Find solutions that might apply
   - Note any patterns or anti-patterns documented

2. **Incorporate Learnings**
   - Reference relevant prior solutions in the plan
   - Avoid previously-documented pitfalls
   - Reuse successful approaches

### Phase 4: External Research (Optional)

For complex or unfamiliar features, research best practices:

1. **Determine if Research is Needed**
   - Is this a well-understood pattern in the codebase? (Skip research)
   - Is this new territory involving security, performance, or complex integrations? (Do research)
   - Ask the user if uncertain

2. **Research Topics**
   - Best practices for this type of feature
   - Security considerations
   - Performance implications
   - Common pitfalls to avoid

**Use WebSearch** for external research when needed:

```
Query: "[framework] [feature type] best practices 2025"
```

### Phase 5: Create Implementation Plan

Produce a plan document with the following structure:

```markdown
# [Feature Name] Implementation Plan

**Date**: YYYY-MM-DD
**Type**: feature | bugfix | refactor | chore
**Status**: planned

## Summary
[One paragraph describing what this plan accomplishes]

## Background
[Context on why this feature is needed]

## Research Findings

### Codebase Patterns
- [Pattern 1]: [Where found and how to apply]
- [Pattern 2]: [Where found and how to apply]

### Prior Learnings Applied
- [Reference to docs/solutions/ if applicable]

### External Research (if performed)
- [Key findings and sources]

## Approach

### High-Level Design
[Description of the overall approach]

### Components to Modify
1. **[File/Component]**: [What changes needed]
2. **[File/Component]**: [What changes needed]

### New Components to Create
1. **[File/Component]**: [Purpose and location]

## Implementation Checklist

### Setup
- [ ] Create feature branch
- [ ] [Other setup tasks]

### Core Implementation
- [ ] [Task 1 - specific and actionable]
- [ ] [Task 2 - specific and actionable]
- [ ] [Task 3 - specific and actionable]

### Testing
- [ ] [Test task 1]
- [ ] [Test task 2]

### Documentation
- [ ] Update relevant documentation
- [ ] [Other doc tasks]

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | Low/Med/High | Low/Med/High | [How to mitigate] |

## Edge Cases
- [Edge case 1 and how to handle]
- [Edge case 2 and how to handle]

## Open Questions
- [ ] [Question 1 - resolve before implementing]
- [ ] [Question 2 - resolve before implementing]

---
*Plan created with Compound Engineering methodology*
```

### Phase 6: Save the Plan

1. **Create the plan file**
   - Path: `docs/plans/YYYY-MM-DD-[type]-[feature-name]-plan.md`
   - Ensure the `docs/plans/` directory exists

2. **Summarize for the user**
   - List the key decisions made
   - Highlight any open questions to resolve
   - Tell them to run `/compound_engineering.work` when ready to implement

## Example Dialog

```
User: I want to add a notification system for when users get new messages

Claude: I'll help you create an implementation plan for a notification system.
Let me ask a few clarifying questions first:

[Uses AskUserQuestion]
1. What types of notifications? (In-app, email, push, or combination?)
2. Should notifications be real-time or can they be slightly delayed?
3. Do users need to be able to configure their notification preferences?

User: In-app and email. Real-time for in-app, email can be batched. Yes, users should control preferences.

Claude: Got it. Let me research your codebase for existing patterns...

[Uses Task tool with Explore agent to research codebase]

I found some relevant patterns:
- You have an existing `EmailService` in `src/services/email.ts` we can extend
- WebSocket setup exists in `src/realtime/` for real-time features
- User preferences are stored in `users.preferences` JSON column

Let me check if there are any prior learnings...

[Reads docs/solutions/ directory]

Found a relevant solution: `docs/solutions/performance-issues/batch-email-processing.md`
documents a pattern for batching emails efficiently.

Based on this research, here's the implementation plan:

[Creates plan file]

Plan saved to: docs/plans/2025-01-29-feature-notification-system-plan.md

Key decisions:
- Extend existing EmailService for email notifications
- Use existing WebSocket infrastructure for real-time
- Follow the batch processing pattern from prior learnings
- Add new UserNotificationPreferences table

Open questions to resolve:
- [ ] What's the email batch interval? (suggested: every 15 minutes)

When you're ready, run `/compound_engineering.work` to start implementation.
```

## Quality Criteria

- Idea was refined through interactive questioning
- Codebase patterns were researched and documented
- Prior learnings were checked and incorporated if relevant
- Implementation approach is clear and specific
- Checklist contains concrete, actionable tasks
- Risks and edge cases are identified
- Plan file is saved to docs/plans/

## Context

This is the first step in the Compound Engineering cycle. A thorough plan makes the work step smoother and the review step faster. The plan also serves as documentation for future reference.

By researching the codebase and prior learnings before designing, we ensure consistency and avoid reinventing solutions to already-solved problems.
