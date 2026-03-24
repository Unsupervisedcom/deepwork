# Initialize Branch and Draft PR

Create a dedicated git branch or worktree for the engineering issue, commit the specification
before any implementation code, and open a draft PR using the repository's PR template.

## Process

1. Create a branch based on the latest default branch, following the repository's naming conventions
2. Commit the engineering specification — this MUST happen before any implementation code
   - Use a conventional commit: `docs(engineer): add engineering spec for #[issue-number]`
3. Open a draft PR using the repository's standardized template:
   - Link the PR to the engineering issue
   - Populate the task checklist from the engineering issue's implementation plan
4. Record the branch name, PR URL, and initial commit SHA

## Output Format

### .deepwork/tmp/branch_context.md

```markdown
# Branch Context

## Version Control
- Branch: [branch-name]
- Base: [default-branch]
- Initial Commit: [sha]

## Pull Request
- URL: [pr-url]
- State: draft
- Template: [template used]

## Engineering Issue
- URL: [engineering-issue-url]

## Task Checklist (from PR)
- [ ] Task 1: [description]
- [ ] Task 2: [description]
```
