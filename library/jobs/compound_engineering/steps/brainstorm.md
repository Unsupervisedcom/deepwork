# Brainstorm Feature

Explore requirements and approaches through collaborative dialogue before planning.

## Purpose

Brainstorming helps answer **WHAT** to build through collaborative dialogue. It precedes the Plan step, which answers **HOW** to build it.

Use this step when:
- The feature is unclear or ambiguous
- Multiple valid approaches exist
- Stakeholders need alignment
- The scope needs refinement

Skip this step when:
- Requirements are already specific and detailed
- Following an established pattern
- Implementing a well-defined bug fix

## Input

**Feature Idea**: `{{feature_idea}}`

If no feature idea is provided, ask the user:
> "What would you like to explore? Please describe the feature, problem, or improvement you're thinking about."

Do not proceed until you have a clear feature description.

## Execution Flow

### Phase 0: Assess Clarity

First, evaluate if brainstorming is even needed:

**Clear requirements indicators:**
- Specific acceptance criteria already provided
- Referenced existing patterns to follow
- Exact expected behavior described
- Well-constrained scope

**If requirements seem clear**, suggest:
> "Your requirements seem detailed enough to proceed directly to planning. Should we skip to the Plan step, or would you like to explore the idea further?"

### Phase 1: Understand the Idea

#### 1.1 Quick Codebase Research

Before asking questions, scan the codebase for context:

```bash
# Look for similar features or patterns
grep -r "relevant_keyword" --include="*.{rb,py,ts,js}" -l | head -10

# Check for existing documentation
ls docs/ 2>/dev/null
cat CLAUDE.md 2>/dev/null | head -50
```

Focus on: similar features, established patterns, technology choices already made.

#### 1.2 Collaborative Dialogue

Ask clarifying questions **one at a time**. Guidelines:

1. **Start broad, then narrow**
   - Purpose: "What problem does this solve for users?"
   - Users: "Who will use this feature?"
   - Constraints: "Are there performance/security requirements?"
   - Edge cases: "What should happen when X?"

2. **Prefer multiple choice when natural**
   > "How should we handle authentication?"
   > 1. Use existing session auth
   > 2. Add API key support
   > 3. Both options

3. **Validate assumptions explicitly**
   > "I'm assuming we need to support mobile. Is that correct?"

4. **Ask about success criteria**
   > "How will we know this feature is working well?"

**Exit condition**: Continue until:
- The idea is clear and well-defined, OR
- User says "proceed" or "that's enough"

### Phase 2: Explore Approaches

Based on research and conversation, propose **2-3 concrete approaches**.

For each approach:
1. Brief description (2-3 sentences)
2. Pros and cons
3. When it's best suited

**Lead with your recommendation** and explain why. Apply YAGNI - prefer simpler solutions that solve the immediate problem.

Example format:
```markdown
## Approach Options

### Recommended: Simple Service Object
Add a single service class that handles the core logic.

**Pros**: Simple, easy to test, follows existing patterns
**Cons**: May need refactoring if scope grows significantly
**Best for**: Features with clear, bounded scope

### Alternative: Event-Driven
Use background jobs with event publishing.

**Pros**: Scalable, decoupled, supports async processing
**Cons**: More complex, harder to debug, may be overkill
**Best for**: Features needing high throughput or fan-out

Which approach do you prefer?
```

### Phase 3: Capture the Design

Write a brainstorm document:

**Path**: `docs/brainstorms/YYYY-MM-DD-[topic]-brainstorm.md`

**Structure**:
```markdown
---
topic: [feature name]
date: YYYY-MM-DD
status: ready-for-planning
participants: [who was involved]
---

# [Feature Name] Brainstorm

## What We're Building
[2-3 sentence summary of the feature]

## Why This Approach
[Chosen approach and rationale for selection]

## Key Decisions
- [Decision 1]: [Rationale]
- [Decision 2]: [Rationale]
- [Decision 3]: [Rationale]

## Open Questions
- [ ] [Question that needs resolution during planning]
- [ ] [Another open question]

## Next Steps
Ready for `/compound_engineering.plan`
```

Ensure the `docs/brainstorms/` directory exists:
```bash
mkdir -p docs/brainstorms
```

### Phase 4: Handoff

Present next steps:

> "Brainstorm captured at `docs/brainstorms/[filename]`. What would you like to do?"
> 1. **Proceed to planning** - Run the Plan step (will use this brainstorm)
> 2. **Refine further** - Continue exploring
> 3. **Done for now** - Return later

## Important Guidelines

- **Stay focused on WHAT, not HOW** - Implementation details belong in the plan
- **Ask one question at a time** - Don't overwhelm with multiple questions
- **Apply YAGNI** - Prefer simpler approaches; avoid speculative features
- **Keep outputs concise** - 200-300 words per section maximum
- **NEVER CODE** - This step is for exploration and documentation only

## Output

When complete, display:

```
Brainstorm complete!

Document: docs/brainstorms/YYYY-MM-DD-[topic]-brainstorm.md

Key decisions:
- [Decision 1]
- [Decision 2]

Open questions:
- [Any unresolved questions]

Next: Run the Plan step when ready to create implementation plan.
```
