# Document Learnings

## Objective

Capture solutions and learnings while context is fresh, creating searchable documentation for future reference.

## Task

Document a recently solved problem or completed feature in a structured format that makes it easy for future engineers (including AI assistants) to find and apply the solution.

**Philosophy**: Knowledge compounds when captured. A problem solved once should never need to be solved from scratch again. This step converts ephemeral context into permanent institutional knowledge.

### When to Use This Step

Run this step when:
- You just fixed a tricky bug
- You solved a problem after significant debugging
- You discovered a non-obvious solution
- You learned something that would help others
- A feature implementation had unexpected challenges
- You found a pattern worth documenting

**Trigger phrases** (if you hear these, suggest this step):
- "That worked!"
- "Finally fixed it"
- "The problem was..."
- "Turns out the issue was..."
- "I wish I'd known..."

### Phase 1: Capture Context

While the context is fresh, gather:

1. **Problem Description**
   - What was the symptom observed?
   - What was the expected vs actual behavior?
   - When/where did it occur?

2. **Investigation Path**
   - What did you try that didn't work?
   - What led you to the solution?
   - What was the debugging process?

3. **Root Cause**
   - What was actually wrong?
   - Why did it happen?
   - What made it non-obvious?

4. **Solution**
   - What fixed it?
   - Why does this fix work?
   - Are there alternative solutions?

5. **Prevention**
   - How can this be prevented in the future?
   - Should there be a test for this?
   - Should there be a lint rule or guard?

### Phase 2: Categorize the Learning

Assign the documentation to an appropriate category:

| Category | Use For |
|----------|---------|
| `build-errors` | Compilation, bundling, dependency issues |
| `test-failures` | Test flakiness, mocking issues, test setup |
| `runtime-errors` | Exceptions, crashes, unexpected behavior |
| `performance-issues` | Slow queries, memory leaks, bottlenecks |
| `database-issues` | Migrations, queries, data integrity |
| `security-issues` | Vulnerabilities, auth problems, data exposure |
| `ui-bugs` | Visual issues, interaction problems, layout |
| `integration-issues` | API problems, service communication |
| `logic-errors` | Business logic bugs, edge cases |
| `configuration` | Environment, settings, deployment |
| `patterns` | Useful patterns, best practices |
| `anti-patterns` | Things to avoid, common mistakes |

### Phase 3: Create Documentation

Create a markdown file in `docs/solutions/[category]/`:

```markdown
---
title: [Brief descriptive title]
category: [category from above]
date: YYYY-MM-DD
tags: [relevant, searchable, keywords]
related: [links to related solutions if any]
---

# [Title]

## Problem

### Symptoms
[What was observed - error messages, unexpected behavior]

### Context
[When/where this occurred - specific conditions]

### Expected Behavior
[What should have happened]

### Actual Behavior
[What actually happened]

## Investigation

### What Didn't Work
1. [Approach tried and why it failed]
2. [Another approach and why it failed]

### What Led to the Solution
[The debugging process, the "aha" moment]

## Root Cause

[Clear explanation of why this happened]

## Solution

### The Fix
[Step-by-step solution]

```[language]
// Code example if applicable
```

### Why This Works
[Explanation of why the solution addresses the root cause]

### Alternative Solutions
[Other approaches that could work, with trade-offs]

## Prevention

### How to Avoid This
- [Preventive measure 1]
- [Preventive measure 2]

### Suggested Tests/Guards
```[language]
// Test or guard code if applicable
```

## Related Resources
- [Link to relevant documentation]
- [Link to related issue or PR]

---
*Documented via Compound Engineering methodology*
```

### Phase 4: File the Documentation

1. **Create the Directory** (if needed)
   ```bash
   mkdir -p docs/solutions/[category]
   ```

2. **Choose a Filename**
   - Use kebab-case: `descriptive-name.md`
   - Be specific: `postgres-connection-pool-exhaustion.md` not `db-issue.md`

3. **Save the File**
   - Path: `docs/solutions/[category]/[filename].md`

### Phase 5: Cross-Reference

1. **Check for Related Issues**
   - Search for similar problems in `docs/solutions/`
   - Link to related solutions in the "related" frontmatter

2. **Pattern Detection**
   - If this is the 3rd+ similar issue, consider adding to a `patterns` or `anti-patterns` doc
   - Escalate recurring issues to project documentation

3. **Notify if Critical**
   - If this is a critical pattern everyone should know, mention it to the user
   - Suggest adding to onboarding docs or required reading

## Example Dialog

```
User: Finally fixed that notification bug! The WebSocket was disconnecting because we weren't handling reconnection properly.

Claude: Great! Let's capture this learning while the context is fresh. I'll document this solution.

[Asks clarifying questions to fill gaps]

What were the symptoms you observed?

User: Notifications would stop working after about 30 minutes. Users had to refresh to get them again.

Claude: And what led you to discover it was a reconnection issue?

User: I noticed in the network tab that the WebSocket was closing with code 1006, which is an abnormal closure. Then I saw we had no reconnection logic.

Claude: Got it. Let me create the documentation.

[Creates file]

# Documentation Created

**File**: docs/solutions/integration-issues/websocket-reconnection-notifications.md

**Summary**:
- Problem: Notifications stop after ~30 minutes
- Root Cause: WebSocket abnormal closure (1006) with no reconnection logic
- Solution: Added exponential backoff reconnection with max retries
- Prevention: Added automated test that simulates connection drop

**Tags**: websocket, notifications, reconnection, real-time

I've also linked this to a related solution:
- `docs/solutions/integration-issues/websocket-heartbeat-timeout.md` (related connection issue)

This is the second WebSocket-related issue this month. Would you like me to:
1. Create a general "WebSocket Best Practices" pattern document?
2. Add this to the team's required reading?
3. Just keep this individual solution?

User: Create the best practices doc

Claude: [Creates docs/solutions/patterns/websocket-best-practices.md]

Created! This consolidates learnings from both WebSocket issues into a reusable reference.
```

## Quality Criteria

- Problem is clearly described with symptoms
- Root cause is identified and explained
- Solution is documented step-by-step
- Documentation is filed in the appropriate category
- Tags make the documentation searchable
- Prevention strategies are documented

## Context

This is the knowledge-capture step in the Compound Engineering cycle. It transforms temporary debugging context into permanent searchable documentation.

The compounding effect: Every documented solution makes the next similar problem faster to solve. Over time, the `docs/solutions/` directory becomes a powerful institutional knowledge base.

This step works best when done immediately after solving a problem, while all the context is still in memory. Waiting even a day causes important details to be lost.
