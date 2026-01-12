---
description: Set up platform directories and verify deepwork install works correctly
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            You must evaluate whether Claude has met all the below quality criteria for the request.

            ## Quality Criteria

            Verify the installation meets ALL criteria:
            1. Platform-specific directories/files are added to the deepwork repo as needed
            2. Running `deepwork install --platform <platform>` completes without errors
            3. Expected command files are created in the platform's command directory
            4. Command file content matches the templates and job definitions
            5. Established DeepWork jobs (deepwork_jobs, deepwork_policy) are installed correctly
            6. The platform can be used alongside existing platforms without conflicts

            If ALL criteria are met, include `<promise>QUALITY_COMPLETE</promise>`.


            ## Instructions

            Review the conversation and determine if ALL quality criteria above have been satisfied.
            Look for evidence that each criterion has been addressed.

            If the agent has included `<promise>QUALITY_COMPLETE</promise>` in their response AND
            all criteria appear to be met, respond with: {"ok": true}

            If criteria are NOT met AND the promise tag is missing, respond with:
            {"ok": false, "reason": "Continue working. [specific feedback on what's wrong]"}
---

# add_platform.verify

**Step 4 of 4** in the **add_platform** workflow

**Summary**: Add a new AI platform to DeepWork with adapter, templates, and tests

## Job Overview

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


## Prerequisites

This step requires completion of the following step(s):
- `/add_platform.implement`

Please ensure these steps have been completed before proceeding.

## Instructions

# Verify Installation

## Objective

Ensure the new platform integration works correctly by setting up necessary directories and running the full installation process.

## Task

Perform end-to-end verification that the new platform can be installed and that DeepWork's standard jobs work correctly with it.

### Prerequisites

Ensure the implementation step is complete:
- Adapter class exists in `src/deepwork/adapters.py`
- Templates exist in `src/deepwork/templates/<platform_name>/`
- Tests pass with 100% coverage
- README.md is updated

### Process

1. **Set up platform directories in the DeepWork repo**

   The DeepWork repository itself should have the platform's command directory structure for testing:

   ```bash
   mkdir -p <platform_command_directory>
   ```

   For example:
   - Claude: `.claude/commands/`
   - Cursor: `.cursor/commands/` (or wherever Cursor stores commands)

2. **Run deepwork install for the new platform**

   ```bash
   deepwork install --platform <platform_name>
   ```

   Verify:
   - Command completes without errors
   - No Python exceptions or tracebacks
   - Output indicates successful installation

3. **Check that command files were created**

   List the generated command files:
   ```bash
   ls -la <platform_command_directory>/
   ```

   Verify:
   - `deepwork_jobs.define.md` exists (or equivalent for the platform)
   - `deepwork_jobs.implement.md` exists
   - `deepwork_jobs.refine.md` exists
   - `deepwork_policy.define.md` exists
   - All expected step commands exist

4. **Validate command file content**

   Read each generated command file and verify:
   - Content matches the expected format for the platform
   - Job metadata is correctly included
   - Step instructions are properly rendered
   - Any platform-specific features (hooks, frontmatter) are present

5. **Test alongside existing platforms**

   If other platforms are already installed, verify they still work:
   ```bash
   deepwork install --platform claude
   ls -la .claude/commands/
   ```

   Ensure:
   - New platform doesn't break existing installations
   - Each platform's commands are independent
   - No file conflicts or overwrites

6. **Document verification results**

   Create a verification report documenting what was tested and the results.

## Output Format

### verification_complete.md

Location: `deepwork/add_platform/verification_complete.md` (in work directory)

**Structure**:
```markdown
# Platform Verification Complete: <platform_name>

## Summary

**Platform**: <platform_name>
**Date**: YYYY-MM-DD
**Status**: PASSED / FAILED

## Installation Test

### Command Executed
```bash
deepwork install --platform <platform_name>
```

### Result
- Exit code: 0
- Errors: None
- Warnings: [any warnings]

## Generated Files

### Command Directory: <path>

| File | Status | Notes |
|------|--------|-------|
| deepwork_jobs.define.md | Created | [size, any notes] |
| deepwork_jobs.implement.md | Created | [size, any notes] |
| deepwork_jobs.refine.md | Created | [size, any notes] |
| deepwork_policy.define.md | Created | [size, any notes] |

## Content Validation

### Sample Command File Review

**File**: deepwork_jobs.define.md

- [ ] Correct frontmatter/metadata for platform
- [ ] Job summary included
- [ ] Step instructions rendered correctly
- [ ] Platform-specific hooks present (if applicable)

### Format Compliance

- [ ] Files match platform's expected command format
- [ ] No template rendering errors
- [ ] All placeholders resolved

## Cross-Platform Compatibility

### Other Platforms Tested

| Platform | Still Works | Notes |
|----------|-------------|-------|
| claude | Yes/No | [any issues] |

## Conclusion

[Summary of verification results and any recommendations]

## Next Steps

- [ ] Platform is ready for use
- [ ] Consider adding to CI/CD pipeline
- [ ] Update any additional documentation
```

