---
name: deepwork_jobs.clone_remote_job
description: "Installs a DeepWork job from a GitHub repository and guides customization. Use when adding a pre-built job from the library."user-invocable: false---

# deepwork_jobs.clone_remote_job

**Standalone skill** - can be run anytime

> Creates and manages multi-step AI workflows. Use when defining, implementing, or improving DeepWork jobs.


## Instructions

**Goal**: Installs a DeepWork job from a GitHub repository and guides customization. Use when adding a pre-built job from the library.

# Clone Remote Job

## Objective

Help the user install a DeepWork job from a remote GitHub repository and customize it for their project.

## Task

Guide the user through cloning a remote job from the DeepWork job library (or any GitHub repository), then assist with any required customization.

### Step 1: Understand the User's Request

1. **Get the job URL**
   - Ask the user for the GitHub URL of the job they want to install
   - The URL should point to a job directory, e.g.:
     - `https://github.com/Unsupervisedcom/deepwork/tree/main/library/jobs/spec_driven_development`
   - If they don't have a URL, point them to the job library: `https://github.com/Unsupervisedcom/deepwork/tree/main/library/jobs`

2. **Confirm the destination**
   - Jobs are installed to `.deepwork/jobs/<job_name>/`
   - If a job with the same name exists, warn the user it will be overwritten

### Step 2: Run the Install Script

Execute the `install_remote_job.sh` script:

```bash
.deepwork/jobs/deepwork_jobs/install_remote_job.sh <github_url>
```

**Script requirements:**
- `curl` - for downloading files
- `jq` - for parsing JSON responses from GitHub API

If the script fails due to missing dependencies, help the user install them:
- On macOS: `brew install jq`
- On Ubuntu/Debian: `sudo apt-get install jq`
- On other systems: Guide them to https://stedolan.github.io/jq/download/

### Step 3: Review the Job's README

After installation, check for a readme file in the installed job directory:

1. **Read the readme**
   - Check for `readme.md` or `README.md` in `.deepwork/jobs/<job_name>/`
   - Look for sections about customization, configuration, or setup

2. **Identify required customizations**
   - Look for placeholders like `[docs_folder]`, `[project_name]`, etc.
   - Note any environment variables or configuration needed
   - Check for technology stack requirements

### Step 4: Apply Customizations

Work through any required customizations with the user:

1. **Replace placeholders**
   - Use find/replace to update placeholders throughout the job files
   - Example: Replace `[docs_folder]` with the actual documentation directory
   ```bash
   # Find all occurrences
   grep -r "\[docs_folder\]" .deepwork/jobs/<job_name>/

   # Replace throughout the job (preview first)
   find .deepwork/jobs/<job_name>/ -type f -name "*.md" -o -name "*.yml" | xargs sed -i 's/\[docs_folder\]/docs/g'
   ```

2. **Adjust for project conventions**
   - Review step instructions for any project-specific adjustments
   - Update paths, naming conventions, or workflow steps as needed

3. **Configure any required integrations**
   - Set up environment variables if needed
   - Configure any external services or tools

### Step 5: Update the README

After applying customizations:

1. **Remove customization instructions**
   - Delete or update the "REQUIRED CUSTOMIZATION" section in the readme
   - The readme should now describe the job as configured for this project

2. **Add project-specific notes**
   - Document any customizations made
   - Add notes about how this job fits into the project workflow

### Step 6: Sync and Review

1. **Run deepwork sync**
   ```bash
   deepwork sync
   ```

2. **Review the new skills** in `.claude/skills/` to make sure they make sense

## Output Format

After completing the installation and customization:

```
## Installation Summary

**Job:** <job_name>
**Source:** <github_url>
**Installed to:** .deepwork/jobs/<job_name>/

### Customizations Applied
- [List of customizations made]

### Next Steps
- [Instructions on how to kick off the main job workflow, e.g., "Run /<job_name> to start"]
- [Any remaining setup or first-use guidance]
```

## Quality Criteria

- Job files downloaded successfully to `.deepwork/jobs/<job_name>/`
- README reviewed for customization requirements
- All required placeholders replaced with project-specific values
- README updated to remove/update customization instructions
- `deepwork sync` run successfully
- User informed how to kick off the job workflow
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>`

## Example Dialog

```
User: /deepwork_jobs.clone_remote_job

