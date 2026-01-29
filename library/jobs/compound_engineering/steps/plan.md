# Create Implementation Plan

Transform feature descriptions, bug reports, or improvement ideas into well-structured implementation plans.

## Purpose

Planning is the foundation of compound engineering. A good plan:
- Captures research and context for future reference
- References existing patterns in the codebase
- Provides clear acceptance criteria
- Enables efficient execution during the Work step

**Philosophy**: 80% of effort goes into planning and review, 20% into execution.

## Input

**Feature Description**: `{{feature_description}}`

If no description is provided, ask:
> "What would you like to plan? Please describe the feature, bug fix, or improvement."

Do not proceed until you have a clear description.

## Execution Flow

### Phase 0: Check for Brainstorm

Before asking questions, look for recent brainstorm documents:

```bash
ls -la docs/brainstorms/*.md 2>/dev/null | head -10
```

**If a relevant brainstorm exists** (matches topic, created within 14 days):
1. Read the brainstorm document
2. Announce: "Found brainstorm from [date]: [topic]. Using as context for planning."
3. Skip to Phase 1 - the brainstorm already answered WHAT to build

**If no brainstorm found**, optionally run Phase 0.5 (Idea Refinement):
- Ask clarifying questions one at a time to understand the idea
- Focus on: purpose, constraints, success criteria
- Skip if the description is already detailed

### Phase 1: Local Research (Always Run)

Research the codebase to understand existing patterns:

```bash
# Find similar implementations
grep -r "related_keyword" --include="*.{rb,py,ts,js}" -l | head -10

# Check project conventions
cat CLAUDE.md 2>/dev/null
cat .github/CONTRIBUTING.md 2>/dev/null

# Look for existing documentation
ls docs/solutions/ 2>/dev/null
```

**What to capture**:
- Existing patterns to follow
- CLAUDE.md guidance
- Related files and their locations
- Previous solutions to similar problems (from docs/solutions/)

### Phase 1.5: Research Decision

Based on the findings, decide if external research is needed:

**Always research** for:
- Security-sensitive features (auth, payments, data privacy)
- External API integrations
- Performance-critical code paths

**Skip external research** when:
- Strong local patterns exist
- CLAUDE.md provides guidance
- User knows what they want

Announce your decision:
> "Your codebase has solid patterns for this. Proceeding without external research."
>
> OR
>
> "This involves [security/external APIs/etc], so I'll research best practices first."

### Phase 1.5b: External Research (If Needed)

When external research is valuable:

```bash
# Search for best practices
# Use web search for "[technology] best practices 2026"
# Check official documentation
```

Focus on:
- Official documentation recommendations
- Security considerations
- Common pitfalls to avoid

### Phase 2: Choose Detail Level

Select the appropriate level based on complexity:

#### MINIMAL (Quick Issue)
**Best for**: Simple bugs, small improvements, clear features

Includes:
- Problem statement
- Basic acceptance criteria
- Essential context

#### MORE (Standard Issue) - **Default**
**Best for**: Most features, complex bugs, team collaboration

Includes everything from MINIMAL plus:
- Detailed background and motivation
- Technical considerations
- Success metrics
- Dependencies and risks

#### A LOT (Comprehensive Issue)
**Best for**: Major features, architectural changes, complex integrations

Includes everything from MORE plus:
- Implementation phases
- Alternative approaches considered
- Resource requirements
- Risk mitigation strategies

### Phase 3: Create the Plan

**Filename format**: `docs/plans/YYYY-MM-DD-[type]-[descriptive-name]-plan.md`

Examples:
- `docs/plans/2026-01-29-feat-user-authentication-flow-plan.md`
- `docs/plans/2026-01-29-fix-checkout-race-condition-plan.md`

**Type prefixes**:
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code improvement

Ensure directory exists:
```bash
mkdir -p docs/plans
```

**Standard Template** (MORE level):

```markdown
---
title: [Issue Title]
type: [feat|fix|refactor]
date: YYYY-MM-DD
status: ready-for-work
---

# [Issue Title]

## Overview
[Comprehensive description of what we're building and why]

## Problem Statement / Motivation
[Why this matters, what pain it solves]

## Proposed Solution
[High-level approach, not implementation details]

## Technical Considerations
- Architecture impacts
- Performance implications
- Security considerations

## Acceptance Criteria
- [ ] Detailed requirement 1
- [ ] Detailed requirement 2
- [ ] Testing requirements

## Success Metrics
[How we measure success - quantitative if possible]

## Dependencies & Risks
[What could block or complicate this]

## References & Research
### Internal References
- Similar implementations: [file_path:line_number]
- Related code: [file_path]

### External References
- Documentation: [url]
- Best practices: [url]

## Implementation Notes
[Key patterns to follow, gotchas to avoid]
```

### Phase 4: Post-Generation Options

After writing the plan, present options:

> "Plan ready at `docs/plans/[filename]`. What would you like to do next?"
> 1. **Start Work** - Begin implementing this plan
> 2. **Review Plan** - Get feedback on the plan first
> 3. **Create Issue** - Create issue in project tracker (GitHub/Linear)
> 4. **Simplify** - Reduce detail level
> 5. **Other** - Specify what you need

Handle each option:
- **Start Work** -> Proceed to Work step
- **Review Plan** -> Quick review of plan quality
- **Create Issue** -> Use `gh issue create --title "[type]: [title]" --body-file [plan_path]`
- **Simplify** -> Ask what to simplify, regenerate

## Important Guidelines

- **Reference real files** - Include actual file paths with line numbers
- **Use code examples** - Show patterns from the codebase
- **Keep acceptance criteria testable** - Each should be verifiable
- **Include ERD diagrams** - Use Mermaid for data model changes
- **NEVER CODE** - This step produces documentation, not implementation

## Output

When complete, display:

```
Plan created!

File: docs/plans/YYYY-MM-DD-[type]-[name]-plan.md
Detail level: [MINIMAL|MORE|A LOT]

Key sections:
- Overview: [1-sentence summary]
- Acceptance Criteria: [count] items
- References: [count] internal, [count] external

Next steps:
1. Start Work - Begin implementation
2. Review Plan - Get feedback first
3. Create Issue - Track in GitHub/Linear
```
