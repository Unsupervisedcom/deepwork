# Review Changes

Perform comprehensive code review from multiple perspectives before merging.

## Purpose

Code review is a critical part of the compound engineering cycle. Good reviews:
- Catch issues before they reach production
- Ensure code follows established patterns
- Identify opportunities for simplification
- Capture learnings for future reference

**Philosophy**: Reviews should be thorough but actionable. Every finding should either block merge (P1), require fixing (P2), or suggest improvement (P3).

## Input

**Review Target**: `{{review_target}}`

Accepted formats:
- PR number: `123`
- GitHub URL: `https://github.com/org/repo/pull/123`
- Branch name: `feat/user-auth`
- `latest` - Review current branch

If no target provided, ask:
> "What should I review? Provide a PR number, branch name, or say 'latest' for current branch."

## Execution Flow

### Phase 1: Setup

#### 1.1 Identify Review Target

```bash
# For PR number
gh pr view [number] --json title,body,files,headRefName

# For current branch
git branch --show-current
git log -5 --oneline
git diff main...HEAD --stat
```

Capture:
- PR title and description
- Files changed
- Branch name
- Commit history

#### 1.2 Checkout Code (If Needed)

**If already on the target branch**: Proceed with review

**If on different branch**, offer options:
1. **Review from diff** - Read diffs without switching
2. **Checkout branch** - `git checkout [branch]`
3. **Use worktree** - `git worktree add .worktrees/review-[branch]`

### Phase 2: Multi-Perspective Review

Review the changes from multiple angles. For each perspective, note findings with severity.

#### 2.1 Code Simplicity Review

Ask: "Is this code as simple as it can be?"

**Check for**:
- Unnecessary complexity
- Over-engineered abstractions
- Code that could be inlined
- YAGNI violations (features not needed yet)
- Redundant error checking
- Dead code or commented-out code

**Output format**:
```
## Simplicity Analysis

**Core purpose**: [What this code does]

**Unnecessary complexity found**:
- [File:line] - [Issue] - [Suggested simplification]

**YAGNI violations**:
- [Feature/abstraction that isn't needed]

**Estimated LOC reduction**: [X lines]
```

#### 2.2 Security Review

Ask: "Are there security vulnerabilities?"

**Check for**:
- SQL injection risks
- XSS vulnerabilities
- Authentication/authorization gaps
- Sensitive data exposure
- Input validation issues
- CSRF protection

**Output format**:
```
## Security Analysis

**Attack surface**: [Brief description]

**Vulnerabilities found**:
- [P1] [File:line] - [Vulnerability] - [Impact]
- [P2] [File:line] - [Issue] - [Mitigation]
```

#### 2.3 Performance Review

Ask: "Are there performance issues?"

**Check for**:
- N+1 queries
- Missing indexes
- Expensive operations in loops
- Memory leaks
- Unnecessary data loading
- Missing caching opportunities

**Output format**:
```
## Performance Analysis

**Hot paths affected**: [List]

**Issues found**:
- [File:line] - [Issue] - [Impact] - [Fix]
```

#### 2.4 Architecture Review

Ask: "Does this fit the codebase patterns?"

**Check for**:
- Consistency with existing patterns
- Proper separation of concerns
- Appropriate abstraction levels
- API design issues
- Breaking changes

**Output format**:
```
## Architecture Analysis

**Patterns followed**: [Which existing patterns are used]
**Deviations**: [Where it differs from conventions]

**Concerns**:
- [Issue] - [Why it matters] - [Suggested change]
```

#### 2.5 Data Integrity Review

For changes involving database or data transformations:

**Check for**:
- Migration safety (can it be rolled back?)
- Data validation
- Referential integrity
- Race conditions in data updates
- Audit trail for sensitive changes

### Phase 3: Synthesize Findings

#### 3.1 Categorize by Severity

**P1 - Critical (Blocks Merge)**:
- Security vulnerabilities
- Data corruption risks
- Breaking changes without migration
- Critical bugs

**P2 - Important (Should Fix)**:
- Performance issues
- Architectural concerns
- Code quality problems
- Missing tests for critical paths

**P3 - Nice-to-Have**:
- Minor improvements
- Code cleanup
- Documentation updates
- Style suggestions

#### 3.2 Create Review Document

Write findings to `docs/reviews/`:

```bash
mkdir -p docs/reviews
```

**Filename**: `docs/reviews/[pr-number-or-branch]-review.md`

**Template**:
```markdown
---
target: [PR #X or branch name]
date: YYYY-MM-DD
reviewer: Claude
status: [needs-changes|approved|approved-with-suggestions]
---

# Code Review: [Title]

## Summary
- **Total Findings**: [X]
- **P1 (Blocks Merge)**: [count]
- **P2 (Should Fix)**: [count]
- **P3 (Nice-to-Have)**: [count]

## Verdict
[BLOCKED - address P1 issues | APPROVED with P2 suggestions | APPROVED]

## P1 - Critical Issues
### [Issue Title]
**File**: `path/to/file.ext:line`
**Issue**: [Description]
**Impact**: [What could go wrong]
**Fix**: [Suggested solution]

## P2 - Important Issues
### [Issue Title]
**File**: `path/to/file.ext:line`
**Issue**: [Description]
**Suggested Fix**: [Solution]

## P3 - Suggestions
- [File:line] - [Suggestion]
- [File:line] - [Suggestion]

## What's Good
- [Positive observation 1]
- [Positive observation 2]

## Next Steps
1. [Required action]
2. [Suggested action]
```

### Phase 4: Present Findings

#### 4.1 Summary Report

Present a concise summary:

```
## Review Complete: [PR Title]

**Verdict**: [BLOCKED / NEEDS CHANGES / APPROVED]

### Findings:
- P1 (Critical): [count] - [MUST FIX before merge]
- P2 (Important): [count] - [Should fix]
- P3 (Nice-to-have): [count] - [Optional]

### Critical Issues (P1):
1. [Brief description] - [file:line]

### Required Actions:
1. [Action item]
2. [Action item]

Full review: docs/reviews/[filename].md
```

#### 4.2 Next Steps

Present options based on findings:

**If P1 issues exist**:
> "This PR has critical issues that block merge. Would you like me to:"
> 1. Help fix the P1 issues
> 2. Comment on the PR with findings
> 3. Just note for manual fixing

**If only P2/P3 issues**:
> "No critical issues found. Would you like to:"
> 1. Comment suggestions on the PR
> 2. Approve with comments
> 3. Make suggested improvements first

## Review Checklist

Use this checklist for thorough review:

- [ ] **Functionality**: Does it do what the plan/spec says?
- [ ] **Tests**: Are new features tested? Do existing tests pass?
- [ ] **Security**: Any injection, auth, or data exposure risks?
- [ ] **Performance**: Any N+1, missing indexes, or expensive ops?
- [ ] **Architecture**: Does it follow existing patterns?
- [ ] **Simplicity**: Is it as simple as it can be?
- [ ] **Error Handling**: Are errors handled gracefully?
- [ ] **Documentation**: Is complex logic explained?
- [ ] **Edge Cases**: Are boundary conditions handled?

## Output

When complete, display:

```
Review complete!

Target: [PR #X / branch name]
Verdict: [BLOCKED / APPROVED / APPROVED WITH SUGGESTIONS]

Findings:
- P1: [count] critical issues
- P2: [count] important issues
- P3: [count] suggestions

Full review: docs/reviews/[filename].md

Recommended action: [What to do next]
```
