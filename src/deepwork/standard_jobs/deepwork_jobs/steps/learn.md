# Learn from Job Execution

## Objective

Think deeply about this task. Reflect on the current conversation to identify learnings from DeepWork job executions, improve job instructions with generalizable insights, and capture bespoke (run-specific) learnings in AGENTS.md files in the deepest common folder that would contain all work on the topic in the future.

## Task

Analyze the conversation history to extract learnings and improvements, then apply them appropriately:
- **Generalizable learnings** → Update job instruction files
- **Bespoke learnings** (specific to this run) → Add to AGENTS.md in the deepest common folder for the topic

### Step 1: Analyze Conversation for Job Executions

1. **Scan the conversation** for DeepWork slash commands that were run
   - Look for patterns like `/job_name.step_id`
   - Identify which jobs and steps were executed
   - Note the order of execution

2. **Locate the job directory using `job_dir`**
   - The MCP server returns `job_dir` (absolute path) when starting workflows — use this as the authoritative location
   - The job may live in `.deepwork/jobs/`, `src/deepwork/standard_jobs/`, or an **external folder** via `DEEPWORK_ADDITIONAL_JOBS_FOLDERS`
   - Check if `job_dir` is inside the current project's git repo or in a **separate git repository** (e.g. a library checkout at `~/.keystone/*/deepwork/library/jobs/`)
   - If `job_dir` is in a different git repo, note this — you'll need to handle commits/pushes separately in Step 8

3. **Identify the AGENTS.md target folder**
   - This should be the deepest common folder that would contain all work on the topic in the future
   - Should be clear from conversation history where work was done
   - If unclear, run `git diff` to see where changes were made on the branch

4. **If no job was specified**, ask the user:
   - "Which DeepWork job would you like me to learn from?"
   - List available jobs (call `get_workflows` to see all discovered jobs)

### Step 2: Identify Points of Confusion and Inefficiency

Review the conversation for:

1. **Confusion signals**
   - Questions the agent asked that shouldn't have been necessary
   - Misunderstandings about what a step required
   - Incorrect outputs that needed correction
   - Ambiguous instructions that led to wrong interpretations

2. **Inefficiency signals**
   - Extra steps or iterations that were needed
   - Information that had to be repeated
   - Context that was missing from instructions
   - Dependencies that weren't clear

3. **Error patterns**
   - Failed validations and why they failed
   - Quality criteria that were misunderstood
   - Edge cases that weren't handled

4. **Success patterns**
   - What worked particularly well
   - Efficient approaches worth preserving
   - Good examples that could be added to instructions

### Step 3: Classify Learnings

For each learning identified, determine if it is:

**Generalizable** (should improve instructions):
- Would help ANY future run of this job
- Addresses unclear or missing guidance
- Fixes incorrect assumptions in instructions
- Adds helpful examples or context
- Examples:
  - "Step instructions should mention that X format is required"
  - "Quality criteria should include checking for Y"
  - "Add example of correct output format"

**Bespoke** (should go in AGENTS.md):
- Specific to THIS project/codebase/run
- Depends on local conventions or structure
- References specific files or paths
- Would not apply to other uses of this job
- Examples:
  - "In this codebase, API endpoints are in `src/api/`"
  - "This project uses camelCase for function names"
  - "The main config file is at `config/settings.yml`"

### Step 4: Update Job Instructions (Generalizable Learnings)

For each generalizable learning:

1. **Locate the instruction file using `job_dir`**
   - Path: `<job_dir>/steps/[step_id].md` (where `job_dir` was identified in Step 1)
   - Do NOT assume `.deepwork/jobs/` — the job may live in an external folder

2. **Make targeted improvements**
   - Add missing context or clarification
   - Include helpful examples
   - Clarify ambiguous instructions
   - Update quality criteria if needed
   - If you identify problems in the outcomes of steps, those usually should be reflected in an update to the `reviews` for that step in `job.yml` (adjusting criteria names, statements, or `run_each` targeting)

3. **Keep instructions concise**
   - Avoid redundancy - don't repeat the same guidance in multiple places
   - Be direct - remove verbose explanations that don't add value
   - Prefer bullet points over paragraphs where appropriate

4. **Preserve instruction structure**
   - Keep existing sections (Objective, Task, Process, Output Format, Quality Criteria)
   - Add to appropriate sections rather than restructuring
   - Maintain consistency with other steps

### Step 4b: Extract Shared Content into Referenced Files

Review all instruction files for the job and identify content that:
- Appears in multiple step instructions (duplicated)
- Is lengthy and could be extracted for clarity
- Would benefit from being maintained in one place

**Extract to shared files:**

1. **Create shared files** in `<job_dir>/steps/shared/`
   - `conventions.md` - Coding/formatting conventions used across steps
   - `examples.md` - Common examples referenced by multiple steps
   - `schemas.md` - Data structures or formats used throughout

2. **Reference from instructions** using markdown includes or explicit references:
   ```markdown
   ## Conventions

   Follow the conventions defined in `shared/conventions.md`.
   ```

3. **Benefits of extraction:**
   - Single source of truth - update once, applies everywhere
   - Shorter instruction files - easier to read and maintain
   - Consistent guidance across steps

### Step 5: Create/Update AGENTS.md (Bespoke Learnings)

The AGENTS.md file captures project-specific knowledge that helps future agent runs.

1. **Determine the correct location**
   - Place AGENTS.md in the deepest common folder that would contain all work on the topic in the future
   - This ensures the knowledge is available when working in that context
   - If uncertain, place at the project root

