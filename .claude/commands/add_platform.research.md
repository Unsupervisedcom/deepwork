---
description: Capture CLI configuration and hooks system documentation for the new platform
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            You must evaluate whether Claude has met all the below quality criteria for the request.

            ## Quality Criteria

            Verify the research output meets ALL criteria:
            1. Both files exist in doc/platforms/<platform>/: cli_configuration.md and hooks_system.md
            2. Each file has a comment at the top with:
               - Last updated date
               - Source URL where the documentation was obtained
            3. cli_configuration.md covers how the platform's CLI is configured
            4. hooks_system.md covers hooks available for slash command definitions ONLY
            5. No extraneous documentation (only these two specific topics)
            6. Documentation is comprehensive enough to implement the platform

            If ALL criteria are met, include `<promise>QUALITY_COMPLETE</promise>`.


            ## Instructions

            Review the conversation and determine if ALL quality criteria above have been satisfied.
            Look for evidence that each criterion has been addressed.

            If the agent has included `<promise>QUALITY_COMPLETE</promise>` in their response AND
            all criteria appear to be met, respond with: {"ok": true}

            If criteria are NOT met AND the promise tag is missing, respond with:
            {"ok": false, "reason": "Continue working. [specific feedback on what's wrong]"}
---

# add_platform.research

**Step 1 of 4** in the **add_platform** workflow

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



## Instructions

# Research Platform Documentation

## Objective

Capture comprehensive documentation for the new AI platform's CLI configuration and hooks system, creating a local reference that will guide the implementation phases.

## Task

Research the target platform's official documentation and create two focused documentation files that will serve as the foundation for implementing platform support in DeepWork.

### Process

1. **Identify the platform's documentation sources**
   - Find the official documentation website
   - Locate the CLI/agent configuration documentation
   - Find the hooks or customization system documentation
   - Note: Focus ONLY on slash command/custom command hooks, not general CLI hooks

2. **Gather CLI configuration documentation**
   - How is the CLI configured? (config files, environment variables, etc.)
   - Where are custom commands/skills stored?
   - What is the command file format? (markdown, YAML, etc.)
   - What metadata or frontmatter is supported?
   - How does the platform discover and load commands?

3. **Gather hooks system documentation**
   - What hooks are available for custom command definitions?
   - Focus on hooks that trigger during or after command execution
   - Examples: `stop_hooks`, `pre_hooks`, `post_hooks`, validation hooks
   - Document the syntax and available hook types
   - **Important**: Only document hooks available on slash command definitions, not general CLI hooks

4. **Create the documentation files**
   - Place files in `doc/platforms/<platform_name>/`
   - Each file must have a header comment with source and date
   - Content should be comprehensive but focused

## Output Format

### cli_configuration.md

Located at: `doc/platforms/<platform_name>/cli_configuration.md`

**Structure**:
```markdown
<!--
Last Updated: YYYY-MM-DD
Source: [URL where this documentation was obtained]
-->

# <Platform Name> CLI Configuration

## Overview

[Brief description of the platform and its CLI/agent system]

## Configuration Files

[Document where configuration lives and its format]

### File Locations

- [Location 1]: [Purpose]
- [Location 2]: [Purpose]

### Configuration Format

[Show the configuration file format with examples]

## Custom Commands/Skills

[Document how custom commands are defined]

### Command Location

[Where command files are stored]

### Command File Format

[The format of command files - markdown, YAML, etc.]

### Metadata/Frontmatter

[What metadata fields are supported in command files]

```[format]
[Example of a minimal command file]
```

## Command Discovery

[How the platform discovers and loads commands]

## Platform-Specific Features

[Any unique features relevant to command configuration]
```

### hooks_system.md

Located at: `doc/platforms/<platform_name>/hooks_system.md`

