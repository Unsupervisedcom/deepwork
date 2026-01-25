# Create Specification

## Objective

Create a functional specification (`spec.md`) that defines what the feature should do and why, using user stories and acceptance criteria, without making technology or implementation decisions.

## Task

Guide the user through creating a comprehensive specification by asking structured questions about their feature requirements, user needs, and success criteria.

**Important**: Use the AskUserQuestion tool to ask structured questions when gathering information from the user.

**Key Principle**: This step focuses entirely on the **"what"** and **"why"** - never the **"how"**. Technology choices and implementation details belong in the planning step.

**Critical**: Do not include any code examples, implementation snippets, or technical solutions. The specification describes user needs and acceptance criteria in plain language. Code is written only in the implement step.

### Prerequisites

Before starting, verify:
1. The constitution exists at `[docs_folder]/constitution.md`
2. Read the constitution to understand project principles and priorities

If the constitution doesn't exist, inform the user they should run `/spec_driven_development.constitution` first.

### Step 1: Define the Feature

Ask structured questions to understand the feature:

1. **What is this feature called?**
   - Get a concise, descriptive name
   - Convert to lowercase with hyphens for the directory name (e.g., "User Authentication" → "user-authentication")

2. **What problem does this feature solve?**
   - What user pain point does it address?
   - What business value does it provide?
   - Why is this feature needed now?

3. **Who are the users of this feature?**
   - Primary user personas
   - Secondary stakeholders
   - Admin or support considerations

### Step 2: Gather User Stories

For each user type identified, ask structured questions to create user stories:

1. **What does [user type] need to do?**
   - What's their goal?
   - What triggers them to use this feature?
   - What does success look like for them?

2. **Create user stories in standard format:**
   ```
   As a [user type]
   I want to [action]
   So that [benefit/goal]
   ```

3. **Define acceptance criteria for each story:**
   - What must be true for this story to be "done"?
   - What are the happy path scenarios?
   - What are the edge cases?

### Step 3: Define Requirements

Gather detailed requirements:

1. **Functional Requirements**
   - What actions must users be able to take?
   - What data must be captured or displayed?
   - What workflows must be supported?

2. **Non-Functional Requirements**
   - Performance: What are acceptable response times?
   - Security: What data needs protection? What access controls?
   - Accessibility: What accessibility standards apply?
   - Scalability: What load must this support?

3. **Constraints**
   - What are the boundaries of this feature?
   - What is explicitly out of scope?
   - What dependencies exist on other features?

### Step 4: Define Scope Boundaries

Clearly establish what's in and out of scope:

1. **In Scope**
   - List all capabilities included in this feature
   - Be specific about what will be delivered

2. **Out of Scope**
   - Explicitly list what will NOT be included
   - Identify items that might be assumed but aren't part of this work
   - Note future enhancements that are deferred

3. **Assumptions**
   - What are we assuming to be true?
   - What dependencies must be in place?

### Step 5: Create the Specification File

**Create directory structure first:**
```bash
mkdir -p specs/[feature-name]
```

**Create the specification file** at `specs/[feature-name]/spec.md`:

```markdown
# [Feature Name] Specification

## Overview

### Problem Statement
[Description of the problem this feature solves]

### Business Value
[Why this feature matters to the business/users]

### Target Users
- **[User Type 1]**: [Description and needs]
- **[User Type 2]**: [Description and needs]

## User Stories

### US-1: [Story Title]

**As a** [user type]
**I want to** [action]
**So that** [benefit]

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

**Edge Cases:**
- [Edge case 1]: [Expected behavior]
- [Edge case 2]: [Expected behavior]

### US-2: [Story Title]
[Continue for each user story...]

## Requirements

### Functional Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-1 | [Requirement] | Must Have | |
| FR-2 | [Requirement] | Should Have | |

### Non-Functional Requirements

#### Performance
- [Performance requirement 1]
- [Performance requirement 2]

#### Security
- [Security requirement 1]
- [Security requirement 2]

#### Accessibility
- [Accessibility requirement 1]

## Scope

### In Scope
- [Capability 1]
- [Capability 2]

### Out of Scope
- [Excluded item 1]
- [Excluded item 2]

### Assumptions
- [Assumption 1]
- [Assumption 2]

### Dependencies
- [Dependency 1]
- [Dependency 2]

## Open Questions

[List any questions that need clarification before planning]

1. [Question 1]
2. [Question 2]
```

## Example Dialog

```
Claude: I'll help you create a specification for your new feature. Let me first check the
project constitution...

[Reads [docs_folder]/constitution.md]

Great, I see you're prioritizing code quality and security. Let's define your feature.

What feature are you building? Give me a name and brief description.

User: User authentication - allowing users to sign up and log in to our app

Claude: Perfect. I'll create this under `specs/user-authentication/`.

What problem does authentication solve for your users? Why do they need accounts?

User: Users need accounts to save their preferences and access their data across devices.

Claude: That makes sense. Who are the primary users of this authentication system?

[Uses AskUserQuestion with options: New users signing up, Returning users logging in,
Admins managing users, All of the above]

User: All of the above

Claude: Let's create user stories for each. Starting with new users signing up:

What's most important to a new user when creating an account?

User: Quick signup - ideally with email or social login. No lengthy forms.

Claude: Got it. Here's the user story I'd write:

**As a** new user
**I want to** sign up quickly using my email or social account
**So that** I can start using the app without friction

What would make this story "done"? What must work for you to accept it?

User: They need to be able to sign up with email/password or Google. Email verification
should be required. The whole flow should take under a minute.

Claude: Those are clear acceptance criteria. Now let's think about edge cases...

[Continues gathering information...]

✓ Specification created!

**File created:**
- specs/user-authentication/spec.md

**Open Questions:**
I noted 2 questions that need clarification before we can plan the implementation.

**Next step:**
Run `/spec_driven_development.clarify` to resolve open questions and finalize the spec.
```

## Validation Rules

Before creating the spec.md, ensure:
- Feature name is lowercase with hyphens
- All user stories follow "As a... I want... So that..." format
- Each story has at least 2 acceptance criteria
- In/out of scope sections are populated
- No technology or implementation details are included
- Open questions are documented

## Output Format

### specs/[feature-name]/spec.md

A markdown document containing:
- Overview (problem, value, users)
- User stories with acceptance criteria
- Functional and non-functional requirements
- Scope boundaries
- Open questions

**Location**: `specs/[feature-name]/spec.md`

After creating the file:
1. Summarize the key user stories
2. Highlight any open questions that need resolution
3. Tell the user to run `/spec_driven_development.clarify` to resolve ambiguities

## Quality Criteria

- Asked structured questions to understand user needs
- All user stories are in correct format
- Acceptance criteria are testable
- Non-functional requirements are captured
- Scope boundaries are clear
- **No implementation code**: Spec describes behavior in plain language, not code
- Constitution principles are respected
- File created in correct location
