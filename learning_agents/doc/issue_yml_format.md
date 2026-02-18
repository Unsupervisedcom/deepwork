# Issue File Format

Issue files track problems observed in LearningAgent sessions. They are stored in the session's agent log folder and processed during learning cycles.

## Filename

```
<short-name-roughly-describing-issue>.issue.yml
```

Use dashes and keep names brief but descriptive. Examples:
- `wrong-retry-strategy.issue.yml`
- `missed-edge-case-in-validation.issue.yml`
- `hallucinated-api-endpoint.issue.yml`

## Fields

```yaml
status: identified
seen_at_timestamps:
  - "2025-01-15T14:32:00Z"
  - "2025-01-15T14:45:00Z"
issue_description: |
  Freeform text explaining the thing that went wrong.
  This describes the PROBLEM, not the cause.
investigation_report: |
  Freeform text explaining the root cause of the reported issue.
  Should include specific line numbers of key evidence in the transcript.
  NOT present when the issue is first created.
```

### status

Tracks the issue through the learning lifecycle:

| Status | Meaning |
|--------|---------|
| `identified` | Issue observed but not yet researched further |
| `investigated` | Root cause understood; we know why it happened |
| `learned` | Learning has been incorporated into the LearningAgent |

### seen_at_timestamps

Array of ISO 8601 timestamps where the issue **manifested** (not root cause lines). These are either:
- The exact timestamp from the transcript line numbers, if reviewing transcript files
- The current time, if reporting the issue in real-time

### issue_description

Freeform text describing the observable problem. Focus on **what went wrong**, not why. Be specific enough that someone reading this can understand the failure without seeing the transcript.

### investigation_report

Freeform text explaining the **root cause** of the issue. Added during the `investigate_issues` step (not present when the issue is first created). Should include:
- Specific line numbers from the transcript as evidence
- Why the agent behaved incorrectly
- What knowledge gap or instruction deficiency caused the issue
