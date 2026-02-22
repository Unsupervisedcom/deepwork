# REQ-010: Issue Reporting

## Overview

The `report-issue` skill creates individual issue files documenting problems observed in LearningAgent sessions. It is used both programmatically by the `identify` skill and interactively via `/learning-agents report_issue`.

## Requirements

### REQ-010.1: Skill Visibility

The `report-issue` skill MUST NOT be directly invocable by the user (`user-invocable: false`). It is invoked by the `identify` skill and routed through the main `/learning-agents report_issue` dispatcher.

### REQ-010.2: Input Arguments

The skill MUST accept two arguments:
- `$0`: Path to the session log folder (e.g., `.deepwork/tmp/agent_sessions/<session_id>/<agent_id>/`)
- `$1`: Brief description of the issue observed

### REQ-010.3: Missing Folder Path Validation

If `$0` is not provided or does not point to an existing directory, the skill MUST stop and output: `"Error: session log folder path is required and must be an existing directory."`

### REQ-010.4: Missing Description Validation

If `$1` is not provided or is empty, the skill MUST stop and output: `"Error: issue description is required."`

### REQ-010.5: Issue Name Derivation

The skill MUST derive a kebab-case filename of 3-6 words maximum from the issue description. The name MUST focus on the most distinctive noun and verb from the failure and MUST avoid filler words like "the", "a", "in", "with".

### REQ-010.6: Issue File Creation

The skill MUST create the issue file at `$0/<issue-name>.issue.yml` with the following fields:
- `status: identified`
- `seen_at_timestamps`: array containing a single current ISO 8601 UTC timestamp
- `issue_description`: freeform text derived from the `$1` argument

### REQ-010.7: Issue Description Content

The `issue_description` field MUST focus on the observable problem (symptoms), NOT the root cause. It MUST be specific enough that someone can understand the failure without seeing the transcript.

### REQ-010.8: No Investigation Report

The created issue file MUST NOT include an `investigation_report` field. That field is added during the investigate step.

### REQ-010.9: Status Must Be Identified

The `status` field MUST be set to `identified`. The skill MUST NOT set any other status value.

### REQ-010.10: No Other File Modifications

The skill MUST NOT modify any other files in the session folder or elsewhere. Only the new issue file is created.

### REQ-010.11: Confirmation Output

After creating the issue file, the skill MUST output a two-line confirmation:
- `Created: <path to the created issue file>`
- `Recorded: <one-sentence summary of the issue>`
