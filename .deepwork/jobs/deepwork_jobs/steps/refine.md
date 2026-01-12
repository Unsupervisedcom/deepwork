# Refine Existing DeepWork Job

## Objective

Help the user modify an existing DeepWork job definition by understanding what they want to change and ensuring the modifications maintain consistency and validity.

## Task

Guide the user through refining a job by first understanding their existing job, then what they want to change, and finally implementing those changes safely.

### Step 1: Select and Load Job

1. **List available jobs**
   - Scan `.deepwork/jobs/` directory for installed jobs
   - Display installed jobs with versions and descriptions
   - Ask which job to refine

2. **Load job definition**
   - Read `.deepwork/jobs/[job_name]/job.yml`
   - Parse and understand the current structure

3. **Show current structure**
   - Display all steps with their names and descriptions
   - Show the dependency flow
   - Highlight key inputs and outputs

### Step 2: Understand Desired Changes

Ask the user what they want to change:

**Change Options:**
1. Add a new step to the workflow
2. Modify step instructions
3. Change step inputs/outputs
4. Update dependencies between steps
5. Update job metadata (description, version)
6. Remove a step
7. Add or modify stop hooks (quality validation)

**For each change, ask clarifying questions:**
- Why do they want to make this change?
- How will it improve the workflow?
- Are there dependencies or side effects to consider?

### Step 3: Make Changes Safely

Based on the user's selection:

#### Adding a Step

1. **Gather step details** (same as define command)
   - What does this step accomplish?
   - What are the inputs? User parameters or file inputs?
   - What outputs does it produce?
   - What are the dependencies?

2. **Determine placement**
   - Where should it go in the workflow?
   - Before which existing step?
   - Or at the end?

3. **Validate placement**
   - Can't depend on later steps if inserted early
   - File inputs must come from dependencies
   - Check for circular dependencies

4. **Update files**
   - Update `job.yml` with new step
   - Create step instructions file in `steps/[step_id].md`
   - Prepare changelog entry describing the addition

#### Modifying Step Instructions

1. **Select step to modify**
   - Show list of steps
   - Ask which one to modify

2. **Understand the change**
   - What's not working with current instructions?
   - What should be different?
   - Show current instructions

3. **Update instructions**
   - Modify `.deepwork/jobs/[job_name]/steps/[step_id].md`
   - Keep the same structure (Objective, Task, Process, Output Format, Quality Criteria)
   - Prepare changelog entry describing the modification

#### Changing Inputs/Outputs

1. **Select step to modify**
2. **Show current inputs and outputs**
3. **Understand the change**
   - Adding or removing?
   - Why is this needed?

4. **Validate impact**
   - If removing output: check if other steps depend on it (BREAKING CHANGE)
   - If adding file input: ensure from_step is in dependencies
   - If removing input: ensure it's not critical

5. **Update job.yml**
   - Prepare changelog entry describing the input/output changes

#### Updating Dependencies

1. **Select step to modify**
2. **Show current dependency graph**
3. **Understand the change**
   - Adding or removing dependency?
   - Why?

4. **Validate**
   - Check for circular dependencies
   - Ensure all file inputs have matching dependencies
   - Ensure dependency chain makes logical sense

5. **Update job.yml**
   - Prepare changelog entry describing the dependency changes

#### Updating Metadata

1. **Ask what to change**
   - Description?
   - Version?

2. **If version change, explain semantic versioning**
   - Major (x.0.0): Breaking changes (removing steps, removing outputs)
   - Minor (0.x.0): New features, backwards compatible (adding steps)
   - Patch (0.0.x): Bug fixes, improvements

3. **Update job.yml**
   - Prepare changelog entry describing the metadata changes

#### Removing a Step

1. **Select step to remove**

2. **CRITICAL: Validate safety**
   - Check if other steps depend on this step
   - Check if other steps use outputs from this step
   - If dependencies exist: **WARN** and suggest updating dependents first
   - This is a BREAKING CHANGE - requires major version bump

3. **If safe to remove**
   - Remove from `job.yml`
   - Delete step instructions file
   - Suggest version bump
   - Prepare changelog entry describing the removal

#### Adding or Modifying Stop Hooks

Stop hooks provide quality validation loops that ensure step outputs meet criteria before completing.

1. **Select step to modify**
   - Show list of steps
   - Ask which one to add/modify hooks for

