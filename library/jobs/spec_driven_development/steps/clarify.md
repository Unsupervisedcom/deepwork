# Clarify Specification

## Objective

Resolve ambiguities, fill gaps, and validate completeness of the specification through systematic questioning. The goal is to ensure the spec is detailed enough for technical planning.

## Task

Review the existing specification, identify underspecified areas, and ask structured questions to resolve them. Update the spec.md with clarifications.

**Important**: Ask questions one at a time - present a question, wait for the user's response, then ask the next. Do not output all questions as a list.

**Critical**: This step refines requirements, not implementation. Do not add code examples or technical solutions. Keep clarifications focused on user needs, acceptance criteria, and behavior - not how things will be coded.

### Prerequisites

Before starting, verify:
1. The specification exists at `specs/[feature-name]/spec.md`
2. Read the specification thoroughly

If no specification exists, inform the user they should run `/spec_driven_development.specify` first.

### Step 1: Identify the Feature

Ask the user which feature specification to clarify:

```
Which feature specification would you like to clarify?
```

If they provide a name, look for `specs/[feature-name]/spec.md`.

### Step 2: Analyze for Ambiguities

Read the specification and identify gaps in these categories:

1. **Underspecified User Stories**
   - Stories missing acceptance criteria
   - Vague or unmeasurable criteria
   - Missing edge case definitions

2. **Unclear Requirements**
   - Requirements with ambiguous language ("fast", "user-friendly", "secure")
   - Missing quantitative thresholds
   - Undefined terms or jargon

3. **Missing Scenarios**
   - Error handling not defined
   - Edge cases not covered
   - Multi-user scenarios not addressed

4. **Integration Gaps**
   - Undefined interactions with other features
   - Missing data flow definitions
   - Unclear state transitions

5. **Open Questions**
   - Any questions listed in the "Open Questions" section
   - Implicit assumptions that need validation

### Step 3: Systematic Clarification

For each ambiguity identified, ask structured questions:

**Format your questions systematically:**

```
I've identified [N] areas that need clarification in your specification.

**Ambiguity 1: [Category] - [Brief Description]**

The spec says: "[Quote from spec]"

This is ambiguous because: [Explanation]

Question: [Specific clarifying question]

Options:
- [Option A with implications]
- [Option B with implications]
- [Other - user can specify]
```

**Question best practices:**
- One topic per question
- Provide options when possible
- Explain implications of each option
- Reference specific parts of the spec

### Step 4: Validate Edge Cases

For each user story, ensure edge cases are covered:

1. **What happens if the user...**
   - Provides invalid input?
   - Cancels midway?
   - Loses connection?
   - Times out?

2. **What happens when...**
   - The system is under load?
   - Required data is missing?
   - External services are unavailable?

3. **What about...**
   - First-time users vs returning users?
   - Different user permission levels?
   - Concurrent access scenarios?

### Step 5: Update the Specification

After gathering clarifications, update `specs/[feature-name]/spec.md`:

1. **Add a Clarifications section:**
   ```markdown
   ## Clarifications

   ### [Date] Clarification Session

   **Q1: [Original question]**
   A: [Answer received]
   Impact: [How this affects the spec]

   **Q2: [Original question]**
   A: [Answer received]
   Impact: [How this affects the spec]
   ```

2. **Update affected sections:**
   - Refine vague acceptance criteria with specific thresholds
   - Add missing edge cases to user stories
   - Update non-functional requirements with concrete numbers
   - Remove or resolve open questions

3. **Mark resolved questions:**
   - Move resolved items from "Open Questions" to "Clarifications"
   - Add any new questions discovered during clarification

### Step 6: Validate Acceptance Checklist

Create or update an acceptance checklist:

```markdown
## Acceptance Checklist

### User Stories
- [ ] All stories have 3+ acceptance criteria
- [ ] All criteria are testable/measurable
- [ ] Edge cases are documented

### Requirements
- [ ] Performance thresholds defined (response times, throughput)
- [ ] Security requirements are specific
- [ ] Accessibility standards identified

### Scope
- [ ] In-scope items are detailed
- [ ] Out-of-scope items are explicit
- [ ] Assumptions are documented

### Completeness
- [ ] No open questions remain
- [ ] All ambiguities resolved
- [ ] Ready for technical planning
```

## Example Dialog

```
Claude: I'll help clarify the specification. Which feature would you like to work on?

User: user-authentication

Claude: Let me review the spec at `specs/user-authentication/spec.md`...

[Reads specification]

I've identified 4 areas that need clarification:

**Ambiguity 1: Performance - "Quick signup flow"**

The spec says: "The whole flow should take under a minute"

This is ambiguous because: It's unclear if this refers to user time, system response time,
or includes email verification.

What does "under a minute" mean for the signup flow?

[Uses AskUserQuestion with options:
- User can complete form in under 1 minute (not including email verification)
- System processes signup in under 1 minute (including sending verification email)
- End-to-end including email verification click
- Other]

User: User can complete form in under 1 minute, not including verification

Claude: Got it. I'll update the spec to say:
"Users can complete the signup form within 60 seconds. Email verification is asynchronous
and not included in this timing."

**Ambiguity 2: Security - "Email verification required"**

The spec doesn't define what happens if verification isn't completed.

What should happen to unverified accounts?

[Uses AskUserQuestion with options:
- Allow limited access for 24 hours, then restrict
- No access until verified
- Full access but with reminder prompts
- Other]

User: Allow limited access for 24 hours

Claude: What does "limited access" mean? What can unverified users do vs not do?

[Continues clarification...]

After resolving all ambiguities:

✓ Specification clarified!

**Updates made to** specs/user-authentication/spec.md:
- Added 4 clarifications with answers
- Updated 3 acceptance criteria with specific thresholds
- Added 5 edge cases to user stories
- Resolved all open questions

**Acceptance checklist:** All items complete ✓

**Next step:**
Run `/spec_driven_development.plan` to create the technical implementation plan.
```

## Output Format

### Updated specs/[feature-name]/spec.md

The specification file updated with:
- Clarifications section with Q&A
- Refined acceptance criteria
- Additional edge cases
- Resolved open questions
- Acceptance checklist (all items checked)

**Location**: `specs/[feature-name]/spec.md` (same file, updated)

After updating the file:
1. Summarize the clarifications made
2. Confirm the acceptance checklist is complete
3. Tell the user to run `/spec_driven_development.plan` to create the technical plan

## Quality Criteria

- All ambiguities in the spec were identified
- Structured questions were asked for each ambiguity
- Answers are documented in Clarifications section
- Acceptance criteria now have specific, measurable thresholds
- Edge cases are comprehensively covered
- Open questions are resolved
- Acceptance checklist is complete
- Spec is ready for technical planning
- **No implementation code**: Clarifications describe behavior, not code
