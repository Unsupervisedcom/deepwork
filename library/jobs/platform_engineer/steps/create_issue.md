# Create Platform Issue

## Objective

Create a well-structured GitHub issue for a platform engineering concern, automatically gathering relevant context from the repository and environment. The issue MUST be immediately actionable by a platform engineer or agent who reads it without needing to ask clarifying questions.

## Task

Gather the issue description from the user, automatically collect environmental and repository context, format the issue using the platform issue template, create it via `gh issue create`, and output the issue URL.

### Process

#### 1. Ask the user for the issue description

Use `AskUserQuestion` to ask the user to describe the platform engineering issue. The question should prompt for:
- What is the problem or request?
- What is the impact? (Who is affected? Is this blocking work?)
- Any relevant error messages or symptoms?

If the user provides a terse description (e.g., "CI is slow"), ask a follow-up question to get enough detail for a useful issue. The goal is to capture enough information that someone reading the issue can understand the problem without context from this conversation.

If the user has already provided a detailed description in the `issue_description` input, skip the follow-up question and proceed directly.

#### 2. Gather context automatically

Collect context from the repository and environment. This information enriches the issue without requiring the user to provide it manually.

**Repository information:**
- Get the repository name and owner from `git remote get-url origin`
- Get the current branch from `git branch --show-current`
- Get the default branch from `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`
- Get recent commits on the current branch (last 5) from `git log --oneline -5`
- Check if there are uncommitted changes from `git status --porcelain`

**CI/CD status (if applicable):**
- Check recent CI runs on the current branch: `gh run list --branch <current-branch> -L 3 --json status,conclusion,name,createdAt`
- If the issue is CI-related and there is a recent failed run, note the run ID and workflow name
- Do NOT download full CI logs into the issue — reference the run URL instead

**Recent errors (if the user mentions specific errors):**
- If the user mentions a log file, read the relevant portion (last 50 lines) and include key error lines in the issue
- If the user mentions a failing command, run it and capture the output (truncated to 100 lines)
- Do NOT include full stack traces — include the error summary and note where the full output can be found

**Related files:**
- If the user mentions specific files, verify they exist and include their paths
- If the issue relates to CI, note the CI config files (`.github/workflows/*.yml`, etc.)
- If the issue relates to infrastructure, note the relevant infrastructure config files (from the repo structure)
- If the issue relates to dependencies, note the relevant lockfile and manifest

**Related issues:**
- Search for existing related issues: `gh issue list --search "<relevant keywords>" --limit 5`
- If related issues are found, include references in the issue body
- This helps avoid duplicate issues and provides context for the resolver

**Environment information:**
- OS and version: `uname -sr` or equivalent
- Shell: `echo $SHELL`
- Key tool versions relevant to the issue (e.g., if CI-related: `gh --version`; if Docker-related: `docker --version`)

#### 3. Determine issue metadata

**Title:**
- Format: concise, descriptive, prefixed with the area in brackets
- Examples:
  - `[CI] GitHub Actions build exceeds 15-minute budget`
  - `[monitoring] No alerting configured for payment service`
  - `[infra] Database PVC approaching 80% capacity`
  - `[dev-env] Nix flake evaluation fails after nixpkgs update`
  - `[security] Critical CVE in base container image`
- Keep titles under 80 characters
- Do not include issue numbers or PR references in the title

**Labels:**
- Apply the `platform` label if it exists in the repository
- Apply severity labels based on impact:
  - `P1` / `critical`: Production is down or data is at risk
  - `P2` / `high`: Significant functionality is impaired or a deadline is at risk
  - `P3` / `medium`: Important but not urgent — normal priority
  - `P4` / `low`: Nice to have, no immediate impact
- Apply type labels based on the nature of the issue:
  - `bug`: Something is broken
  - `enhancement`: Improvement to existing infrastructure
  - `security`: Security-related issue
  - `performance`: Performance issue (CI speed, resource usage, etc.)
  - `documentation`: Missing or outdated documentation
  - `ci`: CI/CD-related
  - `infrastructure`: Infrastructure-related
  - `monitoring`: Observability-related

**IMPORTANT**: You MUST check which labels exist in the repository using `gh label list` BEFORE constructing the `gh issue create` command. Build the list of `--label` flags from only labels that exist. If a label does not exist, skip it — note in the output that the label was not applied. Never include a label in `gh issue create` without first confirming it exists, as the command will fail entirely if any label is missing.

**Assignees:**
- Do NOT assign the issue unless the user explicitly requests it
- If the user requests assignment, use `gh issue edit <number> --add-assignee <username>`

**Milestone:**
- Check for open milestones: `gh api repos/{owner}/{repo}/milestones --jq '.[].title'`
- If a relevant milestone exists, ask the user via AskUserQuestion if the issue should be added to it
- If no milestones exist or none are relevant, skip milestone assignment

#### 4. Format the issue body

Use the platform issue template to structure the issue body. Every section MUST be present, even if the content is "N/A" or "Not applicable".

