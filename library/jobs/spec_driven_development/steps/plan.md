# Generate Technical Plan

## Objective

Create a comprehensive technical implementation plan that defines architecture, technology choices, data models, and API contracts. This is where "how" decisions are made, guided by the specification ("what") and constitution (principles).

## Task

Analyze the clarified specification and create detailed technical planning documents that will guide implementation.

**Important**: Ask questions one at a time - present a question, wait for the user's response, then ask the next. Do not output all questions as a list.

**Critical**: This step produces planning documents, NOT implementation code. Do not write actual code - that happens in the implement step. You may include:
- API contracts (endpoints, request/response schemas)
- Data model schemas (tables, fields, relationships)
- Architecture diagrams (text-based)
- Technology selection rationale

Do NOT include:
- Actual implementation code (functions, classes, logic)
- Code snippets showing "how to implement" something
- Sample implementations or starter code

### Prerequisites

Before starting, verify these files exist and read them:
1. `[docs_folder]/constitution.md` - Project principles and technology preferences
2. `specs/[feature-name]/spec.md` - Clarified specification with all requirements
3. `[docs_folder]/architecture.md` - Existing project architecture document (if present)

If the constitution or spec is missing, inform the user which step they need to complete first. The architecture document may not exist yet for new projects - that's okay, you'll create it.

### Step 1: Identify the Feature

Ask the user which feature to plan:

```
Which feature would you like to create a technical plan for?
```

If they provide a name, verify `specs/[feature-name]/spec.md` exists and has been clarified (has a Clarifications section and complete acceptance checklist).

### Step 2: Architecture Design

Analyze the specification and design the high-level architecture:

1. **Component Identification**
   - What major components are needed?
   - How do they interact?
   - What are the boundaries between components?

2. **Integration Points**
   - What external systems must this integrate with?
   - What APIs will be consumed?
   - What APIs will be exposed?

3. **Data Flow**
   - How does data move through the system?
   - What transformations occur?
   - Where is data persisted?

**Ask for input when:**
- Multiple valid architectural approaches exist
- Trade-offs need user decision (e.g., simplicity vs scalability)
- Constitution doesn't specify a preference

### Step 3: Technology Selection

Based on the constitution and requirements, select specific technologies:

1. **Framework/Library Choices**
   - What frameworks best fit the requirements?
   - Are there existing patterns in the codebase to follow?
   - What libraries are needed for specific functionality?

2. **Database Design**
   - What database(s) are appropriate?
   - What's the data model strategy (relational, document, etc.)?
   - What indexing/performance considerations exist?

3. **Infrastructure Considerations**
   - What hosting/deployment approach?
   - What caching strategy (if needed)?
   - What monitoring/observability needs?

**Document rationale for each choice:**
```markdown
### [Technology] Selection

**Chosen**: [Technology name and version]
**Alternatives Considered**: [Other options]
**Rationale**: [Why this was selected]
**Constitution Alignment**: [How it aligns with project principles]
```

### Step 4: Data Model Design

Create a comprehensive data model:

1. **Entities**
   - What data entities are needed?
   - What are their attributes?
   - What are the relationships?

2. **Schema Design**
   ```markdown
   ### [Entity Name]

   | Field | Type | Constraints | Description |
   |-------|------|-------------|-------------|
   | id | UUID | PK | Unique identifier |
   | ... | ... | ... | ... |

   **Relationships:**
   - [Relationship description]

   **Indexes:**
   - [Index description and purpose]
   ```

3. **Data Lifecycle**
   - How is data created, updated, deleted?
   - What are the retention policies?
   - How is data migrated/versioned?

### Step 5: API Design

Define the API contracts:

1. **Endpoint Design**
   ```markdown
   ### [Operation Name]

   **Endpoint**: `[METHOD] /api/v1/[resource]`
   **Description**: [What it does]
   **Authentication**: [Required/Optional, type]

   **Request:**
   ```json
   {
     "field": "type - description"
   }
   ```

   **Response (200):**
   ```json
   {
     "field": "type - description"
   }
   ```

   **Error Responses:**
   - 400: [When/why]
   - 401: [When/why]
   - 404: [When/why]
   ```

2. **Create OpenAPI/JSON Schema** (if applicable)
   - Generate `api-spec.json` with full endpoint definitions

### Step 6: Research Documentation

Document any research performed:

1. **Technology Evaluations**
   - What options were researched?
   - What were the findings?
   - What benchmarks were run (if any)?

2. **Pattern Research**
   - What design patterns were considered?
   - What examples were referenced?
   - What best practices were identified?

3. **Risk Assessment**
   - What technical risks exist?
   - What mitigations are planned?

### Step 7: Review and Update Project Architecture

Review the existing project architecture document (`[docs_folder]/architecture.md`) and update it to accommodate this feature:

