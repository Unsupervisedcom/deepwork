# Update Test Fixtures

## Objective

Update all test fixture job.yml files under `tests/fixtures/jobs/` to conform to the updated schema, while preserving each fixture's intended test purpose.

## Task

Test fixtures are job.yml files used in unit and integration tests. They must conform to the schema or intentionally violate it (in the case of `invalid_job`). After a schema change, fixtures need updating to prevent test failures.

### Process

1. **Read the change summary**
   - Read `.deepwork/tmp/schema_change_summary.md` for what changed
   - Identify whether the change adds required fields, modifies existing fields, or removes fields

2. **Find all fixture job.yml files**
   - Use glob to find all `tests/fixtures/jobs/*/job.yml` files
   - Current known fixtures:
     - `tests/fixtures/jobs/simple_job/job.yml` — minimal single-step job
     - `tests/fixtures/jobs/complex_job/job.yml` — multi-step with dependencies
     - `tests/fixtures/jobs/concurrent_steps_job/job.yml` — concurrent workflow steps
     - `tests/fixtures/jobs/exposed_step_job/job.yml` — step visibility testing
     - `tests/fixtures/jobs/fruits/job.yml` — simple two-step job
     - `tests/fixtures/jobs/invalid_job/job.yml` — intentionally invalid for validation tests
     - `tests/fixtures/jobs/job_with_doc_spec/job.yml` — doc_spec functionality
   - There may be additional fixtures — always glob to find them all

3. **Update each fixture**
   - Read each fixture file
   - Apply the schema change (add new fields, modify existing ones, etc.)
   - **Preserve test intent**: Each fixture exists for a specific testing purpose:
     - `simple_job`: Keep it minimal — only add new required fields
     - `complex_job`: Add new fields in a realistic multi-step context
     - `invalid_job`: Keep intentionally invalid, but update the *type* of invalidity if the old invalid fields are now valid or vice versa
     - Others: Update to conform while maintaining their special characteristics

4. **Verify schema conformance**
   - For valid fixtures: ensure they would pass validation against the updated schema
   - For `invalid_job`: ensure it still fails validation, and the reason is still testable

### Key Files

- **Fixtures directory**: `tests/fixtures/jobs/`
- **Updated schema**: `src/deepwork/schemas/job.schema.json`
- **Change summary**: `.deepwork/tmp/schema_change_summary.md`

## Output Format

### fixture_files

All updated fixture job.yml files. Each should be a valid (or intentionally invalid) job.yml that conforms to (or intentionally violates) the updated schema.

**Example — adding a new required `reviews` field to fixtures:**

Before (simple_job/job.yml, missing new required field):
```yaml
steps:
  - id: greet
    name: "Greet"
    outputs:
      greeting:
        type: file
        description: "A greeting"
        required: true
```

After (simple_job/job.yml, with new required field added minimally):
```yaml
steps:
  - id: greet
    name: "Greet"
    outputs:
      greeting:
        type: file
        description: "A greeting"
        required: true
    reviews: []  # Required field, empty for simple fixtures
```

**Example — updating invalid_job to test invalidity of the new field:**

```yaml
steps:
  - id: bad_step
    reviews: "not_an_array"  # Invalid type — should be array, not string
```

**Common mistake to avoid**: Don't add optional fields to `simple_job` — keep it minimal. Add optional fields to `complex_job` where realistic multi-step usage is demonstrated. Don't accidentally fix the `invalid_job` — it must remain intentionally invalid.

**For valid fixtures**, ensure all new required fields are present and new optional fields are used in at least one fixture (preferably `complex_job`) to ensure they're testable.

**For invalid_job**, verify the file still triggers a validation error, and consider adding a test of the new field being invalid if applicable.

## Quality Criteria

- All valid fixture job.yml files conform to the updated schema
- The `invalid_job` fixture still fails validation intentionally
- Each fixture preserves its original test purpose and characteristics
- New required fields are added to all valid fixtures
- At least one fixture demonstrates usage of new optional fields
- When all criteria are met, include `<promise>✓ Quality Criteria Met</promise>` in your response

## Context

Test fixtures are the foundation of the test suite. If they don't match the schema, parser tests will fail before we even get to test the new functionality. Updating fixtures early (before tests) means we can run the test suite incrementally as we update test code.
