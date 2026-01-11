---
description: Refine and update existing job definitions
---

# Refine Existing DeepWork Job

This command helps you modify existing DeepWork jobs. You can:
- Add new steps to a workflow
- Modify step instructions
- Update inputs/outputs
- Adjust dependencies
- Change job metadata (description, version)

## Instructions

You will help the user refine an existing job definition. Follow this process:

### Step 1: Select Job to Refine

1. **List available jobs**:
   Read `.deepwork/registry.yml` to show installed jobs:
   ```
   Available jobs:
   1. competitive_research v1.0.0 - Systematic competitive analysis workflow
   2. ad_campaign v1.0.0 - Marketing campaign planning
   ```

2. **Ask user which job to refine**

3. **Load job definition**:
   Read `.deepwork/jobs/[job_name]/job.yml`

4. **Show current structure**:
   ```
   Job: [name] v[version]
   Description: [description]

   Steps:
   1. [step1] - [description]
   2. [step2] - [description]
   ...
   ```

### Step 2: Determine Changes

Ask the user what they'd like to change:

**Options**:
1. **Add a new step** - Insert or append a step to the workflow
2. **Modify step instructions** - Update the .md file for a step
3. **Change step inputs/outputs** - Modify what a step consumes or produces
4. **Update dependencies** - Adjust the dependency graph
5. **Update job metadata** - Change description or version
6. **Remove a step** - Delete a step (with validation)

### Step 3: Make Changes

Based on the user's selection:

#### Adding a Step

1. Ask for step details (same as define wizard)
2. Ask where to insert: "Before which step?" or "At the end?"
3. Validate dependencies (can't depend on later steps if inserted early)
4. Update job.yml
5. Create new step instructions file

#### Modifying Step Instructions

1. Ask which step to modify
2. Read current `.deepwork/jobs/[job_name]/steps/[step_id].md`
3. Ask user how to modify (or read their changes)
4. Update the markdown file

#### Changing Inputs/Outputs

1. Ask which step to modify
2. Show current inputs and outputs
3. Ask what changes to make
4. Validate:
   - File inputs must reference existing dependencies
   - If removing an output, check if other steps depend on it
5. Update job.yml

#### Updating Dependencies

1. Ask which step to modify
2. Show current dependencies
3. Ask what changes to make
4. Validate:
   - No circular dependencies
   - All file inputs match dependencies
5. Update job.yml

#### Updating Metadata

1. Ask what to change (description and/or version)
2. If version changes, follow semantic versioning:
   - Major: Breaking changes
   - Minor: New features, backwards compatible
   - Patch: Bug fixes
3. Update job.yml
4. Update registry entry

#### Removing a Step

1. Ask which step to remove
2. **Validate safety**:
   - Check if other steps depend on this step
   - Check if other steps use outputs from this step
   - If dependencies exist, warn user and suggest updating dependents first
3. If safe, remove:
   - Remove from job.yml
   - Delete step instructions file

### Step 4: Sync and Reload Commands

**IMPORTANT**: After making any changes, you MUST run sync to regenerate the slash-commands:

```bash
deepwork sync
```

This will:
- Parse the updated job definition
- Regenerate all slash-commands for this job
- Update commands in `.claude/commands/`

**After sync completes successfully**, reload the commands in the current Claude session:
- Type `/reload` to reload commands (if available), OR
- Restart the Claude session to pick up the new commands

### Step 5: Confirm Changes

Show summary of changes:
```
✓ Job "[job_name]" has been updated!

Changes made:
- Added new step: [step_id]
- Modified step: [step_id]
- Updated version: [old] → [new]

Files updated:
- .deepwork/jobs/[job_name]/job.yml
- .deepwork/jobs/[job_name]/steps/[step_id].md

Commands regenerated via sync. Reload your Claude session to use the updated commands.

To test the changes, run:
/[job_name].[first_step_id]
```

## Validation Rules

Enforce all the same rules as the define wizard, plus:

1. **Version updates**: Follow semantic versioning conventions
2. **Dependency safety**: When removing/modifying steps, check impact on dependent steps
3. **Output safety**: Warn if removing outputs that other steps consume
4. **Step ordering**: If inserting steps, validate dependency order

## Safe Modification Patterns

Guide users toward safe changes:

### Safe Changes (Always OK)
- Adding steps at the end with new outputs
- Updating step instructions (content)
- Changing job description
- Adding user inputs to a step
- Adding outputs (not removing)

### Potentially Breaking Changes (Warn User)
- Removing steps
- Removing outputs
- Changing dependencies
- Renaming outputs (other steps may reference them)
- Major version bumps

### Always Validate
- Circular dependencies after any dependency change
- File inputs match dependencies after any change
- Step IDs remain unique

## Error Handling

If issues arise:
- **Dependency conflict**: "Step X depends on step Y which you're trying to remove. Update X first."
- **Circular dependency**: "Adding this dependency would create a cycle: A → B → C → A"
- **Missing file input**: "Step X requires file.md from step Y, but Y is not in its dependencies"

## Example Usage

```
User: /deepwork.refine_job

Claude: I'll help you refine an existing job. Here are your installed jobs:

1. competitive_research v1.0.0 - Systematic competitive analysis workflow
2. product_launch v1.0.0 - End-to-end product launch planning

Which job would you like to refine?

User: 1

Claude: Loading competitive_research...

Current structure:
- Step 1: identify_competitors
- Step 2: primary_research
- Step 3: secondary_research
- Step 4: comparative_report

What would you like to do?
1. Add a new step
2. Modify step instructions
3. Change inputs/outputs
4. Update dependencies
5. Update job metadata
6. Remove a step

User: 1

Claude: Great! Let's add a new step. Where would you like to insert it?
[continues interactive dialog]
```

---

## Context Files

- Job schema: `src/deepwork/schemas/job_schema.py`
- Job parser: `src/deepwork/core/parser.py`
- Registry: `.deepwork/registry.yml`
- Template: `src/deepwork/templates/claude/command-job-step.md.jinja`