---
name: add_platform
description: "Adds a new AI platform to DeepWork with adapter, templates, and tests. Use when integrating Cursor, Windsurf, or other AI coding tools."
---

# add_platform Agent

Adds a new AI platform to DeepWork with adapter, templates, and tests. Use when integrating Cursor, Windsurf, or other AI coding tools.

A workflow for adding support for a new AI platform (like Cursor, Windsurf, etc.) to DeepWork.

The **integrate** workflow guides you through four phases:
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


## Agent Overview

This agent handles the **add_platform** job with 4 skills.

**Workflows**: integrate
---

## How to Use This Agent

### Workflows
- **integrate**: Full workflow to integrate a new AI platform into DeepWork (research → add_capabilities → implement → verify)
  - Start: `research`

### All Skills
- `research` - Captures CLI configuration and hooks system documentation for the new platform. Use when starting platform integration.
- `add_capabilities` - Updates job schema and adapters with any new hook events the platform supports. Use after research to extend DeepWork's hook system.
- `implement` - Creates platform adapter, templates, tests with 100% coverage, and README documentation. Use after adding hook capabilities.
- `verify` - Sets up platform directories and verifies deepwork install works correctly. Use after implementation to confirm integration.

---

## Agent Execution Instructions

When invoked, follow these steps:

### Step 1: Understand Intent

Parse the user's request to determine:
1. Which workflow or skill to execute
2. Any parameters or context provided
3. Whether this is a continuation of previous work

### Step 2: Check Work Branch

Before executing any skill:
1. Check current git branch
2. If on a `deepwork/add_platform-*` branch: continue using it
3. If on main/master: create new branch `deepwork/add_platform-[instance]-$(date +%Y%m%d)`

### Step 3: Execute the Appropriate Skill

Navigate to the relevant skill section below and follow its instructions.

### Step 4: Workflow Continuation

After completing a workflow step:
1. Inform the user of completion and outputs created
2. Automatically proceed to the next step if one exists
3. Continue until the workflow is complete or the user intervenes

---

## Skills

### Skill: research

**Type**: Workflow step 1/4 in **integrate**

**Description**: Captures CLI configuration and hooks system documentation for the new platform. Use when starting platform integration.


#### Required User Input

Gather these from the user before starting:
- **platform_name**: Clear identifier of the platform (e.g., 'cursor', 'windsurf-editor', 'github-copilot-chat')


#### Instructions

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
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

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


#### Outputs

Create these files/directories:
- `cli_configuration.md`- `hooks_system.md`

#### On Completion

1. Verify outputs are created
2. Inform user: "research complete, outputs: cli_configuration.md, hooks_system.md"
3. **Continue to next skill**: Proceed to `add_capabilities`

---

### Skill: add_capabilities

**Type**: Workflow step 2/4 in **integrate**

**Description**: Updates job schema and adapters with any new hook events the platform supports. Use after research to extend DeepWork's hook system.

#### Prerequisites

Before running this skill, ensure these are complete:
- `research`


#### Input Files

Read these files (from previous steps):
- `hooks_system.md` (from `research`)

#### Instructions

# Add Hook Capabilities

## Objective

Update the DeepWork job schema and platform adapters to support any new hook events that the new platform provides for slash command definitions.

## Task

Analyze the hooks documentation from the research step and update the codebase to support any new hook capabilities, ensuring consistency across all existing adapters.

### Prerequisites

Read the hooks documentation created in the previous step:
- `doc/platforms/<platform_name>/hooks_system.md`

Also review the existing schema and adapters:
- `src/deepwork/schemas/job_schema.py`
- `src/deepwork/adapters.py`

### Process

1. **Analyze the new platform's hooks**
   - Read `doc/platforms/<platform_name>/hooks_system.md`
   - List all hooks available for slash command definitions
   - Compare with hooks already in `job_schema.py`
   - Identify any NEW hooks not currently supported

2. **Determine if schema changes are needed**
   - If the platform has hooks that DeepWork doesn't currently support, add them
   - If all hooks are already supported, document this finding
   - Remember: Only add hooks that are available on slash command definitions