2. **Understand the need**
   - What quality criteria should be validated?
   - Is the output subjective (use prompt hook) or objective (use script hook)?
   - Should validation happen automatically or only on specific conditions?

3. **Choose hook type**

   **Prompt hooks** (recommended for most cases):
   - Best for subjective quality criteria
   - AI evaluates the output against criteria
   - Example: "Verify the report is comprehensive and well-organized"
   ```yaml
   stop_hooks:
     - prompt: |
         Verify the output meets criteria:
         1. Contains all required sections
         2. Analysis is thorough
         3. Recommendations are actionable
   ```

   **Prompt file hooks**:
   - For reusable or complex validation criteria
   - Stores criteria in a separate markdown file
   ```yaml
   stop_hooks:
     - prompt_file: hooks/quality_check.md
   ```

   **Script hooks**:
   - For objective, programmatic validation
   - Best for tests, linting, format checking
   ```yaml
   stop_hooks:
     - script: hooks/run_tests.sh
   ```

4. **Multiple hooks can be combined**
   ```yaml
   stop_hooks:
     - script: hooks/lint.sh           # First: objective checks
     - prompt: "Verify content quality" # Then: subjective review
   ```

5. **Update files**
   - Add/modify `stop_hooks` array in job.yml
   - Create hook files if using prompt_file or script types
   - Update step instructions to match quality criteria
   - Prepare changelog entry

6. **Encourage prompt-based hooks**
   - They leverage the AI's ability to understand context
   - More flexible than rigid script checks
   - Can evaluate nuanced quality criteria

### Step 4: Update Changelog

After making changes to the job.yml:

1. **Add a changelog entry**
   - Add a new entry to the `changelog` array in the job.yml
   - Use the new version number
   - List all changes made in this refinement

2. **Changelog entry format**:
   ```yaml
   - version: "[new_version]"
     changes: "[Description of all changes in this version]"
   ```

3. **Example changelog entries**:
   - "Added step: validate_positioning"
   - "Modified step instructions for research_competitors to improve clarity and add quality criteria"
   - "Removed step: duplicate_analysis (consolidated into comparative_analysis)"
   - "Updated dependencies: positioning_recommendations now depends on validate_positioning"
   - "Changed output filename: comparison_matrix.md → comparison_table.md"
   - "Added step: validate_positioning; Updated dependencies for positioning_recommendations"

### Step 5: Validate Changes

After updating the changelog:

1. **Review the updated structure**
   - Show the complete updated workflow
   - Highlight what changed
   - Check for consistency

2. **Validate job definition**
   - No circular dependencies
   - All file inputs match dependencies
   - All step IDs unique
   - All outputs defined

3. **Confirm version update**
   - Ensure version was bumped appropriately
   - Breaking changes? Major version
   - New features? Minor version
   - Improvements? Patch version

### Step 6: Sync and Reload

1. **Run sync**
   ```bash
   deepwork sync
   ```

2. **Reload commands**
   - Instruct user to run `/reload` or restart session

3. **Provide summary**
   - Show what changed
   - List updated files
   - Display the changelog entry
   - Explain next steps

## Safe Modification Patterns

Guide users toward safe changes:

### Safe Changes (Always OK)
- Adding steps at the end with new outputs
- Updating step instructions (content only)
- Changing job description
- Adding user inputs to a step
- Adding outputs (not removing)
- Patch version bumps

### Potentially Breaking Changes (Warn User)
- Removing steps
- Removing outputs
- Removing inputs
- Changing dependencies
- Renaming outputs (other steps may reference them)
- Requires major or minor version bump

### Always Validate
- Circular dependencies after any dependency change
- File inputs match dependencies after any change
- Step IDs remain unique
- At least one output per step

## Example Dialog

