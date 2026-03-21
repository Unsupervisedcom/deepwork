# Check Branch Protection

## Objective

Check branch protection rules on the repository's default branch and report any missing or insufficient protections.

## Task

### Process

1. **Read platform context** from `platform_context.md`
   - Get the default branch name and provider

2. **Fetch branch protection rules**
   - Use the provider's API or CLI to retrieve current protection settings on the default branch
   - If no protection rules are configured, note that the branch is unprotected

3. **Check for expected protections**

   Expected protections:
   - **Require PR reviews**: At least 1 approval required before merge
   - **Dismiss stale reviews**: Approvals dismissed when new commits are pushed
   - **Require status checks**: CI must pass before merge (if CI is configured)
   - **Restrict force pushes**: Force pushes to default branch are blocked
   - **Restrict deletions**: Default branch cannot be deleted

4. **Report findings**
   - For each expected protection, note whether it is enabled or missing
   - Do NOT attempt to modify protections in the setup workflow — only report

## Output Format

### branch_protection_report.md

```markdown
# Branch Protection Report

## Repository
- **Repo**: [owner/repo]
- **Default Branch**: [branch name]
- **Provider**: [github | forgejo | etc.]

## Protection Status

| Protection | Status | Details |
|------------|--------|---------|
| Require PR reviews | [enabled \| missing] | [min approvals or N/A] |
| Dismiss stale reviews | [enabled \| missing] | |
| Require status checks | [enabled \| missing \| N/A (no CI)] | [required checks] |
| Restrict force pushes | [enabled \| missing] | |
| Restrict deletions | [enabled \| missing] | |

## Summary
- **Protections Enabled**: [count]/5
- **Missing Protections**: [list]
- **Overall**: [protected \| partially protected \| unprotected]
```

## Quality Criteria

- Branch protection rules on the default branch have been inspected
- Each expected protection is reported as enabled or missing
- Missing or insufficient protections are clearly documented