3. **Update job_schema.py (if needed)**
   - Add new hook fields to the step schema
   - Follow existing patterns for hook definitions
   - Add appropriate type hints and documentation
   - Example addition:
     ```python
     # New hook from <platform>
     new_hook_name: Optional[List[HookConfig]] = None
     ```

4. **Update all existing adapters**
   - Open `src/deepwork/adapters.py`
   - For EACH existing adapter class:
     - Add the new hook field (set to `None` if not supported)
     - This maintains consistency across all adapters
   - Document why each adapter does or doesn't support the hook

5. **Validate the changes**
   - Run Python syntax check: `python -m py_compile src/deepwork/schemas/job_schema.py`
   - Run Python syntax check: `python -m py_compile src/deepwork/adapters.py`
   - Ensure no import errors

6. **Document the decision**
   - If no new hooks were added, add a comment explaining why
   - If new hooks were added, ensure they're documented in the schema

## Output Format

### job_schema.py

Location: `src/deepwork/schemas/job_schema.py`

If new hooks are added:
```python
@dataclass
class StepDefinition:
    # ... existing fields ...

    # New hook from <platform_name> - [description of what it does]
    new_hook_name: Optional[List[HookConfig]] = None
```

### adapters.py

Location: `src/deepwork/adapters.py`

For each existing adapter, add the new hook field:
```python
class ExistingPlatformAdapter(PlatformAdapter):
    # ... existing code ...

    def get_hook_support(self) -> dict:
        return {
            # ... existing hooks ...
            "new_hook_name": None,  # Not supported by this platform
        }
```

Or if no changes are needed, add a documentation comment:
```python
# NOTE: <platform_name> hooks reviewed on YYYY-MM-DD
# No new hooks to add - all <platform_name> command hooks are already
# supported by the existing schema (stop_hooks covers their validation pattern)
```

## Quality Criteria

- Hooks documentation from research step has been reviewed
- If new hooks exist:
  - Added to `src/deepwork/schemas/job_schema.py` with proper typing
  - ALL existing adapters updated in `src/deepwork/adapters.py`
  - Each adapter indicates support level (implemented, None, or partial)
- If no new hooks needed:
  - Decision documented with a comment explaining the analysis
- Only hooks available on slash command definitions are considered
- `job_schema.py` has no syntax errors (verified with py_compile)
- `adapters.py` has no syntax errors (verified with py_compile)
- All adapters have consistent hook fields (same fields across all adapters)
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

DeepWork supports multiple AI platforms, and each platform may have different capabilities for hooks within command definitions. The schema defines what hooks CAN exist, while adapters define what each platform actually SUPPORTS.

This separation allows:
- Job definitions to use any hook (the schema is the superset)
- Platform-specific generation to only use supported hooks (adapters filter)
- Future platforms to add new hooks without breaking existing ones

Maintaining consistency is critical - all adapters must have the same hook fields, even if they don't support them (use `None` for unsupported).

## Common Hook Types

For reference, here are common hook patterns across platforms:

| Hook Type | Purpose | Example Platforms |
|-----------|---------|-------------------|
| `stop_hooks` | Quality validation loops | Claude Code |
| `pre_hooks` | Run before command | Various |
| `post_hooks` | Run after command | Various |
| `validation_hooks` | Validate inputs/outputs | Various |

When you find a new hook type, consider whether it maps to an existing pattern or is genuinely new functionality.


#### Outputs

Create these files/directories:
- `job_schema.py`- `adapters.py`

#### On Completion

1. Verify outputs are created
2. Inform user: "add_capabilities complete, outputs: job_schema.py, adapters.py"
3. **Continue to next skill**: Proceed to `implement`

---

### Skill: implement

**Type**: Workflow step 3/4 in **integrate**

**Description**: Creates platform adapter, templates, tests with 100% coverage, and README documentation. Use after adding hook capabilities.

#### Prerequisites

Before running this skill, ensure these are complete:
- `research`
- `add_capabilities`


#### Input Files

