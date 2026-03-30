# Job Schema Reference

Before creating or editing any `job.yml` file, you MUST read the JSON schema at
`.deepwork/job.schema.json`. This schema is the authoritative source of truth for
all valid fields, types, and structures.

Key schema rules:
- `step_arguments` is an array of {name, description, type: "string"|"file_path"} with optional `review` and `json_schema`
- `workflows` is an object keyed by workflow name, each with {summary, steps[]}
- Each step has {name, instructions (inline string), inputs, outputs, process_requirements}
- Inputs/outputs reference step_arguments by name
- No `version`, no root-level `steps[]`, no `instructions_file`, no hooks, no dependencies

Always read the schema file and validate your job.yml structure against it.
