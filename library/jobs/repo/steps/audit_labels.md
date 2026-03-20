# Audit Labels

## Objective

Deep audit of repository labels: verify required labels, find case-insensitive duplicates, identify zero-issue labels, and fix issues.

## Task

### Process

1. **Read existing labels** from `platform_context.md`

2. **Check required labels**
   - Required: `product`, `engineering`, `plan`
   - Create any that are missing (same as ensure_labels)

3. **Find case-insensitive duplicates**
   - Group all labels by lowercased name
   - Flag any groups with more than one label (e.g., `Bug` and `bug`)
   - Recommend which to keep (prefer lowercase)

4. **Find zero-issue labels**
   - For each label, count issues using it via the provider's CLI or API
   - Labels with zero issues are flagged as candidates for cleanup
   - Do NOT auto-delete — just flag them

5. **Fix case mismatches on required labels**
   - If a required label exists with wrong casing, rename it using the provider's label edit command

## Output Format

### labels_audit.md

```markdown
# Labels Audit

## Summary
- **Total Labels**: [count]
- **Required Labels OK**: [count]/3
- **Created**: [count]
- **Case Duplicates Found**: [count]
- **Zero-Issue Labels**: [count]

## Required Labels

| Label | Status | Action |
|-------|--------|--------|
| product | [ok \| created \| renamed] | [details] |
| engineering | [ok \| created \| renamed] | [details] |
| plan | [ok \| created \| renamed] | [details] |

## Case-Insensitive Duplicates

| Lowercase Name | Variants | Recommendation |
|----------------|----------|----------------|
| ... | Bug, bug | Keep "bug", delete "Bug" |

## Zero-Issue Labels

| Label | Created | Recommendation |
|-------|---------|----------------|
| ... | [date] | Consider removing |

## Actions Taken
- [List of changes made]

## Manual Actions Needed
- [List of changes requiring human intervention, or "None"]
```

## Quality Criteria

- All three required labels are verified
- Case-insensitive duplicates are identified
- Zero-issue labels are flagged
- Actions taken and remaining manual steps are documented