**Structure**:
```markdown
<!--
Last Updated: YYYY-MM-DD
Source: [URL where this documentation was obtained]
-->

# <Platform Name> Hooks System (Command Definitions)

## Overview

[Brief description of hooks available for command definitions]

**Important**: This document covers ONLY hooks available within slash command/skill definitions, not general CLI hooks.

## Available Hooks

### [Hook Name 1]

**Purpose**: [What this hook does]

**Syntax**:
```yaml
[hook_name]:
  - [configuration]
```

**Example**:
```yaml
[Complete example of using this hook]
```

**Behavior**: [When and how this hook executes]

### [Hook Name 2]

[Repeat for each available hook]

## Hook Execution Order

[Document the order in which hooks execute, if multiple are supported]

## Comparison with Other Platforms

| Feature | <Platform> | Claude Code | Other |
|---------|-----------|-------------|-------|
| [Feature 1] | [Support] | [Support] | [Support] |

## Limitations

[Any limitations or caveats about the hooks system]
```

## Quality Criteria

- Both files exist in `doc/platforms/<platform_name>/`
- Each file has a header comment with:
  - Last updated date (YYYY-MM-DD format)
  - Source URL where documentation was obtained
- `cli_configuration.md` comprehensively covers:
  - Configuration file locations and format
  - Custom command file format and location
  - Command discovery mechanism
- `hooks_system.md` comprehensively covers:
  - All hooks available for slash command definitions
  - Syntax and examples for each hook
  - NOT general CLI hooks (only command-level hooks)
- Documentation is detailed enough to implement the platform adapter
- No extraneous topics (only CLI config and command hooks)
- When all criteria are met, include `<promise>QUALITY_COMPLETE</promise>` in your response

## Context

This is the foundation step for adding a new platform to DeepWork. The documentation you capture here will be referenced throughout the implementation process:
- CLI configuration informs how to generate command files
- Hooks documentation determines what features the adapter needs to support
- This documentation becomes a permanent reference in `doc/platforms/`

Take time to be thorough - incomplete documentation will slow down subsequent steps.

## Tips

- Use the platform's official documentation as the primary source
- If documentation is sparse, check GitHub repos, community guides, or changelog entries
- When in doubt about whether something is a "command hook" vs "CLI hook", err on the side of inclusion and note the ambiguity
- Include code examples from the official docs where available


## Inputs

### User Parameters

Please gather the following information from the user:
- **platform_name**: Clear identifier of the platform (e.g., 'cursor', 'windsurf-editor', 'github-copilot-chat')


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
- `deepwork/add_platform/cli_configuration.md`- `deepwork/add_platform/hooks_system.md`
Ensure all outputs are:
- Well-formatted and complete
- Committed to the work branch
- Ready for review or use by subsequent steps

## Quality Validation Loop

This step uses an iterative quality validation loop. After completing your work, stop hook(s) will evaluate whether the outputs meet quality criteria. If criteria are not met, you will be prompted to continue refining.

### Quality Criteria
Verify the research output meets ALL criteria:
1. Both files exist in doc/platforms/<platform>/: cli_configuration.md and hooks_system.md
2. Each file has a comment at the top with:
   - Last updated date
   - Source URL where the documentation was obtained
3. cli_configuration.md covers how the platform's CLI is configured
4. hooks_system.md covers hooks available for slash command definitions ONLY
5. No extraneous documentation (only these two specific topics)
6. Documentation is comprehensive enough to implement the platform

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
   git commit -m "add_platform: Complete research step"
   ```

2. **Verify outputs**: Confirm all required files have been created

3. **Inform the user**:
   - Step 1 of 4 is complete
   - Outputs created: cli_configuration.md, hooks_system.md
   - Ready to proceed to next step: `/add_platform.add_capabilities`

## Next Step

To continue the workflow, run:
```
/add_platform.add_capabilities
```

---

## Context Files

- Job definition: `.deepwork/jobs/add_platform/job.yml`
- Step instructions: `.deepwork/jobs/add_platform/steps/research.md`