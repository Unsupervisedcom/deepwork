---
name: Expert Design Patterns
keywords:
  - patterns
  - structure
  - organization
  - best practices
last_updated: 2025-01-30
---

# Expert Design Patterns

Common patterns for structuring effective experts.

## The Layered Knowledge Pattern

Structure expertise from general to specific:

1. **full_expertise**: Core concepts, decision frameworks, common patterns
2. **topics/**: Deep dives into specific subjects
3. **learnings/**: Concrete experiences and edge cases

This mirrors how humans learn - start with foundations, then specialize.

## The Problem-Solution Pattern

For domains centered around solving problems:

- **full_expertise**: Problem categories, diagnostic approaches, solution frameworks
- **topics/**: Specific problem types with detailed solutions
- **learnings/**: Real debugging sessions and unexpected fixes

Works well for: troubleshooting guides, error handling, debugging domains.

## The Reference Pattern

For domains with lots of factual information:

- **full_expertise**: Overview, when to use what, quick reference
- **topics/**: Detailed reference on specific APIs, configs, options
- **learnings/**: Gotchas and undocumented behaviors

Works well for: API documentation, configuration guides, tool references.

## The Process Pattern

For domains with sequential workflows:

- **full_expertise**: Overall process, decision points, success criteria
- **topics/**: Detailed steps for each phase
- **learnings/**: Process failures and improvements

Works well for: deployment procedures, review processes, onboarding.

## Anti-Patterns to Avoid

### The Kitchen Sink
Cramming everything into full_expertise. If it's over 5 pages, split into topics.

### The Empty Shell
Creating expert.yml with minimal content and empty topics/learnings folders.
Start with meaningful content or don't create the expert yet.

### The Stale Expert
Never updating after initial creation. Set a reminder to review quarterly.

### The Duplicate Expert
Creating overlapping experts. Better to have one comprehensive expert than
several fragmented ones.
