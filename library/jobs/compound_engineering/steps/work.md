# Execute Implementation

## Objective

Execute an implementation plan systematically with continuous testing, incremental commits, and real-time task tracking.

## Task

Follow the implementation plan step-by-step, maintaining quality throughout execution by testing continuously and committing incrementally.

**Philosophy**: Execution is only 20% of the effort because the plan did the heavy lifting. Focus on following the plan, maintaining quality, and avoiding scope creep.

### Phase 1: Quick Start

1. **Load the Plan**
   - Ask the user which plan to execute, or use the most recent one
   - Read the plan file from `docs/plans/`
   - Verify all open questions have been resolved (if not, resolve them first)

2. **Clarify Any Ambiguities**
   - If anything in the plan is unclear, ask before starting
   - Don't make assumptions that could lead to rework

3. **Setup the Environment**
   - Create a feature branch if not already on one
   - Ensure the development environment is ready
   - Pull latest changes from the base branch

   ```bash
   git checkout -b feature/[feature-name]
   # or verify current branch
   git branch --show-current
   ```

### Phase 2: Task Tracking Setup

**IMPORTANT**: Use the TodoWrite tool throughout execution to track progress.

1. **Import Tasks from Plan**
   - Extract all checklist items from the plan's "Implementation Checklist" section
   - Add them to TodoWrite as pending tasks

2. **Task Management Rules**
   - Only ONE task should be `in_progress` at a time
   - Mark tasks `completed` immediately when done (don't batch)
   - Add new tasks if you discover additional work needed

### Phase 3: Task Execution Loop

For each task in the checklist:

1. **Mark Task In Progress**
   - Use TodoWrite to mark the current task as `in_progress`
   - Update the plan file: change `- [ ]` to `- [x]` for this task

2. **Implement Following Patterns**
   - Reference the codebase patterns identified in the plan
   - Follow existing conventions (naming, structure, style)
   - Avoid introducing new patterns unless necessary

3. **Write Tests**
   - Write or update tests for the change
   - Follow the test patterns documented in the plan
   - Don't skip tests to "save time"

4. **Run Tests Immediately**
   - Run tests after implementing each task
   - Don't batch test runs to the end
   - Fix failures before moving to the next task

   ```bash
   [test_command]
   ```

5. **Commit Incrementally**
   - After each completed task, consider if it's a logical commit point
   - Use conventional commit messages: `feat(scope): description`
   - Small, focused commits are easier to review and revert

   ```bash
   git add [specific files]
   git commit -m "feat([scope]): [what this commit does]"
   ```

6. **Mark Task Complete**
   - Use TodoWrite to mark the task as `completed`
   - Verify the checkbox is checked in the plan file

7. **Repeat**
   - Move to the next task
   - Continue until all tasks are complete

### Phase 4: Quality Checkpoints

At natural breakpoints (end of a section, major feature complete):

1. **Run Full Test Suite**
   ```bash
   [test_command]
   ```

2. **Run Linting**
   ```bash
   [lint_command]
   ```

3. **Self-Review**
   - Does the code follow the patterns identified in the plan?
   - Is the code simpler than necessary? (prefer simplicity)
   - Are there any obvious issues?

### Phase 5: Completion

When all tasks are done:

1. **Final Verification**
   - All tests pass
   - All checklist items in the plan are checked
   - No uncommitted changes

2. **Summary**
   - Summarize what was implemented
   - Note any deviations from the plan (and why)
   - List any follow-up tasks discovered

3. **Next Steps**
   - Tell the user to run `/compound_engineering.review` for code review
   - Or if they discovered issues worth documenting, suggest `/compound_engineering.compound`

## Example Dialog

```
User: /compound_engineering.work

Claude: I'll execute an implementation plan. Which plan should I work on?

[Lists recent plans from docs/plans/]

1. 2025-01-29-feature-notification-system-plan.md
2. 2025-01-28-bugfix-login-timeout-plan.md

User: 1

Claude: Loading the notification system plan...

[Reads docs/plans/2025-01-29-feature-notification-system-plan.md]

I see 8 tasks in the checklist. Let me set up task tracking:

[Uses TodoWrite to add all tasks]

Open questions status:
- [x] Email batch interval resolved (15 minutes)

All questions resolved. Setting up the environment:

[Creates feature branch]

Starting implementation. Task 1 of 8: Create UserNotificationPreferences table

[Marks task as in_progress in TodoWrite]

Creating the migration...

[Implements migration]

Running tests...

[Runs test command]

Tests pass. Committing...

[Commits with message: feat(notifications): add user notification preferences table]

[Marks task as completed, updates plan checkbox]

Moving to Task 2: Add preference columns...

[Continues through all tasks]

...

All 8 tasks complete!

Summary:
- Added UserNotificationPreferences table with 3 preference columns
- Extended EmailService with batch notification support
- Added WebSocket notification channel
- Created notification preference UI component
- Added 12 new tests (all passing)

Deviations from plan:
- Added a `notification_count` denormalized column for performance (documented in commit)

Ready for review. Run `/compound_engineering.review` to start multi-perspective code review.
```

## Handling Issues

### Tests Fail
- Fix the failure before moving to the next task
- Don't accumulate failures
- If the fix is complex, consider if the plan needs revision

### Scope Creep
- If you discover additional work needed, add it to TodoWrite
- If it's substantial, pause and discuss with the user
- Don't silently expand scope

### Plan Seems Wrong
- Stop and discuss with the user
- It's better to revise the plan than to implement something incorrect
- Update the plan file with changes agreed upon

### Unexpected Complexity
- Break down the complex task into smaller subtasks
- Add subtasks to TodoWrite
- Consider if this should be documented as a learning later

## Quality Criteria

- Plan was loaded and understood before starting
- TodoWrite was used to track all tasks throughout execution
- Tests were run after each task, not batched at the end
- Changes were committed incrementally with clear messages
- Plan checkboxes were updated as tasks completed
- All tasks from the plan were completed
- Final test suite passes

## Context

This is the execution step in the Compound Engineering cycle. By this point, the heavy thinking is done in the plan. This step is about disciplined execution: follow the plan, test continuously, commit incrementally.

The continuous testing and incremental commits make the review step easier (smaller changes to understand) and provide natural rollback points if issues are discovered later.
