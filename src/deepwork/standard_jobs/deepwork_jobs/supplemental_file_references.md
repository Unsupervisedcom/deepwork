# Job Schema Reference

The JSON schema at `.deepwork/job.schema.json` documents all valid fields, types,
and structures for `job.yml` files. You can read it to understand what fields are
available, but you do NOT need to manually validate against it — DeepSchema quality
gates validate `job.yml` files automatically when steps complete.

Key schema rules:
- `step_arguments` is an array of {name, description, type: "string"|"file_path"} with optional `review` and `json_schema`
- `workflows` is an object keyed by workflow name, each with {summary, steps[]}
- Each step has {name, instructions (inline string), inputs, outputs, process_requirements}
- Inputs/outputs reference step_arguments by name
- No `version`, no root-level `steps[]`, no `instructions_file`, no hooks, no dependencies
