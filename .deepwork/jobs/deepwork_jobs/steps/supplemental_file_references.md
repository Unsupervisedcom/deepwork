# Supplementary Reference Files

Step instructions can include additional `.md` files in the `steps/` directory. These supplementary files are useful for:

- Providing detailed examples or templates that would clutter the main instruction file
- Sharing common reference material across multiple steps
- Including technical specifications, API documentation, or style guides

## How to Use

1. Place additional `.md` files in the `steps/` directory alongside the main step instruction files
2. Reference them in your step instructions using the **full path from the project root**

## Example

If you have a job called `my_job` and want to include an API specification template:

1. Create the file at `.deepwork/jobs/my_job/steps/api_spec.md`
2. Reference it in your step instructions like this:

```markdown
Use the template in `.deepwork/jobs/my_job/steps/api_spec.md` to structure your API endpoints.
```

## Path Format

Always use the full relative path from the project root:

```
.deepwork/jobs/[job_name]/steps/[filename].md
```

For example:
- `.deepwork/jobs/competitive_research/steps/competitor_template.md`
- `.deepwork/jobs/api_design/steps/endpoint_schema.md`
- `.deepwork/jobs/onboarding/steps/checklist_template.md`

## Benefits

Using supplementary files keeps your main step instructions focused and readable while allowing you to provide detailed reference material when needed. The AI agent can read these files during execution to get additional context.