2. **Use file references where possible**
   - Instead of duplicating information, reference source files
   - This keeps AGENTS.md in sync as the codebase evolves
   - Pattern: "See `path/to/file.ext` for [description]"

3. **AGENTS.md structure**: See `<job_dir>/templates/agents.md.template` for the standard format.

4. **Writing entries**
   - Be concise but specific
   - Always prefer file references over inline content
   - Use line numbers when referencing specific code: `file.ext:42`
   - Group related learnings together

### Step 6: Create or Fix Scripts

Review the conversation for opportunities to add or improve scripts in the job's `scripts/` directory:

1. **Fix existing scripts** - If any scripts were used during execution and had problems (wrong output, errors, edge cases), fix them now.

2. **Create new scripts** - If any process during execution was manual, repetitive, or error-prone, and would be faster or more reliable as a script, create one. Good candidates:
   - Data fetching or transformation that had to be done by hand
   - File generation with specific formatting requirements
   - Validation or checking steps that could be automated
   - Setup or teardown tasks that will repeat on every run

3. **Test the scripts** - Run any new or modified scripts to verify they work correctly.

4. **Reference from instructions** - Update the relevant step instruction files to reference the new scripts so future runs use them.

### Step 7: Update Job Version

If instruction files were modified:

1. **Bump version in job.yml**
   - Patch version (0.0.x) for instruction improvements
   - Minor version (0.x.0) if quality criteria changed

### Step 8: Commit and Push Changes to External Job Repos

If `job_dir` is in a **separate git repository** (outside the current project), you need to commit and push those changes independently.

1. **Detect the external repo**
   - Run `git -C <job_dir> rev-parse --show-toplevel` to find the repo root
   - If it differs from the current project root, the job lives in an external repo

2. **Commit changes in the external repo**
   - `cd` to the external repo root
   - Stage only the changed job files using a repo-relative path (e.g. `git -C <repo_root> add <relative_job_dir>/`)
   - Create a commit following Conventional Commits: `fix(jobs): improve <job_name> instructions from learn workflow`

3. **Push strategy — ask the user**
   - Ask: "The job `<job_name>` lives in an external repo at `<repo_root>`. How would you like to push these changes?"
     - **Direct push to main**: Commit on main and push (for collaborators who prefer clean history)
     - **PR from branch**: Create a feature branch, push, and open a PR (for non-collaborators or when review is desired)
     - **PR from fork**: Fork the repo, push to fork, and open a PR (for non-collaborators without write access)
   - If the user has previously expressed a preference, follow it without asking again

4. **Execute the chosen strategy**
   - For direct push: `git push origin main`
   - For PR: Create branch `deepwork/learn-<job_name>`, push with `-u`, open PR via `gh pr create`
   - For fork PR: Use `gh repo fork`, push to fork, open PR against upstream

## File Reference Patterns

When adding entries to AGENTS.md, prefer these patterns:

**Good (references)**:
```markdown
- API endpoints follow REST conventions. See `src/api/routes.ts` for examples.
- Error handling pattern: See `src/utils/errors.ts:15-30`
- Configuration schema: Defined in `config/schema.json`
```

**Avoid (duplicating)**:
```markdown
- API endpoints should return JSON with this format: { status: ..., data: ... }
- Error handling should use try/catch with custom error classes
- Configuration requires these fields: name, version, ...
```

## Example Dialog

```
User: [Invokes the learn workflow via MCP]

Claude: I'll analyze this conversation for learnings from DeepWork job executions.

**Conversation Analysis**

I found the following job executions:
1. `/competitive_research.identify_competitors` - Completed
2. `/competitive_research.research_competitors` - Completed with 2 iterations
3. `/competitive_research.comparative_analysis` - Completed

**Identified Issues**

1. **Confusion in step 2**: The instructions didn't specify that competitor research should include pricing information. This caused an extra iteration.

2. **Missing context**: The agent had to ask about the industry focus, which should have been carried forward from step 1.

**Classification**

- Generalizable: Add pricing to research requirements in instructions
- Bespoke: This project focuses on B2B SaaS in the HR tech space

**Actions Taken**

1. Updated `.deepwork/jobs/competitive_research/steps/research_competitors.md`:
   - Added "Include pricing information (tiers, models, approximate ranges)" to research requirements
   - Added note about carrying forward industry context from previous step

2. Created `./competitive_research_output/AGENTS.md`:
   ```markdown
   # Project Context for Competitive Research

   ## Job-Specific Context

   ### competitive_research

   #### Industry Focus
   - Domain: B2B SaaS, HR Technology sector
   - See `identify_competitors_output.md` for market definition

   #### Competitors Identified
   - Reference: `competitor_list.md` for full details

   ## Last Updated
   - Date: 2024-01-15
   - From conversation about: Initial competitive analysis run
   ```

3. Updated job.yml version to 1.0.1

**Summary**

Updated job instructions and created AGENTS.md with bespoke learnings.
```

## Handling Edge Cases

**No job executions found**:
- Ask user which job they'd like to analyze
- Or offer to review available jobs

**Multiple jobs executed**:
- Analyze each job separately
- Create separate AGENTS.md entries or files as appropriate

**AGENTS.md already exists**:
- Read existing content
- Append new learnings to appropriate sections
- Update "Last Updated" section

**No issues found**:
- Document what worked well
- Consider if any successful patterns should be added to instructions as examples

**Sensitive information**:
- Never include secrets, credentials, or PII in AGENTS.md
- Reference config files instead of including values
