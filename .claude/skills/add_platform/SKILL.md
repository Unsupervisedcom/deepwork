---
name: add_platform
description: "Add a new AI platform to DeepWork with adapter, templates, and tests"
---

# add_platform

**Multi-step workflow**: Add a new AI platform to DeepWork with adapter, templates, and tests

> **CRITICAL**: Always invoke steps using the Skill tool. Never copy/paste step instructions directly.

A workflow for adding support for a new AI platform (like Cursor, Windsurf, etc.) to DeepWork.

The workflow ensures consistency across all supported platforms and maintains
comprehensive test coverage for new functionality. It starts with research to
capture the platform's configuration and hooks documentation, then adds any new
hook capabilities to the schema and existing adapters, implements the full adapter
with templates and tests, and finally verifies installation works correctly.

**Important Notes**:
- Only hooks available on slash command definitions should be captured
- Each existing adapter must be updated when new hooks are added (typically with null values)
- Tests must achieve 100% coverage for any new functionality
- Installation verification confirms the platform integrates correctly with existing jobs


## Available Steps

1. **research** - Capture CLI configuration and hooks system documentation for the new platform
2. **add_capabilities** - Update job schema and adapters with any new hook events the platform supports (requires: research)
3. **implement** - Add platform adapter, templates, tests with 100% coverage, and README documentation (requires: research, add_capabilities)
4. **verify** - Set up platform directories and verify deepwork install works correctly (requires: implement)

## Execution Instructions

### Step 1: Analyze Intent

Parse any text following `/add_platform` to determine user intent:
- "research" or related terms → start at `add_platform.research`
- "add_capabilities" or related terms → start at `add_platform.add_capabilities`
- "implement" or related terms → start at `add_platform.implement`
- "verify" or related terms → start at `add_platform.verify`

### Step 2: Invoke Starting Step

Use the Skill tool to invoke the identified starting step:
```
Skill tool: add_platform.research
```

### Step 3: Continue Workflow Automatically

After each step completes:
1. Check if there's a next step in the sequence
2. Invoke the next step using the Skill tool
3. Repeat until workflow is complete or user intervenes

### Handling Ambiguous Intent

If user intent is unclear, use AskUserQuestion to clarify:
- Present available steps as numbered options
- Let user select the starting point

## Context Files

- Job definition: `.deepwork/jobs/add_platform/job.yml`