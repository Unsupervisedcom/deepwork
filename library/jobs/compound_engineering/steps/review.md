# Multi-Perspective Code Review

## Objective

Perform a comprehensive code review using multiple specialized perspectives to catch issues before merging.

## Task

Review code changes from multiple angles, categorize findings by severity, and provide actionable feedback.

**Philosophy**: Reviews are 80% of quality assurance. Multiple perspectives catch what single-focus reviews miss. A thorough review now prevents bugs, tech debt, and rework later.

### Phase 1: Identify Review Target

Determine what code to review:

1. **Ask for the Target**
   - Branch name (review all changes on that branch)
   - PR number (if using GitHub)
   - Specific files (for focused review)
   - "Current changes" (review uncommitted or recent commits)

2. **Get the Diff**
   ```bash
   # For branch comparison
   git diff main...[branch-name]

   # For recent changes
   git diff HEAD~5..HEAD

   # For uncommitted changes
   git diff
   ```

3. **Identify Changed Files**
   ```bash
   git diff --name-only main...[branch-name]
   ```

### Phase 2: Setup for Review

1. **Understand the Context**
   - What feature or fix are these changes for?
   - Is there an implementation plan to reference?
   - What are the acceptance criteria?

2. **Load Review Standards**
   - Read the project's code review standards if they exist
   - Note any project-specific conventions

### Phase 3: Multi-Perspective Review

Run reviews from multiple specialized perspectives. Use sub-agents (Task tool) to keep context clean.

**IMPORTANT**: Run at least 3 perspectives. Choose based on what the changes touch.

#### Core Perspectives (Always Run)

1. **Code Quality Reviewer**
   Focus: Clarity, simplicity, maintainability

   ```
   Review these changes for code quality:
   - Is the code simple and readable?
   - Are names clear and descriptive?
   - Is there unnecessary complexity?
   - Are there DRY violations?
   - Is the code well-organized?
   ```

2. **Pattern Compliance Reviewer**
   Focus: Consistency with existing codebase

   ```
   Review these changes for pattern compliance:
   - Do they follow existing codebase conventions?
   - Are there new patterns introduced unnecessarily?
   - Is the code structure consistent with similar features?
   - Are naming conventions followed?
   ```

3. **Test Coverage Reviewer**
   Focus: Test adequacy

   ```
   Review the tests for these changes:
   - Are all new code paths tested?
   - Are edge cases covered?
   - Are the tests meaningful (not just for coverage)?
   - Do tests follow existing patterns?
   ```

#### Conditional Perspectives (Run When Relevant)

4. **Security Reviewer** (run for: auth, input handling, data access)
   Focus: Security vulnerabilities

   ```
   Review these changes for security issues:
   - Input validation and sanitization
   - Authentication and authorization
   - Data exposure risks
   - SQL injection, XSS, CSRF vulnerabilities
   - Secrets handling
   ```

5. **Performance Reviewer** (run for: data processing, queries, loops)
   Focus: Performance implications

   ```
   Review these changes for performance:
   - N+1 queries
   - Unnecessary database calls
   - Inefficient algorithms
   - Memory usage concerns
   - Caching opportunities
   ```

6. **Database Reviewer** (run for: migrations, schema changes)
   Focus: Data integrity and migrations

   ```
   Review these database changes:
   - Is the migration reversible?
   - Are there data integrity risks?
   - Are indexes appropriate?
   - Is the migration safe for production?
   ```

7. **API Reviewer** (run for: endpoint changes, contracts)
   Focus: API design and compatibility

   ```
   Review these API changes:
   - Is the API intuitive and consistent?
   - Are breaking changes identified?
   - Is error handling appropriate?
   - Is the documentation updated?
   ```

8. **Accessibility Reviewer** (run for: UI changes)
   Focus: Accessibility compliance

   ```
   Review these UI changes for accessibility:
   - Keyboard navigation
   - Screen reader compatibility
   - Color contrast
   - ARIA labels and roles
   ```

### Phase 4: Run the Reviews

For each perspective:

1. **Spawn a Sub-Agent**
   Use Task tool with `subagent_type: general-purpose`

   ```
   Prompt: "You are a [Perspective] reviewer. Review these code changes:

   [Include the diff or file contents]

   [Include perspective-specific questions from above]

   For each issue found, provide:
   - File and line number
   - Issue description
   - Severity: P1 (critical/blocks merge), P2 (important), P3 (nice-to-have)
   - Suggested fix"
   ```

2. **Collect Findings**
   - Gather all issues identified
   - Note the perspective that found each issue

### Phase 5: Synthesize Findings

After all reviews complete:

1. **Deduplicate**
   - Multiple perspectives may find the same issue
   - Combine duplicate findings