Claude: I'll help you install a remote DeepWork job.

What is the GitHub URL of the job you'd like to install?

If you're looking for jobs to install, you can browse the job library at:
https://github.com/Unsupervisedcom/deepwork/tree/main/library/jobs

User: https://github.com/Unsupervisedcom/deepwork/tree/main/library/jobs/spec_driven_development

Claude: I'll install the spec_driven_development job for you.

*Runs install_remote_job.sh script*

The job has been installed to `.deepwork/jobs/spec_driven_development/`.

Let me review the readme for any required customization...

I found that this job requires customization - there's a placeholder `[docs_folder]` that needs to be replaced with your project's documentation directory.

Where do you keep your documentation? (e.g., `docs/`, `documentation/`, or at the root)

User: We use docs/

Claude: I'll replace `[docs_folder]` with `docs` throughout the job files.

*Makes replacements*

I've updated 4 files with the correct documentation path. Let me also update the readme to remove the customization instructions since this is now configured for your project.

*Updates readme*

Now let me sync the job to generate slash commands.

*Runs deepwork sync*

## Installation Summary

**Job:** spec_driven_development
**Source:** https://github.com/Unsupervisedcom/deepwork/tree/main/library/jobs/spec_driven_development
**Installed to:** .deepwork/jobs/spec_driven_development/

### Customizations Applied
- Replaced `[docs_folder]` with `docs` in job.yml, constitution.md, plan.md
- Updated readme to remove customization instructions

### Next Steps
- Run `/spec_driven_development` to start the workflow
- Type 'exit' then run 'claude --resume' to load the new skills

<promise>✓ Quality Criteria Met</promise>
```


### Job Context

Core commands for managing DeepWork jobs. These commands help you define new multi-step
workflows and learn from running them.

The `new_job` workflow guides you through defining and implementing a new job by
asking structured questions about your workflow, understanding each step's inputs and outputs,
reviewing the specification, and generating all necessary files.

The `clone_remote_job` skill installs a job from a GitHub repository (like the DeepWork
job library) and guides you through any required customization for your project.

The `learn` skill reflects on conversations where DeepWork jobs were run, identifies
confusion or inefficiencies, and improves job instructions. It also captures bespoke
learnings specific to the current run into AGENTS.md files in the working folder.


## Required Inputs

**User Parameters** - Gather from user before starting:
- **github_url**: GitHub URL to the job directory (e.g., https://github.com/Unsupervisedcom/deepwork/tree/main/library/jobs/spec_driven_development)


## Work Branch

Use branch format: `deepwork/deepwork_jobs-[instance]-YYYYMMDD`

- If on a matching work branch: continue using it
- If on main/master: create new branch with `git checkout -b deepwork/deepwork_jobs-[instance]-$(date +%Y%m%d)`

## Outputs

**Required outputs**:
- `.deepwork/jobs/` (directory)

## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs

## Quality Validation

**Before completing this step, you MUST have your work reviewed against the quality criteria below.**

Use a sub-agent (Haiku model) to review your work against these criteria:

**Criteria (all must be satisfied)**:
1. **Script Executed**: Was install_remote_job.sh run successfully?
2. **Files Downloaded**: Were all job files downloaded to .deepwork/jobs/[job_name]/?
3. **README Reviewed**: Was the job's readme checked for customization requirements?
4. **Placeholders Replaced**: Were all required placeholders replaced with project-specific values?
5. **README Updated**: Was the readme updated to remove/update customization instructions?
6. **Sync Complete**: Has `deepwork sync` been run successfully?
7. **Workflow Instructions**: Was the user informed how to kick off the job workflow?
**Review Process**:
1. Once you believe your work is complete, spawn a sub-agent using Haiku to review your work against the quality criteria above
2. The sub-agent should examine your outputs and verify each criterion is met
3. If the sub-agent identifies valid issues, fix them
4. Have the sub-agent review again until all valid feedback has been addressed
5. Only mark the step complete when the sub-agent confirms all criteria are satisfied

## On Completion

1. Verify outputs are created
2. Inform user: "clone_remote_job complete, outputs: .deepwork/jobs/"

This standalone skill can be re-run anytime.

---

**Reference files**: `.deepwork/jobs/deepwork_jobs/job.yml`, `.deepwork/jobs/deepwork_jobs/steps/clone_remote_job.md`