```
Claude: I'll help you refine an existing job. Here are your installed jobs:

1. competitive_research v1.0.0 - Systematic competitive analysis workflow
2. blog_post v1.0.0 - Blog post creation workflow

Which job would you like to refine?

User: 1

Claude: Loading competitive_research v1.0.0...

Current structure:
- Step 1: identify_competitors - Identify 5-7 competitors in target market
- Step 2: research_competitors - Deep research on each competitor
- Step 3: comparative_analysis - Side-by-side comparison matrix
- Step 4: positioning_recommendations - Strategic positioning report

What would you like to change?
1. Add a new step
2. Modify step instructions
3. Change inputs/outputs
4. Update dependencies
5. Update job metadata
6. Remove a step

User: 1

Claude: Great! Let's add a new step. First, help me understand:

1. What should this new step accomplish?
2. Where should it fit in the workflow?
   - Should it go between existing steps or at the end?

User: I want to add a step that validates our product positioning before the final recommendations. It should go between step 3 and step 4.

Claude: Excellent idea. So this would be:
- Step 4: validate_positioning
- Step 5: positioning_recommendations (renumbered)

For this validation step:
1. What inputs does it need? I assume it needs the comparison_matrix.md from step 3?
2. What should it output?
3. What exactly should this validation check for?

User: Yes, it needs the comparison matrix. It should output a validation_report.md that identifies gaps in our positioning.

Claude: Perfect. Let me confirm the details:

**New Step: validate_positioning**
- Name: "Validate Product Positioning"
- Description: "Identify gaps and opportunities in current positioning"
- Inputs: comparison_matrix.md (from comparative_analysis step)
- Outputs: validation_report.md
- Dependencies: comparative_analysis
- Position: Between step 3 and 4

Should the positioning_recommendations step also use the validation_report.md as input?

User: Yes, definitely

Claude: Great! So I'll also update the positioning_recommendations step to include validation_report.md as an input and add validate_positioning as a dependency.

This is a new feature, so I'll bump the version to 1.1.0 (minor version).

Creating the new step... ✓

Updated files:
- .deepwork/jobs/competitive_research/job.yml (added step, updated dependencies, version → 1.1.0, updated changelog)
- .deepwork/jobs/competitive_research/steps/validate_positioning.md (created)

Changelog entry added:
```yaml
- version: "1.1.0"
  changes: "Added step: validate_positioning between comparative_analysis and positioning_recommendations; Updated dependencies for positioning_recommendations"
```

Now run:
```bash
deepwork sync
```

Then reload your session and you'll have:
- /competitive_research.validate_positioning (new!)
- All other commands updated
```

## Validation Rules

Enforce the same rules as job definition:
- Job name: lowercase, underscores
- Version: semantic versioning
- Step IDs: unique within job
- Dependencies: must reference existing step IDs
- File inputs: `from_step` must be in dependencies
- At least one output per step
- No circular dependencies

## Error Handling

If issues arise, provide clear guidance:
- **Dependency conflict**: "Step X depends on step Y which you're trying to remove. You must update step X first, or remove both steps."
- **Circular dependency**: "Adding this dependency would create a cycle: A → B → C → A. Please choose a different dependency structure."
- **Missing file input**: "Step X requires file.md from step Y, but Y is not in its dependencies. I'll add Y to the dependencies."
- **Breaking change**: "Removing this output is a breaking change. Other steps depend on it. I recommend against this change unless you update the dependent steps first."

## Changelog Entry Format

Instead of creating a separate refinement_summary.md file, add the changes directly to the job.yml changelog section. This creates a permanent version history within the job definition itself.

**Location**: `.deepwork/jobs/[job_name]/job.yml`

**Add to the `changelog` array**:

```yaml
changelog:
  - version: "1.0.0"
    changes: "Initial job creation"
  - version: "[new_version]"
    changes: "[Concise description of all changes in this version]"
```

**Guidelines for changelog entries**:
- Be concise but descriptive
- Use action verbs (Added, Modified, Removed, Updated, Changed, Fixed)
- Reference specific step names when relevant
- For breaking changes, prefix with "BREAKING:"
- If multiple changes, separate with semicolons or use clear phrasing

**Examples**:
- "Added step: validate_positioning between comparative_analysis and positioning_recommendations"
- "Modified step instructions for research_competitors to improve clarity and add quality criteria"
- "Removed step: duplicate_analysis (consolidated into comparative_analysis)"
- "Updated dependencies: positioning_recommendations now depends on validate_positioning"
- "Changed output filename: comparison_matrix.md → comparison_table.md"
- "BREAKING: Removed output file shared_data.json from identify_competitors step"
- "Fixed circular dependency between steps A and B"
- "Updated job description to reflect new validation phase"
- "Added validate_positioning step; Updated dependencies for positioning_recommendations"

## Quality Criteria

- Changes maintain job consistency
- Dependencies are logically valid
- Version bump follows semantic versioning
- No circular dependencies introduced
- User understands impact of changes
- Breaking changes are clearly communicated