2. **Categorize by Severity**

   **P1 - Critical (Blocks Merge)**
   - Security vulnerabilities
   - Data integrity risks
   - Breaking changes without migration
   - Failing tests

   **P2 - Important (Should Fix)**
   - Performance issues
   - Missing test coverage
   - Code quality concerns
   - Pattern violations

   **P3 - Nice-to-Have (Optional)**
   - Style preferences
   - Minor optimizations
   - Documentation improvements

3. **Create Findings Document**

   ```markdown
   # Code Review Findings

   **Target**: [branch/PR/files reviewed]
   **Date**: YYYY-MM-DD
   **Perspectives Applied**: [list of perspectives]

   ## Summary
   - P1 (Critical): [count]
   - P2 (Important): [count]
   - P3 (Nice-to-have): [count]

   **Merge Status**: [BLOCKED if any P1s, else APPROVED with conditions]

   ## P1 - Critical Issues

   ### [Issue Title]
   - **File**: [path:line]
   - **Found by**: [perspective]
   - **Issue**: [description]
   - **Fix**: [suggested remediation]

   ## P2 - Important Issues

   ### [Issue Title]
   ...

   ## P3 - Nice-to-Have

   ### [Issue Title]
   ...

   ## Positive Observations
   - [What was done well]
   ```

### Phase 6: Present Findings

1. **Summarize for the User**
   - Total findings by severity
   - Whether merge is blocked (any P1s)
   - Key issues to address

2. **Provide Clear Next Steps**
   - If P1s exist: Must fix before merge
   - If only P2s: Strongly recommend fixing
   - If only P3s: Optional, approve merge

3. **Offer Follow-up**
   - Re-review after fixes
   - Run `/compound_engineering.compound` to document learnings

## Example Dialog

```
User: /compound_engineering.review

Claude: I'll perform a multi-perspective code review. What should I review?

1. A specific branch
2. A PR number
3. Current uncommitted changes
4. Specific files

User: Branch feature/notification-system

Claude: Reviewing changes on feature/notification-system compared to main...

[Gets diff and file list]

I see changes to:
- src/services/email.ts (modified)
- src/realtime/notifications.ts (new)
- src/db/migrations/add_notification_prefs.ts (new)
- tests/notifications.test.ts (new)

Based on these changes, I'll apply 6 review perspectives:
1. Code Quality (core)
2. Pattern Compliance (core)
3. Test Coverage (core)
4. Security (auth/data handling)
5. Performance (email batching)
6. Database (migration)

Running reviews in parallel...

[Spawns 6 sub-agents with Task tool]

Synthesizing findings...

# Review Summary

**Perspectives Applied**: 6
**Findings**: 0 P1, 3 P2, 2 P3
**Merge Status**: APPROVED with conditions

## P2 - Important Issues (3)

### Missing Rate Limiting on Notification Endpoint
- **File**: src/realtime/notifications.ts:45
- **Found by**: Security Reviewer
- **Issue**: The WebSocket notification endpoint doesn't rate limit, allowing potential spam
- **Fix**: Add rate limiting middleware, suggest 10 notifications/second per user

### No Index on notification_preferences.user_id
- **File**: src/db/migrations/add_notification_prefs.ts:12
- **Found by**: Database Reviewer
- **Issue**: The user_id foreign key should have an index for query performance
- **Fix**: Add index in migration

### Batch Email Query Could Be Optimized
- **File**: src/services/email.ts:78
- **Found by**: Performance Reviewer
- **Issue**: The batch query fetches all columns when only email is needed
- **Fix**: Select only required columns

## P3 - Nice-to-Have (2)

### Consider Extracting Notification Types to Enum
- **File**: src/realtime/notifications.ts:15
- **Found by**: Pattern Compliance
- **Issue**: Notification types are string literals, enum would be safer
- **Fix**: Extract to NotificationType enum

### Add JSDoc to New Public Functions
- **File**: src/services/email.ts:60
- **Found by**: Code Quality
- **Issue**: New public functions lack documentation
- **Fix**: Add JSDoc comments

## Positive Observations
- Good test coverage for the new functionality
- Migration is properly reversible
- Follows existing service patterns well

**Recommendation**: Fix the 3 P2 issues before merging. The P3s are optional.

Would you like me to help fix these issues, or should I re-review after you make changes?
```

## Quality Criteria

- Review target was clearly identified
- At least 3 review perspectives were applied
- Findings were categorized by severity (P1/P2/P3)
- Any merge-blocking issues are clearly marked as P1
- Each finding includes actionable remediation
- A summary of overall code quality was provided

## Context

This is the quality assurance step in the Compound Engineering cycle. Multiple perspectives catch different types of issues that a single-focus review would miss.

The severity categorization (P1/P2/P3) helps prioritize: P1s must be fixed, P2s should be fixed, P3s are optional. This prevents bikeshedding on minor issues while ensuring critical issues are addressed.