1. **If the architecture document exists:**
   - Read it thoroughly to understand the current system architecture
   - Identify where this feature fits into the existing architecture
   - Determine if any existing components need modification
   - Add new components, services, or modules introduced by this feature
   - Update diagrams or descriptions to reflect the changes
   - Ensure consistency between the feature plan and the overall architecture

2. **If the architecture document doesn't exist:**
   - Create a new architecture document that captures the project's structure
   - Include the components being added by this feature
   - Document the high-level system design

3. **What to include in architecture updates:**
   - New components or services added
   - Modified integration points
   - New data flows
   - Updated system boundaries
   - Any architectural decisions that affect the broader system

**Important**: The architecture document is a living document that evolves with the project. Each feature should leave it more complete and accurate than before.

### Step 8: Create Planning Documents

Create the following files in `specs/[feature-name]/`:

**1. plan.md** - Main implementation plan
```markdown
# [Feature Name] Implementation Plan

## Architecture Overview

### High-Level Design
[Diagram or description of component architecture]

### Component Responsibilities
- **[Component 1]**: [Responsibility]
- **[Component 2]**: [Responsibility]

### Integration Points
- [External system]: [How it integrates]

## Technology Stack

### [Category]
**Chosen**: [Technology]
**Rationale**: [Why]

## Implementation Strategy

### Phase 1: [Phase Name]
[Description of what will be built]

### Phase 2: [Phase Name]
[Description of what will be built]

## Security Considerations
[How security requirements will be met]

## Performance Strategy
[How performance requirements will be met]

## Testing Strategy
[Approach to testing this feature]

## Deployment Considerations
[How this will be deployed]
```

**2. data-model.md** - Database schema and relationships
```markdown
# [Feature Name] Data Model

## Entity Relationship Diagram
[Text-based ERD or description]

## Entities

### [Entity Name]
[Table definition as shown in Step 4]

## Migrations
[Migration strategy if applicable]
```

**3. api-spec.json** - OpenAPI specification (if applicable)
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "[Feature] API",
    "version": "1.0.0"
  },
  "paths": {
    ...
  }
}
```

**4. research.md** - Research findings
```markdown
# [Feature Name] Research

## Technology Evaluations
[Findings from research]

## Design Decisions
[Key decisions and rationale]

## References
[Links to documentation, articles, examples referenced]
```

## Example Dialog

```
Claude: I'll create a technical implementation plan. Which feature are you planning?

User: user-authentication

Claude: Let me review the specification and constitution...

[Reads both files]

I see you're using TypeScript with Next.js and prioritizing security. The spec requires
email/password and Google OAuth signup with email verification.

Let me design the architecture. I have a question about session management:

[Uses AskUserQuestion with options:
- JWT tokens (stateless, good for scaling)
- Server-side sessions with Redis (more control, easier revocation)
- Next.js built-in auth (iron-session)
- Other]

User: JWT tokens

Claude: Good choice for scalability. For the database schema, I see you're using PostgreSQL.

Here's the proposed data model:

**Users Table:**
| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NULL (for OAuth users) |
| email_verified | BOOLEAN | DEFAULT FALSE |
| created_at | TIMESTAMP | NOT NULL |

**OAuth Connections Table:**
| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users |
| provider | VARCHAR(50) | NOT NULL |
| provider_id | VARCHAR(255) | NOT NULL |

Does this data model match your needs?

[Continues planning...]

✓ Technical plan created!

**Files created/updated:**
- specs/user-authentication/plan.md
- specs/user-authentication/data-model.md
- specs/user-authentication/api-spec.json
- specs/user-authentication/research.md
- [docs_folder]/architecture.md (updated with auth components)

**Next step:**
Run `/spec_driven_development.tasks` to generate the implementation task breakdown.
```

## Output Format

### specs/[feature-name]/plan.md
Main implementation plan with architecture, technology choices, and strategy.

### specs/[feature-name]/data-model.md
Database schema with entities, relationships, and migration strategy.

### specs/[feature-name]/api-spec.json
OpenAPI specification for API endpoints (if applicable).

### specs/[feature-name]/research.md
Research findings, technology evaluations, and references.

### [docs_folder]/architecture.md
Project-wide architecture document, updated to include this feature's components and integrations.

After creating the files:
1. Summarize the architecture and key technology choices
2. Highlight any decisions that required user input
3. Tell the user to run `/spec_driven_development.tasks` to generate tasks

## Quality Criteria

- Architecture clearly addresses all specification requirements
- Technology choices are justified with rationale
- Constitution principles are respected
- Data model is normalized and complete
- API contracts are well-defined
- Security considerations are addressed
- Research is documented
- Project architecture document reviewed and updated
- All planning documents created in correct location
- **No implementation code**: Documents contain schemas and contracts, not actual code
