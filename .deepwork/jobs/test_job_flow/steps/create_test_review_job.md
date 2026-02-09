# Create Test Review Job via Sub-Agent

## Objective

Launch the DeepWork `new_job` workflow as a nested sub-agent to create a job called `detailed_test_review`. This exercises the full job creation pipeline end-to-end.

## Task

Start the `deepwork_jobs/new_job` workflow as a nested workflow (using `start_workflow`), providing extremely prescriptive instructions so the sub-agent can complete the entire job creation without needing to ask the user any questions. Then follow through all the steps of that nested workflow until it completes.

### Process

1. **Start the nested workflow**
   - Call `start_workflow` with `job_name: deepwork_jobs`, `workflow_name: new_job`, `instance_id: detailed_test_review`
   - Use a goal that contains ALL the details below so the sub-agent has full context

2. **Guide the nested workflow through the `define` step**
   When the nested workflow starts on its `define` step, create the `detailed_test_review` job with these exact specifications:

   **Job name**: `detailed_test_review`
   **Summary**: "Run tests with coverage and update README with results"
   **Description**: A two-step workflow that runs the project's test suite with code coverage enabled, reviews test quality and coverage thresholds, then updates the README with the coverage results.

   **Step 1 - `run_tests`**:
   - Name: "Run Tests with Coverage"
   - Description: Run all project tests with code coverage reporting enabled. Collect the test files and the coverage report as outputs.
   - No user inputs (it auto-detects tests)
   - Outputs (note: every output MUST include `required: true` or `required: false`):
     - `test_files` (type: `files`, required: true): All test files that were executed
     - `coverage_report` (type: `file`, required: true): The code coverage report file
   - Dependencies: none
   - Reviews:
     - `run_each: test_files` with quality criteria:
       - "On-Topic Tests": "Are all tests in this file on-topic and relevant to the module or functionality being tested? Flag any tests that seem unrelated or misplaced."
     - `run_each: step` with quality criteria:
       - "Coverage Threshold": "Does the code coverage report show overall coverage above 60%? If not, what areas have low coverage?"

   **Step 2 - `update_readme`**:
   - Name: "Update README with Coverage"
   - Description: Update the project README to include the code coverage percentage with an as-of date at the very end of the file.
   - Inputs:
     - `coverage_report` from step `run_tests`
   - Outputs:
     - `readme` (type: `file`, required: true): The updated README.md file
   - Dependencies: `run_tests`
   - Reviews:
     - `run_each: readme` with quality criteria:
       - "Coverage Line Present": "Does the README have a line at the very end showing the code coverage percentage?"
       - "Date Included": "Does the coverage line include an as-of date?"

3. **Follow through all nested workflow steps**
   After `define`, the nested workflow will proceed to `implement` (creating step instruction files) and potentially `test` and `iterate`. Follow each step's instructions as they come.

4. **Collect the output**
   Once the nested workflow completes, the `detailed_test_review` job should exist at `.deepwork/jobs/detailed_test_review/job.yml`. This is the output for this step.

## Output Format

### job_yml

The job.yml file created by the nested workflow at `.deepwork/jobs/detailed_test_review/job.yml`.

**Expected structure**:
```yaml
name: detailed_test_review
version: "1.0.0"
summary: "Run tests with coverage and update README with results"
description: |
  A two-step workflow that runs the project's test suite with code coverage
  enabled, reviews test quality and coverage thresholds, then updates the
  README with the coverage results.

steps:
  - id: run_tests
    name: "Run Tests with Coverage"
    outputs:
      test_files:
        type: files
        description: "All test files that were executed"
        required: true
      coverage_report:
        type: file
        description: "The code coverage report file"
        required: true
    reviews:
      - run_each: test_files
        quality_criteria:
          "On-Topic Tests": "..."
      - run_each: step
        quality_criteria:
          "Coverage Threshold": "..."

  - id: update_readme
    name: "Update README with Coverage"
    inputs:
      - file: coverage_report
        from_step: run_tests
    outputs:
      readme:
        type: file
        description: "The updated README.md file"
        required: true
    reviews:
      - run_each: readme
        quality_criteria:
          "Coverage Line Present": "..."
          "Date Included": "..."
```

## Quality Criteria

- The nested workflow ran to completion (all steps finished)
- The `detailed_test_review` job.yml exists and is valid YAML
- It defines exactly two steps: `run_tests` and `update_readme`
- `run_tests` has both `test_files` (files) and `coverage_report` (file) outputs
- `run_tests` has a for_each file review on `test_files` and a for_each step review for coverage
- `update_readme` takes `coverage_report` as input from `run_tests`
- `update_readme` produces a `readme` output
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Context

This step is the core exercise of the test_job_flow. By running the full job creation workflow as a nested sub-agent, we can observe the entire process end-to-end and identify any friction points. The transcript from this step will be reviewed in the next step.
