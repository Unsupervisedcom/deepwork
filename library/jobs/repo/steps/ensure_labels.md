# Ensure Labels

## Objective

Verify that the three required labels (`product`, `engineering`, `plan`) exist on the repository. Create any that are missing.

## Task

### Process

1. **Read existing labels** from `platform_context.md`

2. **Check for required labels**
   - Required: `product`, `engineering`, `plan`
   - Match case-insensitively against existing labels
   - If an exact-case match exists, mark as present
   - If a case-insensitive match exists but with wrong casing, note the discrepancy

3. **Create missing labels**
   - Use the provider's label creation CLI or API
   - Recommended colors and descriptions:
     - `product` — color `#7057ff`, description "Product/UX scope"
     - `engineering` — color `#0075ca`, description "Technical scope"
     - `plan` — color `#e4e669`, description "Planning/coordination"

4. **Verify creation**
   - Re-list labels to confirm the new labels exist

## Output Format

### labels_report.md

```markdown
# Labels Report

## Summary
- **Required Labels**: 3
- **Already Present**: [count]
- **Created**: [count]
- **Case Mismatches**: [count]

## Details

| Label | Status | Notes |
|-------|--------|-------|
| product | [present \| created \| case mismatch] | [details] |
| engineering | [present \| created \| case mismatch] | [details] |
| plan | [present \| created \| case mismatch] | [details] |
```

## Quality Criteria

- All three required labels are accounted for
- Missing labels were created with appropriate colors and descriptions
- Case mismatches are documented