```markdown
## Context

**Repository**: <owner>/<repo>
**Branch**: <current branch>
**Default Branch**: <default branch>
**Date**: <today's date>
**Recent Commits** (on current branch):
- `<hash>` <message>
- `<hash>` <message>
- ...

**Environment**:
- OS: <os and version>
- Shell: <shell>
- Key tools: <relevant tool versions>

**CI Status** (if applicable):
- Recent runs: <status of last 3 runs on this branch>
- Failed run: <URL if applicable>

## Problem / Request

<User's description of the problem, edited for clarity but preserving all details.
 Expand the user's input with additional context gathered — do not simply copy-paste
 a terse description. The reader should understand the problem fully from this section.>

<If error messages were provided, include them in a code block:>
```
<error output>
```

## Impact

- **Who is affected**: <developers, users, CI pipelines, production services, etc.>
- **Urgency**: <blocking | high | medium | low>
- **Current workaround**: <description of workaround, or "None">
<If production is affected, note when the issue started (if known)>

## Relevant Files

- `<path/to/file>` — <brief description of why this file is relevant>
- `<path/to/file>` — <brief description>
- ...

(If no specific files are relevant, state: "No specific files identified — requires investigation.")

## References

- <Link to related issues, PRs, docs, dashboards, or incidents>
- <If no related issues found: "No related issues found.">

## Checklist

- [ ] <action item derived from the problem description>
- [ ] <action item>
- [ ] <action item>
- ...
```

**Checklist guidelines:**
- Derive checklist items from the problem description — break the work into actionable steps
- Each item should be completable independently where possible
- Include investigation items if the root cause is unknown (e.g., "Investigate why X is happening")
- Include verification items (e.g., "Verify fix in staging before production")
- Include documentation items if the fix requires documentation updates
- Aim for 3-7 checklist items — too few suggests the issue is underspecified, too many suggests it should be split

#### 5. Create the issue via gh

Run `gh issue create` with the formatted title, body, and labels:

```bash
# Only include --label flags for labels confirmed to exist via gh label list
gh issue create \
  --title "<title>" \
  --label "<confirmed-label-1>" \
  --label "<confirmed-label-2>" \
  --body "$(cat <<'EOF'
<issue body>
EOF
)"
```

The issue creation MUST succeed on the first attempt. Never include labels that haven't been confirmed to exist.

Capture the issue URL from the command output.

#### 6. Output the issue URL

Write the issue URL to `github_issue_url.md` and present it to the user.

If additional context was gathered that could not fit in the issue (e.g., a large log file), inform the user where the full data can be found.

## Output Format

### github_issue_url.md

```markdown
# Created Platform Issue

**URL**: <full GitHub issue URL>
**Number**: #<issue number>
**Title**: <issue title>
**Labels**: <labels applied>
**Repository**: <owner>/<repo>
**Created**: <timestamp>

## Summary

<1-2 sentence summary of what the issue is about>

## Notes

<Any labels that could not be applied because they do not exist in the repo>
<Any additional context gathered but not included in the issue>
```

## Quality Criteria

- **Issue Created**: A GitHub issue was created successfully via `gh issue create`. The issue URL is captured and written to `github_issue_url.md`. The command did not fail.
- **Properly Formatted**: The issue follows the platform issue template with all six sections present: Context, Problem/Request, Impact, Relevant Files, References, and Checklist. No section is omitted. The Problem/Request section is detailed enough that a reader can understand the issue without additional context.
- **Context Gathered Automatically**: Repository information (repo name, branch, recent commits), CI status (if applicable), and environment details are gathered automatically without requiring the user to provide them. Related existing issues are searched for and referenced if found.
- **Labels Applied**: Appropriate labels are applied (severity and type labels as applicable). Labels are validated against `gh label list` BEFORE the `gh issue create` call — never after. If a label does not exist in the repository, it is skipped and noted in the output.
- **Actionable Checklist**: The checklist contains 3-7 actionable items derived from the problem description. Each item represents a concrete step toward resolution. Investigation items are included when the root cause is unknown.
- **Clear Title**: The issue title is concise (under 80 characters), prefixed with the area in brackets (e.g., `[CI]`, `[infra]`, `[monitoring]`), and descriptive enough to understand the issue without reading the body.
- **No Sensitive Data**: Error messages are included but secrets, tokens, passwords, and credentials are never included in the issue body. Environment variable values are not exposed — only their names and whether they are set. `.env` file contents are never read.

## Context

This step is the sole step in the `platform_issue` workflow and does NOT depend on `gather_context`. It is designed to be a quick, standalone workflow for creating well-structured platform issues from any context.

Unlike other workflows in this job, the `platform_issue` workflow does not have a `gather_context` dependency. This is intentional — creating an issue should be fast and not require a full environment scan. The step gathers only the context relevant to the issue being created.

The platform issue template is designed to make issues immediately actionable. A platform engineer reading the issue should be able to:
1. Understand the problem from the title and Problem/Request section
2. Know the context (repo, branch, environment) from the Context section
3. Assess priority from the Impact section and labels
4. Find relevant code from the Relevant Files section
5. See related work from the References section
6. Start working from the Checklist

This step may also be used as a reference by other workflows. For example, the `diagnose_dev` step creates a GitHub issue when a dev environment problem cannot be resolved. The format here serves as the canonical platform issue template for the entire job.