Read these files (from previous steps):
- `job_schema.py` (from `add_capabilities`)
- `adapters.py` (from `add_capabilities`)
- `cli_configuration.md` (from `research`)

#### Instructions

# Implement Platform Support

## Objective

Create the complete platform implementation including the adapter class, command templates, comprehensive tests, and documentation updates.

## Task

Build the full platform support by implementing the adapter, creating templates, writing tests with 100% coverage, and updating the README.

### Prerequisites

Read the outputs from previous steps:
- `doc/platforms/<platform_name>/cli_configuration.md` - For template structure
- `src/deepwork/schemas/job_schema.py` - For current schema
- `src/deepwork/adapters.py` - For adapter patterns

Also review existing implementations for reference:
- `src/deepwork/templates/claude/` - Example templates
- `tests/` - Existing test patterns

### Process

1. **Create the platform adapter class**

   Add a new adapter class to `src/deepwork/adapters.py`:

   ```python
   class NewPlatformAdapter(PlatformAdapter):
       """Adapter for <Platform Name>."""

       platform_name = "<platform_name>"
       command_directory = "<path to commands>"  # e.g., ".cursor/commands"
       command_extension = ".md"  # or appropriate extension

       def get_hook_support(self) -> dict:
           """Return which hooks this platform supports."""
           return {
               "stop_hooks": True,  # or False/None
               # ... other hooks
           }

       def generate_command(self, step: StepDefinition, job: JobDefinition) -> str:
           """Generate command file content for this platform."""
           # Use Jinja2 template
           template = self.env.get_template(f"{self.platform_name}/command.md.j2")
           return template.render(step=step, job=job)
   ```

2. **Create command templates**

   Create templates in `src/deepwork/templates/<platform_name>/`:

   - `command.md.j2` - Main command template
   - Any other templates needed for the platform's format

   Use the CLI configuration documentation to ensure the template matches the platform's expected format.

3. **Register the adapter**

   Update the adapter registry in `src/deepwork/adapters.py`:

   ```python
   PLATFORM_ADAPTERS = {
       "claude": ClaudeAdapter,
       "<platform_name>": NewPlatformAdapter,
       # ... other adapters
   }
   ```

4. **Write comprehensive tests**

   Create tests in `tests/` that cover:

   - Adapter instantiation
   - Hook support detection
   - Command generation
   - Template rendering
   - Edge cases (empty inputs, special characters, etc.)
   - Integration with the sync command

   **Critical**: Tests must achieve 100% coverage of new code.

5. **Update README.md**

   Add the new platform to `README.md`:

   - Add to "Supported Platforms" list
   - Add installation instructions:
     ```bash
     deepwork install --platform <platform_name>
     ```
   - Document any platform-specific notes or limitations

6. **Run tests and verify coverage**

   ```bash
   uv run pytest --cov=src/deepwork --cov-report=term-missing
   ```

   - All tests must pass
   - New code must have 100% coverage
   - If coverage is below 100%, add more tests

7. **Iterate until tests pass with full coverage**

   This step has a `stop_hooks` script that runs tests. Keep iterating until:
   - All tests pass
   - Coverage is 100% for new functionality

## Output Format

### templates/

Location: `src/deepwork/templates/<platform_name>/`

Create the following files:

**command.md.j2**:
```jinja2
{# Template for <platform_name> command files #}
{# Follows the platform's expected format from cli_configuration.md #}

[Platform-specific frontmatter or metadata]

# {{ step.name }}

{{ step.description }}

## Instructions

{{ step.instructions_content }}

[... rest of template based on platform format ...]
```

### tests/

Location: `tests/test_<platform_name>_adapter.py`

```python
"""Tests for the <platform_name> adapter."""
import pytest
from deepwork.adapters import NewPlatformAdapter

class TestNewPlatformAdapter:
    """Test suite for NewPlatformAdapter."""

    def test_adapter_initialization(self):
        """Test adapter can be instantiated."""
        adapter = NewPlatformAdapter()
        assert adapter.platform_name == "<platform_name>"

    def test_hook_support(self):
        """Test hook support detection."""
        adapter = NewPlatformAdapter()
        hooks = adapter.get_hook_support()
        assert "stop_hooks" in hooks
        # ... more assertions

    def test_command_generation(self):
        """Test command file generation."""
        # ... test implementation

    # ... more tests for 100% coverage
```

