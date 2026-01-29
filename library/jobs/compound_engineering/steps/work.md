# Execute Implementation

Execute a work plan efficiently while maintaining quality and finishing features.

## Purpose

This step takes a work document (plan, specification, or todo file) and executes it systematically. The focus is on **shipping complete features** by understanding requirements quickly, following existing patterns, and maintaining quality throughout.

**Philosophy**: Start fast, execute faster, ship complete features.

## Input

**Plan Document**: `{{plan_file}}`

If no plan is provided, ask:
> "Which plan should I execute? Please provide the path to the plan file."

Suggest checking `docs/plans/` for recent plans.

## Execution Flow

### Phase 1: Quick Start

#### 1.1 Read and Clarify

1. **Read the plan document completely**
   - Review all sections, especially acceptance criteria
   - Note all referenced files and patterns

2. **Ask clarifying questions NOW** (not later)
   - If anything is unclear or ambiguous, ask immediately
   - Better to ask now than build the wrong thing

3. **Get user approval to proceed**
   > "I've reviewed the plan. Ready to start on [summary]. Proceed?"

#### 1.2 Setup Environment

Check current branch:
```bash
current_branch=$(git branch --show-current)
echo "Currently on: $current_branch"
```

**If already on a feature branch**:
> "Continue working on `[current_branch]`, or create a new branch?"

**If on main/master**, offer options:
1. **Create new branch** (recommended)
   ```bash
   git checkout -b [feature-branch-name]
   ```
   Use meaningful names: `feat/user-authentication`, `fix/email-validation`

2. **Use git worktree** (for parallel development)
   ```bash
   git worktree add .worktrees/[branch-name] -b [branch-name]
   cd .worktrees/[branch-name]
   ```

3. **Stay on main** (requires explicit confirmation)
   > "Are you sure you want to commit directly to main?"

#### 1.3 Create Task List

Break the plan into actionable tasks using TodoWrite:

```
Example tasks:
- [ ] Read reference files mentioned in plan
- [ ] Create data model / database migration
- [ ] Implement core service/logic
- [ ] Add controller/API endpoints
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update documentation
- [ ] Run full test suite
```

Include:
- Dependencies between tasks
- Testing tasks alongside implementation
- Quality check tasks

### Phase 2: Execute

#### 2.1 Task Execution Loop

For each task:

1. **Mark task as in_progress** in TodoWrite
2. **Read referenced files** from the plan
3. **Look for similar patterns** in codebase
4. **Implement** following existing conventions
5. **Write tests** for new functionality
6. **Run tests** after changes
7. **Mark task completed** in TodoWrite
8. **Check off the item** in the plan file (`[ ]` -> `[x]`)
9. **Evaluate for commit** (see below)

**IMPORTANT**: Always update the plan document by checking off completed items. This keeps the plan as a living document.

#### 2.2 Incremental Commits

After each task, evaluate whether to commit:

| Commit when... | Don't commit when... |
|----------------|---------------------|
| Logical unit complete | Small part of larger unit |
| Tests pass | Tests failing |
| About to switch contexts | Purely scaffolding |
| Before risky changes | Would need "WIP" message |

**Heuristic**: Can you write a commit message describing a complete, valuable change? If yes, commit. If the message would be "WIP" or "partial X", wait.

```bash
# Commit workflow
git add [specific files for this unit]
git commit -m "feat(scope): description of this unit"
```

#### 2.3 Follow Existing Patterns

- Read the files referenced in the plan first
- Match naming conventions exactly
- Reuse existing components/utilities
- Follow project coding standards (see CLAUDE.md)
- When unsure, grep for similar implementations

#### 2.4 Test Continuously

- Run relevant tests after each significant change
- Don't wait until the end to test
- Fix failures immediately
- Add new tests for new functionality

### Phase 3: Quality Check

#### 3.1 Run Core Checks

Always run before creating PR:

```bash
# Run test suite (adjust to project)
npm test
# OR
pytest
# OR
bundle exec rspec
# OR
go test ./...

# Run linting
npm run lint
# OR
rubocop
# OR
ruff check .
```

#### 3.2 Self-Review Checklist

Before creating PR, verify:

- [ ] All TodoWrite tasks marked completed
- [ ] All plan checkboxes checked off
- [ ] Tests pass
- [ ] Linting passes
- [ ] Code follows existing patterns
- [ ] No console.log/print debugging left
- [ ] No commented-out code
- [ ] Commit messages are clear

#### 3.3 Consider Review Perspectives

For complex changes, mentally review from multiple angles:

- **Simplicity**: Is this as simple as it can be?
- **Security**: Any injection risks, auth issues?
- **Performance**: Any N+1 queries, expensive operations?
- **Architecture**: Does this fit the existing patterns?

### Phase 4: Ship It

#### 4.1 Final Commit

If there are uncommitted changes:

```bash
git add .
git status  # Review what's being committed
git diff --staged  # Check the changes

git commit -m "feat(scope): description

Brief explanation if needed.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### 4.2 Create Pull Request

```bash
git push -u origin [branch-name]

gh pr create --title "feat: [Description]" --body "## Summary
- What was built
- Why it was needed

## Testing
- Tests added/modified
- Manual testing performed

## Checklist
- [ ] Tests pass
- [ ] Linting passes
- [ ] Documentation updated (if needed)

---
Plan: docs/plans/[plan-filename].md"
```

#### 4.3 Notify User

Summarize completion:
> "Implementation complete!"
>
> **PR**: [link]
> **Branch**: [branch-name]
> **Commits**: [count]
>
> **Completed**:
> - [Major item 1]
> - [Major item 2]
>
> **Follow-up needed**:
> - [Any remaining work]
>
> **Suggested next step**: Run the Review step on this PR

## Key Principles

### Start Fast, Execute Faster
- Get clarification once at the start, then execute
- Don't wait for perfect understanding
- The goal is to **finish the feature**

### The Plan is Your Guide
- Work documents reference similar code - read those files
- Follow established patterns
- Don't reinvent - match what exists

### Test As You Go
- Run tests after each change, not at the end
- Fix failures immediately
- Continuous testing prevents surprises

### Quality is Built In
- Follow existing patterns
- Write tests for new code
- Run linting before pushing

### Ship Complete Features
- Mark all tasks completed before moving on
- Don't leave features 80% done
- A finished feature beats a perfect feature that doesn't ship

## Common Pitfalls

- **Analysis paralysis** - Don't overthink, read the plan and execute
- **Skipping clarifying questions** - Ask now, not after building wrong thing
- **Ignoring plan references** - The plan has links for a reason
- **Testing at the end** - Test continuously
- **Forgetting TodoWrite** - Track progress or lose track
- **80% done syndrome** - Finish the feature, don't move on early

## Output

When complete, display:

```
Implementation complete!

PR: https://github.com/[org]/[repo]/pull/[number]
Branch: [branch-name]

Tasks completed: [X] of [Y]
Commits made: [count]

Key changes:
- [Summary of major changes]

Plan status: All acceptance criteria met

Suggested next: Run Review step on this PR
```
