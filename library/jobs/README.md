# Job Library

This directory contains a public library of example jobs that you can use as starting points for your own workflows. Each job demonstrates best practices for structuring multi-step tasks with DeepWork.

## Purpose

The job library provides:

- **Inspiration**: See how others have structured complex workflows
- **Templates**: Copy and adapt jobs for your own use cases
- **Learning**: Understand the job definition format through real examples

## Structure

Each job in this library follows the same structure as the `.deepwork/jobs` subfolders in your local project:

```
library/jobs/
├── .deepreview              # Review rules for library job quality
├── README.md
├── platform_engineer/       # Platform engineering workflows
│   ├── job.yml
│   ├── AGENTS.md            # Agent context and learnings
│   ├── conventions.md       # RFC 2119 platform engineering standards
│   ├── readme.md
│   ├── steps/               # Step instruction files
│   └── templates/           # Output templates
├── repo/
│   ├── job.yml              # Job definition (name, steps, workflows)
│   ├── readme.md            # Job-specific documentation
│   └── steps/
│       ├── detect_platform.md
│       ├── ensure_labels.md
│       ├── check_branch_protection.md
│       ├── check_milestones.md
│       ├── check_boards.md
│       ├── setup_report.md
│       ├── audit_labels.md
│       ├── audit_branch_protection.md
│       ├── audit_milestones.md
│       ├── audit_boards.md
│       └── doctor_report.md
├── research/
│   ├── job.yml              # Job definition (name, steps, workflows)
│   ├── readme.md            # Job-specific documentation
│   ├── AGENTS.md            # Agent context and learnings
│   └── steps/
│       ├── scope.md
│       ├── choose_platforms.md
│       ├── gather.md
│       ├── gather_quick.md
│       ├── synthesize.md
│       ├── summarize.md
│       ├── report.md
│       ├── parse.md
│       ├── file.md
│       ├── ingest_material.md
│       ├── analyze.md
│       └── plan.md
└── spec_driven_development/
    ├── job.yml              # Job definition (name, steps, workflows)
    ├── readme.md            # Job-specific documentation
    └── steps/
        ├── constitution.md
        ├── specify.md
        ├── clarify.md
        ├── plan.md
        ├── tasks.md
        └── implement.md
```

### job.yml

The job definition file contains:

- `name`: Unique identifier for the job
- `version`: Semantic version (e.g., "1.0.0")
- `summary`: Brief description (under 200 characters)
- `common_job_info_provided_to_all_steps_at_runtime`: Detailed context provided to all steps at runtime
- `workflows`: Named sequences of steps (optional)
  - `name`: Workflow identifier
  - `summary`: What the workflow accomplishes
  - `steps`: Ordered list of step IDs to execute
- `steps`: Array of step definitions with:
  - `id`: Step identifier
  - `name`: Human-readable step name
  - `description`: What this step accomplishes
  - `hidden`: Whether the step is hidden from direct invocation (optional, default false)
  - `instructions_file`: Path to the step's markdown instructions
  - `inputs`: What the step requires — each input has `name`/`description`, or `file`/`from_step` to reference outputs from prior steps
  - `outputs`: Map of output names to objects with `type` (`file` or `files`), `description`, and `required` fields
  - `dependencies`: Other step IDs that must complete first
  - `reviews`: Quality reviews to run when step completes — array of objects with `run_each` (output name or `step`), `quality_criteria` (map of criterion name to expected state), and optional `additional_review_guidance` (context for the reviewer)

### steps/

Each step has a markdown file with detailed instructions that guide the AI agent through executing that step. These files include:

- Context and goals for the step
- Specific actions to take
- Expected outputs and quality criteria
- Examples of good output

## Using a Job from the Library

1. Browse the jobs in this directory
2. Copy the job folder to your project's `.deepwork/jobs/` directory
3. Run `/deepwork` to start the job — the MCP server will discover it automatically

## Using Library Jobs via Nix Dev Shell

Instead of copying jobs into your project, you can keep them live and up-to-date by cloning the DeepWork repo and pointing your dev shell at its library. This lets you receive upstream improvements and contribute back.

### Setup

1. Clone the DeepWork repo (or a sparse subset — see below) into `.deepwork/upstream/` in your project:

```bash
git clone https://github.com/Unsupervisedcom/deepwork.git .deepwork/upstream
```

2. Add `.deepwork/upstream/` to your `.gitignore`:

```
.deepwork/upstream/
```

3. Set `DEEPWORK_ADDITIONAL_JOBS_FOLDERS` in your `flake.nix` shellHook:

```nix
shellHook = ''
  export REPO_ROOT=$(git rev-parse --show-toplevel)

  # Clone DeepWork library jobs if not present
  if [ ! -d "$REPO_ROOT/.deepwork/upstream" ]; then
    git clone --sparse --filter=blob:none \
      https://github.com/Unsupervisedcom/deepwork.git \
      "$REPO_ROOT/.deepwork/upstream"
    git -C "$REPO_ROOT/.deepwork/upstream" sparse-checkout set --cone library/jobs/
  fi

  export DEEPWORK_ADDITIONAL_JOBS_FOLDERS="$REPO_ROOT/.deepwork/upstream/library/jobs"
'';
```

Library jobs now appear in `/deepwork` alongside your local and standard jobs.

### Sparse Checkout (Specific Jobs Only)

If you only need certain library jobs, use a sparse checkout to minimize disk usage:

```bash
# Clone with sparse checkout enabled (downloads minimal data)
git clone --sparse --filter=blob:none \
  https://github.com/Unsupervisedcom/deepwork.git \
  .deepwork/upstream

cd .deepwork/upstream

# Check out only the jobs you need
git sparse-checkout set --cone library/jobs/repo/

# Add more jobs later as needed
git sparse-checkout add library/jobs/spec_driven_development/
```

To update your checkout with the latest upstream changes:

```bash
git -C .deepwork/upstream pull
```

## Contributing Improvements Back

When you use a library job and discover improvements, you can contribute them back upstream.

### The Learn Flow

1. Run the library job in your project as normal
2. Run `/deepwork deepwork_jobs learn` — the learn step classifies improvements as:
   - **Generalizable**: Improvements that benefit all users (update the library job)
   - **Bespoke**: Improvements specific to your project (update your local `AGENTS.md`)

### Submitting Generalizable Improvements

For improvements classified as generalizable:

1. Create a branch in the upstream checkout:

```bash
cd .deepwork/upstream
git checkout -b improve/repo-job-step-name
```

2. Make your changes to the library job files

3. Run the portability review to ensure your changes are portable:

```bash
# From the upstream checkout
/deepwork:review
```

The `library_job_portability` review rule checks for hardcoded paths, personal information, platform-specific assumptions, and schema compliance. All library job changes must pass this review before submitting a PR.

4. Commit, push, and open a PR:

```bash
git add library/jobs/
git commit -m "feat(library): improve repo job step description"
git push -u origin improve/repo-job-step-name
gh pr create --title "feat(library): improve repo job step description" \
  --body "Description of the improvement and why it benefits all users"
```

## Contributing

To add a job to the library, ensure it follows the structure above and includes clear, actionable instructions in each step file.
