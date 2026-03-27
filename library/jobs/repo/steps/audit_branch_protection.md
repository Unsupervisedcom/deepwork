# Audit Branch Protection

## Objective

Deep check of branch protection rules on the default branch. Attempt to enable missing protections via the provider's API.

## Task

### Process

1. **Read platform context** from `platform_context.md`

2. **Fetch current branch protection**
   - Use the provider's API or CLI to retrieve protection settings on the default branch

3. **Check all expected protections**

   Same checklist as check_branch_protection:
   - Require PR reviews (min 1 approval)
   - Dismiss stale reviews
   - Require status checks (if CI configured)
   - Restrict force pushes
   - Restrict deletions

4. **Attempt to enable missing protections**
   - Use the provider's API to enable missing protections
   - Be careful with APIs that replace the entire protection config — read existing settings first and merge
   - Document any API errors or permission issues

5. **Verify changes**
   - Re-fetch protection rules to confirm the changes took effect
   - Document any API errors or permission issues

## Output Format

### branch_protection_audit.md

```markdown
# Branch Protection Audit

## Repository
- **Repo**: [owner/repo]
- **Default Branch**: [branch name]
- **Provider**: [github | forgejo | etc.]

## Findings

| Protection | Before | After | Action |
|------------|--------|-------|--------|
| Require PR reviews | [enabled \| missing] | [enabled \| missing] | [enabled via API \| already set \| failed: reason] |
| Dismiss stale reviews | ... | ... | ... |
| Require status checks | ... | ... | ... |
| Restrict force pushes | ... | ... | ... |
| Restrict deletions | ... | ... | ... |

## Actions Taken
- [List of API calls made and their results]

## Remaining Gaps
- [Protections that could not be enabled, with reasons]
- [Or "None — all protections are in place"]
```

## Quality Criteria

- All branch protection rules have been inspected
- Missing protections were attempted to be enabled via API
- Any gaps that could not be fixed are documented with reasons
