---
description: Add a new AI platform to DeepWork with adapter, templates, and tests
---

# add_platform

You are executing the **add_platform** job. Add a new AI platform to DeepWork with adapter, templates, and tests

A workflow for adding support for a new AI platform (like Cursor, Windsurf, etc.) to DeepWork.

This job guides you through four phases:
1. **Research**: Capture the platform's CLI configuration and hooks system documentation
2. **Add Capabilities**: Update the job schema and adapters with any new hook events
3. **Implement**: Create the platform adapter, templates, tests (100% coverage), and README updates
4. **Verify**: Ensure installation works correctly and produces expected files

The workflow ensures consistency across all supported platforms and maintains
comprehensive test coverage for new functionality.

**Important Notes**:
- Only hooks available on slash command definitions should be captured
- Each existing adapter must be updated when new hooks are added (typically with null values)
- Tests must achieve 100% coverage for any new functionality
- Installation verification confirms the platform integrates correctly with existing jobs


## Available Steps

This job has 4 step(s):

### research
**Research Platform Documentation**: Capture CLI configuration and hooks system documentation for the new platform
- Command: `add_platform.research`
### add_capabilities
**Add Hook Capabilities**: Update job schema and adapters with any new hook events the platform supports
- Command: `add_platform.add_capabilities`
- Requires: research
### implement
**Implement Platform Support**: Add platform adapter, templates, tests with 100% coverage, and README documentation
- Command: `add_platform.implement`
- Requires: research, add_capabilities
### verify
**Verify Installation**: Set up platform directories and verify deepwork install works correctly
- Command: `add_platform.verify`
- Requires: implement

## Instructions

This is a **multi-step workflow**. Determine the starting point and run through the steps in sequence.

1. **Analyze user intent** from the text that follows `/add_platform`

2. **Identify the starting step** based on intent:
   - research: Capture CLI configuration and hooks system documentation for the new platform
   - add_capabilities: Update job schema and adapters with any new hook events the platform supports
   - implement: Add platform adapter, templates, tests with 100% coverage, and README documentation
   - verify: Set up platform directories and verify deepwork install works correctly

3. **Run the workflow** starting from the identified step:
   - Invoke the starting step using the Skill tool
   - When that step completes, **automatically continue** to the next step in the workflow
   - Continue until the workflow is complete or the user intervenes

4. **If intent is ambiguous**, ask the user which step to start from:
   - Present the available steps as numbered options
   - Use AskUserQuestion to let them choose

**Critical**:
- You MUST invoke each step using the Skill tool. Do not copy/paste step instructions.
- After each step completes, check if there's a next step and invoke it automatically.
- The workflow continues until all dependent steps are complete.

## Context Files

- Job definition: `.deepwork/jobs/add_platform/job.yml`