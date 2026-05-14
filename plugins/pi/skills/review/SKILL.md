---
name: review
description: "Run DeepWork Reviews on the current branch using .deepreview rules"
---

# DeepWork Review

Run automated code reviews on the current branch based on `.deepreview` config files.

## Routing

Stop and redirect if either applies:

- User wants to configure, create, or modify review rules -> use `configure-reviews`
- User wants to add a doc-sync rule -> call `start_workflow` with `job_name="deepwork_reviews"` and `workflow_name="add_document_update_rule"`

Only proceed if the user wants to run reviews.

## How to Run

Pi's DeepWork extension registers `/review` as a command. If this skill body is loaded
instead of the command, continue with the manual fallback below.

1. Call `get_review_instructions`.
   - No arguments reviews the current branch's changes.
   - With `files`, reviews only specific files.
   - If no rules are configured, ask whether the user wants to set up rules. If yes, invoke `deepwork_reviews` / `discover_rules`.
2. The output lists review tasks with `prompt_file` values. If a Pi subagent or parallel-delegation extension is available, dispatch them in parallel. Otherwise, run them one at a time in this session.
3. For each task, read the `prompt_file`, follow it exactly, and report findings with file and line references.
4. While reviews run, check changelog and PR description if relevant.
5. Act on findings and iterate until clean or explicitly skipped.

If direct MCP tools are not visible, use the `mcp` proxy tool: search for `get_review_instructions`, then call the returned tool name with JSON-string arguments.

## Changelog & PR Description Check

Run this concurrently with review tasks when possible:

1. Check for a changelog file.
2. If a changelog exists and there are branch commits, verify the unreleased/current section reflects the branch. Update it if needed.
3. If a PR is open and you updated the changelog, verify the PR description matches.

## Acting on Results

- Make obviously good, low-risk fixes immediately.
- Ask the user before refactors, architectural changes, style tradeoffs, or anything debatable.
- When dismissing a finding, call `mark_review_as_passed` with the review ID so it does not re-run while files remain unchanged.

## Iterate

After making changes, call `get_review_instructions` with `files` set only to files edited during this iteration. Re-run only tasks that had findings last time.
