# Initialize Branch and Draft PR

## Objective

Create a dedicated git worktree or branch for the engineering issue, commit the specification,
and open a draft PR using the repository's standardized PR template.

## Task

Set up the version control foundation for engineering work. The specification must be committed
before any implementation code, and a draft PR must exist immediately to enable continuous
synchronization.

### Process

1. **Create a dedicated branch or worktree**
   - Branch naming: follow the repository's conventions (e.g., `feat/issue-123-description`)
   - If the repository uses worktrees, create one; otherwise create a branch
   - Ensure the branch is based on the latest default branch

2. **Commit the engineering specification**
   - Add the engineering issue content to the branch (e.g., as a spec file, or as the commit message)
   - This commit MUST happen before any implementation code
   - Use a conventional commit message: `docs(engineer): add engineering spec for #[issue-number]`

3. **Open a draft PR**
   - Use the repository's standardized PR template
   - Title: follow repository conventions (e.g., `feat(scope): description`)
   - Link the PR to the engineering issue
   - Populate the task checklist from the engineering issue's implementation plan
   - Mark the PR as draft

4. **Record the branch context**
   - Document the branch name, PR URL, and initial commit SHA
   - This context is consumed by subsequent steps

### Domain Adaptation

| Concept          | Software            | Hardware/CAD         | Firmware            | Docs               |
|------------------|---------------------|----------------------|---------------------|---------------------|
| Spec commit      | API contract/schema | Design doc/BOM       | Register map        | Content outline     |
| PR template      | Code PR template    | Design review form   | HW/FW PR template   | Doc review template |

## Output Format

### .deepwork/tmp/branch_context.md

**Structure**:
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
- Linked in PR: yes/no

## Task Checklist (from PR)
- [ ] Task 1: [description]
- [ ] Task 2: [description]
...
```

## Quality Criteria

- Branch is based on the latest default branch
- Engineering spec was committed before any implementation code
- Draft PR uses the repository's standardized template
- PR is linked to the engineering issue
- Task checklist is populated from the implementation plan
