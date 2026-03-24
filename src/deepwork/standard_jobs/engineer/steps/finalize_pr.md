# Finalize PR with Artifacts

## Objective

Ensure CI generates visual artifacts, populate the PR #demo section with those artifacts,
document handoff notes, and verify all checkboxes are complete before requesting review.

## Task

Prepare the PR for peer review by ensuring all automated artifacts are captured, the demo
section showcases the changes, and any downstream implications are documented.

### Process

1. **Verify CI artifact generation**
   - Confirm the CI pipeline ran successfully on the latest push
   - Check that visual artifacts were generated (domain-appropriate):
     - Software: DOM snapshots, screenshot diffs, API response samples
     - Hardware/CAD: rendered STLs, compiled schematics, Gerber previews
     - Firmware: logic analyzer traces, memory maps
     - Docs: PDF renders, HTML previews
   - If CI does not generate artifacts, document this as a gap and manually capture equivalents

2. **Populate the #demo section**
   - Add the automatically generated visual artifacts to the PR's `## Demo` section
   - Include before/after comparisons where applicable
   - Add brief captions explaining what each artifact shows

3. **Document handoff notes**
   - If the implementation unblocks downstream work, document in a `## Handoff` section:
     - What is unblocked and for whom
     - Any staging/production verification needed
     - Migration steps if applicable
   - If no downstream implications exist, note this explicitly

4. **Final checkbox verification**
   - Verify every PR task checkbox is checked
   - Cross-reference against the engineering issue's implementation plan
   - Ensure the branch is up to date with the base branch

5. **Undraft and request review**
   - MUST transition the PR from draft to ready-for-review state
     - GitHub: `gh pr ready [PR-URL]`
     - Forgejo/Gitea: equivalent API call to remove WIP/draft status
   - Code owners (defined in `CODEOWNERS` or equivalent) are automatically requested as
     reviewers when the PR is undrafted — verify this happened
   - If the platform does not support automatic code owner assignment, manually request
     the appropriate reviewers
   - Note: the PR SHALL NOT be merged until peer review validates artifacts and checkboxes

### Domain Adaptation

| Concept          | Software              | Hardware/CAD           | Firmware              | Docs                 |
|------------------|-----------------------|------------------------|-----------------------|----------------------|
| CI artifacts     | DOM snapshots, tests  | STL renders, DRC      | HIL logs, .hex size  | PDF render, link check |
| Demo section     | Screenshots, GIFs     | 3D model views         | Logic traces          | Before/after content |
| Handoff          | Deploy instructions   | BOM update notes       | Flash instructions    | Publish instructions |

## Output Format

### .deepwork/tmp/pr_finalization.md

**Structure**:
```markdown
# PR Finalization

## CI Status
- Pipeline: [pass/fail/pending]
- Artifact generation: [available/not available/manual]

## Visual Artifacts
| Artifact | Type | Location |
|----------|------|----------|
| [artifact name] | [STL render/screenshot/trace/etc.] | [URL or path] |

## Demo Section
- Updated: yes/no
- Artifacts included: [N]
- Before/after comparisons: yes/no/not applicable

## Handoff
- Downstream implications: [yes/no]
- Details: [description or "none"]
- Staging verification needed: [yes/no]

## Checkbox State
- Total checkboxes: [N]
- Checked: [N]
- All synchronized: yes/no

## Review Readiness
- PR undrafted: yes/no
- Code owner reviewers requested: [names or "not configured"]
- Additional reviewers: [names or "none"]
- Base branch up to date: yes/no
```

## Quality Criteria

- CI artifacts are verified or manually captured
- The PR #demo section displays visual artifacts relevant to the domain
- Handoff notes document downstream implications (or explicitly state there are none)
- All PR checkboxes are checked and synchronized
- The PR is undrafted (transitioned to ready for review)
- Code owner reviewers are requested (or noted as not configured)
