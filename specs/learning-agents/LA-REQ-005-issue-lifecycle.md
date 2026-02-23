# LA-REQ-005: Issue Lifecycle

## Overview

Issues track problems observed in LearningAgent sessions. They progress through a defined lifecycle from identification through investigation to learning incorporation. Issue files use a YAML format and are stored in session log folders.

## Requirements

### LA-REQ-005.1: Issue File Location

Issue files MUST be stored in the session log folder at `.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/`.

### LA-REQ-005.2: Issue File Naming

Issue files MUST be named `<short-name-roughly-describing-issue>.issue.yml`. The short name MUST use dashes, be 3-6 words maximum, and descriptively identify the issue (e.g., `wrong-retry-strategy.issue.yml`).

### LA-REQ-005.3: Issue File Extension

Issue files MUST use the `.issue.yml` extension (not `.yaml` or `.yml` alone).

### LA-REQ-005.4: Status Field -- Required

Every issue file MUST contain a `status` field. The status field MUST be one of: `identified`, `investigated`, or `learned`.

### LA-REQ-005.5: Status Lifecycle

Issue status MUST progress through the lifecycle in order: `identified` -> `investigated` -> `learned`. A status MUST NOT be set to a previous stage (no regressions). The status MUST NOT skip stages (e.g., going directly from `identified` to `learned`).

### LA-REQ-005.6: Initial Status

When an issue file is first created, the `status` field MUST be set to `identified`.

### LA-REQ-005.7: Seen-At Timestamps Field

Every issue file MUST contain a `seen_at_timestamps` field as an array of ISO 8601 timestamp strings. Each timestamp represents when the issue manifested (not the root cause location).

### LA-REQ-005.8: Seen-At Timestamps -- Source

Timestamps in `seen_at_timestamps` MUST be either:
- The exact timestamp from the transcript line numbers (when reviewing transcript files)
- The current UTC time (when reporting the issue in real-time)

### LA-REQ-005.9: Issue Description Field

Every issue file MUST contain an `issue_description` field with freeform text. The description MUST describe the observable problem (what went wrong), NOT the root cause (why it happened). It MUST be specific enough that a reader can understand the failure without seeing the transcript.

### LA-REQ-005.10: Investigation Report Field -- Conditional

The `investigation_report` field MUST NOT be present when the issue is first created (status: `identified`). It MUST be added when the status transitions to `investigated`.

### LA-REQ-005.11: Investigation Report Content

The `investigation_report` field MUST contain:
- Specific line numbers from the transcript as evidence
- An explanation of why the agent behaved incorrectly
- Identification of the knowledge gap or instruction deficiency that caused the issue

### LA-REQ-005.12: Issue File YAML Structure

The issue file MUST be valid YAML with the following structure:
```yaml
status: <identified|investigated|learned>
seen_at_timestamps:
  - "<ISO 8601 timestamp>"
issue_description: |
  <freeform text>
investigation_report: |
  <freeform text, only when investigated or learned>
```

### LA-REQ-005.13: No Duplicate Issues

The system MUST NOT create duplicate issue files for the same problem within a single session. The identify skill MUST check for existing issues before creating new ones.
