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
└── spec_driven_development/
    ├── job.yml              # Job definition (name, steps, dependencies)
    ├── readme.md            # Job-specific documentation
    └── steps/
        ├── constitution.md  # Instructions for each step
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
  - `quality_criteria`: Measurable criteria for step completion

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

## Contributing

To add a job to the library, ensure it follows the structure above and includes clear, actionable instructions in each step file.