## Quality Criteria

- Platform-specific directories are set up in the DeepWork repo
- `deepwork install --platform <platform_name>` completes without errors
- All expected command files are created:
  - deepwork_jobs.define, implement, refine
  - deepwork_policy.define
  - Any other standard job commands
- Command file content is correct:
  - Matches platform's expected format
  - Job/step information is properly rendered
  - No template errors or missing content
- Existing platforms still work (if applicable)
- No conflicts between platforms
- `verification_complete.md` documents all test results
- When all criteria are met, include `<promise>QUALITY_COMPLETE</promise>` in your response

## Context

This is the final validation step before the platform is considered complete. A thorough verification ensures:
- The platform actually works, not just compiles
- Standard DeepWork jobs install correctly
- The platform integrates properly with the existing system
- Users can confidently use the new platform

Take time to verify each aspect - finding issues now is much better than having users discover them later.

## Common Issues to Check

- **Template syntax errors**: May only appear when rendering specific content
- **Path issues**: Platform might expect different directory structure
- **Encoding issues**: Special characters in templates or content
- **Missing hooks**: Platform adapter might not handle all hook types
- **Permission issues**: Directory creation might fail in some cases


## Inputs


### Required Files

This step requires the following files from previous steps:
- `templates/` (from step `implement`)
  Location: `deepwork/add_platform/templates/`

Make sure to read and use these files as context for this step.

## Work Branch Management

All work for this job should be done on a dedicated work branch:

1. **Check current branch**:
   - If already on a work branch for this job (format: `deepwork/add_platform-[instance]-[date]`), continue using it
   - If on main/master, create a new work branch

2. **Create work branch** (if needed):
   ```bash
   git checkout -b deepwork/add_platform-[instance]-$(date +%Y%m%d)
   ```
   Replace `[instance]` with a descriptive identifier (e.g., `acme`, `q1-launch`, etc.)

3. **All outputs go in the work directory**:
   - Create files in: `deepwork/add_platform/`
   - This keeps work products organized by job

## Output Requirements

Create the following output(s) in the work directory:
- `deepwork/add_platform/verification_complete.md`
Ensure all outputs are:
- Well-formatted and complete
- Committed to the work branch
- Ready for review or use by subsequent steps

## Quality Validation Loop

This step uses an iterative quality validation loop. After completing your work, stop hook(s) will evaluate whether the outputs meet quality criteria. If criteria are not met, you will be prompted to continue refining.

### Quality Criteria
Verify the installation meets ALL criteria:
1. Platform-specific directories/files are added to the deepwork repo as needed
2. Running `deepwork install --platform <platform>` completes without errors
3. Expected command files are created in the platform's command directory
4. Command file content matches the templates and job definitions
5. Established DeepWork jobs (deepwork_jobs, deepwork_policy) are installed correctly
6. The platform can be used alongside existing platforms without conflicts

If ALL criteria are met, include `<promise>QUALITY_COMPLETE</promise>`.


### Completion Promise

To signal that all quality criteria have been met, include this tag in your final response:

```
<promise>QUALITY_COMPLETE</promise>
```

**Important**: Only include this promise tag when you have verified that ALL quality criteria above are satisfied. The validation loop will continue until this promise is detected.

## Completion

After completing this step:

1. **Commit your work**:
   ```bash
   git add deepwork/add_platform/
   git commit -m "add_platform: Complete verify step"
   ```

2. **Verify outputs**: Confirm all required files have been created

3. **Inform the user**:
   - Step 4 of 4 is complete
   - Outputs created: verification_complete.md
   - This is the final step - the job is complete!

## Workflow Complete

This is the final step in the add_platform workflow. All outputs should now be complete and ready for review.

Consider:
- Reviewing all work products in `deepwork/add_platform/`
- Creating a pull request to merge the work branch
- Documenting any insights or learnings

---

## Context Files

- Job definition: `.deepwork/jobs/add_platform/job.yml`
- Step instructions: `.deepwork/jobs/add_platform/steps/verify.md`