### README.md

Add to the existing README.md:

```markdown
## Supported Platforms

- **Claude Code** - Anthropic's CLI for Claude
- **<Platform Name>** - [Brief description]

## Installation

### <Platform Name>

```bash
deepwork install --platform <platform_name>
```

[Any platform-specific notes]
```

## Quality Criteria

- Platform adapter class added to `src/deepwork/adapters.py`:
  - Inherits from `PlatformAdapter`
  - Implements all required methods
  - Registered in `PLATFORM_ADAPTERS`
- Templates created in `src/deepwork/templates/<platform_name>/`:
  - `command.md.j2` exists and renders correctly
  - Format matches platform's expected command format
- Tests created in `tests/`:
  - Cover all new adapter functionality
  - Cover template rendering
  - All tests pass
- Test coverage is 100% for new code:
  - Run `uv run pytest --cov=src/deepwork --cov-report=term-missing`
  - No uncovered lines in new code
- README.md updated:
  - Platform listed in supported platforms
  - Installation command documented
  - Any platform-specific notes included
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

This is the core implementation step. The adapter you create will be responsible for:
- Determining where command files are placed
- Generating command file content from job definitions
- Handling platform-specific features and hooks

The templates use Jinja2 and should produce files that match exactly what the platform expects. Reference the CLI configuration documentation frequently to ensure compatibility.

## Tips

- Study the existing `ClaudeAdapter` as a reference implementation
- Run tests frequently as you implement
- Use `--cov-report=html` for a detailed coverage report
- If a test is hard to write, the code might need refactoring
- Template syntax errors often show up at runtime - test early


#### Outputs

Create these files/directories:
- `templates/` (directory)- `tests/` (directory)- `README.md`

#### On Completion

1. Verify outputs are created
2. Inform user: "implement complete, outputs: templates/, tests/, README.md"
3. **Continue to next skill**: Proceed to `verify`

---

### Skill: verify

**Type**: Workflow step 4/4 in **integrate**

**Description**: Sets up platform directories and verifies deepwork install works correctly. Use after implementation to confirm integration.

#### Prerequisites

Before running this skill, ensure these are complete:
- `implement`


#### Input Files

Read these files (from previous steps):
- `templates/` (from `implement`)

#### Instructions

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
   - `deepwork_rules.define.md` exists
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

## Quality Criteria

- Platform-specific directories are set up in the DeepWork repo
- `deepwork install --platform <platform_name>` completes without errors
- All expected command files are created:
  - deepwork_jobs.define, implement, refine
  - deepwork_rules.define
  - Any other standard job commands
- Command file content is correct:
  - Matches platform's expected format
  - Job/step information is properly rendered
  - No template errors or missing content
- Existing platforms still work (if applicable)
- No conflicts between platforms
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

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


#### Outputs

Create these files/directories:
- `verification_checklist.md`

#### On Completion

1. Verify outputs are created
2. Inform user: "integrate workflow complete, outputs: verification_checklist.md"
3. Consider creating a PR to merge the work branch

---

## Guardrails

- **Never skip prerequisites**: Always verify required steps are complete before running a skill
- **Never produce partial outputs**: Complete all required outputs before marking a skill done
- **Always use the work branch**: Never commit directly to main/master
- **Follow quality criteria**: Use sub-agent review when quality criteria are specified
- **Ask for clarification**: If user intent is unclear, ask before proceeding

## Context Files

- Job definition: `.deepwork/jobs/add_platform/job.yml`
- research instructions: `.deepwork/jobs/add_platform/steps/research.md`
- add_capabilities instructions: `.deepwork/jobs/add_platform/steps/add_capabilities.md`
- implement instructions: `.deepwork/jobs/add_platform/steps/implement.md`
- verify instructions: `.deepwork/jobs/add_platform/steps/verify.md`
