# Project Context for commit

## Job-Specific Context

### commit

#### review
- Sub-agent approach: Use `general-purpose` subagent_type for code review (not `Bash`) since it needs to read and analyze code
- Review criteria priorities: DRY opportunities, naming clarity, and test coverage are emphasized based on common code quality issues
- Order matters: Review runs before tests so that any issues found can be fixed and verified by subsequent test run

#### Design Decisions
- Review step is first: Catching issues early reduces wasted test runs on code that will need changes
- Sub-agent for review: Keeps main conversation context clean for subsequent steps
- Fix in main agent: After sub-agent reports issues, fixes happen in main agent to maintain context about the session's changes

## Last Updated
- Date: 2026-01-21
- From conversation about: Adding code review stage to commit job
