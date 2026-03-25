# Finalize PR with Artifacts

Ensure CI generates visual artifacts, populate the PR `## Demo` section, document handoff
notes, verify all checkboxes are complete, and undraft the PR for review.

## Process

1. **Verify CI artifacts** — confirm the pipeline produced domain-appropriate visual artifacts
   (DOM snapshots, rendered STLs, logic traces, PDF renders, etc.). If CI does not produce
   artifacts, document the gap and manually capture equivalents.
2. **Populate `## Demo`** — add visual artifacts with captions and before/after
   comparisons where applicable
3. **Document handoff** — if the implementation unblocks downstream work or needs
   staging/production verification, add a `## Handoff` section; otherwise note "none"
4. **Verify checkboxes** — confirm every PR task checkbox is checked and matches the branch state
5. **Undraft and request review**:
   - MUST transition the PR from draft to ready-for-review (`gh pr ready [PR-URL]`)
   - Code owners (from `CODEOWNERS`) are automatically requested as reviewers — verify this happened
   - If the platform lacks automatic code owner assignment, manually request reviewers
   - The PR SHALL NOT be merged until peer review validates artifacts and checkboxes

## Output Format

### .deepwork/tmp/pr_finalization.md

```markdown
# PR Finalization

## CI Status
- Pipeline: [pass/fail/pending]
- Artifacts: [available/not available/manual]

## Visual Artifacts
| Artifact | Type | Location |
|----------|------|----------|
| [name] | [type] | [URL or path] |

## Demo Section
- Updated: yes/no
- Artifacts included: [N]

## Handoff
- Downstream implications: [yes/no]
- Details: [description or "none"]

## Checkboxes
- Total: [N], Checked: [N], Synchronized: yes/no

## Review
- PR undrafted: yes/no
- Code owner reviewers requested: [names or "not configured"]
- Base branch up to date: yes/no
```
