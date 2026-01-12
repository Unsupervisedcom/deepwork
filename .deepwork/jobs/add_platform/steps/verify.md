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
