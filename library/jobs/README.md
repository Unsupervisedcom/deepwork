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
├── [job-name]/
│   ├── job.yml              # Job definition (name, steps, dependencies)
│   └── steps/
│       ├── step_one.md      # Instructions for step one
│       ├── step_two.md      # Instructions for step two
│       └── ...
├── [another-job]/
│   ├── job.yml
│   └── steps/
│       └── ...
└── README.md
```

### job.yml

The job definition file contains:

- `name`: Unique identifier for the job
- `version`: Semantic version (e.g., "1.0.0")
- `summary`: Brief description (under 200 characters)
- `description`: Detailed explanation of the job's purpose
- `steps`: Array of step definitions with:
  - `id`: Step identifier
  - `name`: Human-readable step name
  - `description`: What this step accomplishes
  - `instructions_file`: Path to the step's markdown instructions
  - `inputs`: What the step requires
  - `outputs`: What the step produces
  - `dependencies`: Other steps that must complete first

### steps/

Each step has a markdown file with detailed instructions that guide the AI agent through executing that step. These files include:

- Context and goals for the step
- Specific actions to take
- Expected outputs and quality criteria
- Examples of good output

## Using a Job from the Library

1. Browse the jobs in this directory
2. Copy the job folder to your project's `.deepwork/jobs/` directory
3. Run `/deepwork_jobs.refine` to customize it for your needs
4. Run `deepwork sync` to generate the slash commands

## Contributing

To add a job to the library, ensure it follows the structure above and includes clear, actionable instructions in each step file.
