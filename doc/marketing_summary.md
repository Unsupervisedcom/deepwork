# DeepWork Marketing Summary

## Value Proposition

**DeepWork makes AI agents trustworthy through reliability, not guardrails.**

The industry is focused on agent safety via guardrails — human-in-the-loop approvals, output filters, permission gates. That prevents agents from doing something destructive. DeepWork solves the other half: getting agents to reliably do the right things in complex situations.

## The Problem

Simple agent tasks work fine. Complex, multi-step processes fall apart:

- Agents skip steps or invent shortcuts
- They forget context between steps
- They don't check their work against your standards
- Results are inconsistent across runs
- They miss interdependencies and the need to take certain actions elsewhere from their direct changes

The result: you babysit the agent, defeating the purpose of automation.

## How DeepWork Solves It

Deepwork brings techniques from managing humans and human processes to the agentic world.

Three complementary systems:

1. **Workflows** — Structured, step-by-step execution with quality gates. The agent can't skip ahead or go off-script. You define the process once in plain English, DeepWork hardens it into a repeatable workflow.

2. **DeepSchemas** — "Best Practices" documentation. File-level contracts that define what makes for a good file of a given type. When an agent writes or edits a file, applicable schemas are validated immediately — at write time, before it ever reaches review. Requirements use RFC 2119 keywords (MUST/SHOULD/MAY) so enforcement severity is explicit. Define a schema once for a file type, and every matching file is held to the same standard.

3. **Reviews** — Automated verification rules that run against every change. Catches style regressions, documentation drift, security issues, and requirements losing test coverage. DeepSchemas automatically generate review rules too, so schema requirements are enforced both at write time and during review.

Together: workflows enforce the right process, DeepSchemas enforce file-level contracts at write time, and reviews verify the overall output meets your standards. Three layers of reliability reinforcing each other.

## Cross-Domain Examples

- **Coding**: Ensuring the agent follows a TDD process
- **Data analysis**: Ensuring data query results are cited properly in the final report
- **Marketing**: Making sure customer quotes shown are all real and approved for publication

## Origin

Built from hard-won learnings in AI data analysis — where reliability is critical and hallucinated numbers can't be tolerated — then generalized for any high-discretion agent or CLI workflow.

## Traction / Social Proof

- NASA researchers uses it for analysis and simulations
- Multiple startups automating processes with it
- Builds itself at an insanely low defect level (0.27 defects per 1k LOC)

## Product Details

- Delivered as a plugin for AI agent CLIs (Claude Code, Gemini CLI, Claude Desktop)
- Git-native: all work products versioned for collaboration and review
- Domain-agnostic: works for any multi-step workflow, not just coding
- One-command install, define jobs in plain English
- 89% test coverage across 783 tests
- ~62K lines of code
- 234 merged PRs to date (87 adding new functionality, 31 bug fixes)

## How DeepWork Uses It On Itself

DeepWork is its own most demanding user. Every system it offers — workflows, DeepSchemas, reviews, hooks — is actively enforced on the DeepWork codebase itself. This isn't a demo; it's how the project actually ships.

### Workflows Define How Jobs Are Built

The `deepwork_jobs` standard workflow governs how new jobs are created: define → implement → test → iterate → learn. Every job definition in the project was built through this workflow, with quality gates at each step. There's even a meta-workflow (`test_job_flow`) that runs the job-creation workflow as a sub-agent, analyzes the transcript for friction points, and produces engineering recommendations — DeepWork testing its own creation process by using it.

### DeepSchemas Enforce File Contracts at Write Time

Two named DeepSchemas validate the project's most critical file types:

- **`job_yml`** — 20+ requirements enforced on every `job.yml` file. Catches issues like missing data flow declarations, vague step descriptions, duplicated context, and non-RFC-2119 review criteria. Every job definition — standard, library, and bespoke — is held to the same contract.
- **`deepschema`** — Validates DeepSchema definitions themselves. Requirements must use RFC 2119 keywords, matchers must be present for named schemas, verification commands must be non-destructive.

These aren't checked at PR time — they fire immediately when an agent writes or edits a file, via the `deepschema_write` hook. The agent gets instant feedback and fixes issues before they ever reach review.

### 12+ Review Rules Catch Everything Else

The `.deepreview` configuration runs automated reviews on every change:

- **Prompt quality**: All instruction files (CLAUDE.md, skill definitions, job step instructions, `.deepreview` rules themselves) are reviewed against Anthropic prompt engineering best practices.
- **Code quality**: Python files get convention checks and auto-linting (ruff + mypy). Shell scripts get safety and portability reviews.
- **Documentation drift**: A dedicated rule detects when source code changes but related documentation (architecture docs, MCP interface docs, README) hasn't been updated.
- **Requirements traceability**: Every RFC 2119 requirement in a spec must have either an automated test or a review rule validating it — no untested requirements allowed.
- **Review rule quality**: The `.deepreview` configs themselves are reviewed for rule consolidation, overly broad patterns, description accuracy, and correct directory placement.
- **Schema-instruction compatibility**: When the job schema or standard job instructions change, a rule verifies they still agree on field names, required vs. optional status, and terminology.
- **New rule suggestions**: After every change, a conservative rule analyzes the diff and suggests new review rules that would catch similar issues going forward.

### Hooks Enforce Standards at the Moment of Action

Four hook scripts fire at key moments during agent work:

- **Write-time schema validation** — Every file write or edit is checked against applicable DeepSchemas immediately, before the agent moves on.
- **Post-commit review reminder** — After any `git commit`, the agent is reminded to run reviews on the changes.
- **Context restoration after compaction** — When Claude Code compacts its context window, a hook restores the full workflow state (current step, goal, instructions) so the agent seamlessly resumes mid-workflow.
- **Session identity injection** — Every session and sub-agent gets a stable ID for workflow state tracking.

### The Result: A Virtuous Cycle

DeepWork's own development produces the learnings that improve the framework. When a review rule catches a real issue in a PR, that validates the rule. When a DeepSchema fires at write time and saves an agent from submitting a broken `job.yml`, that validates the schema. When the `test_job_flow` meta-workflow identifies friction in job creation, those findings become concrete improvements to the `deepwork_jobs` workflow.

The 0.27 defects per 1K LOC isn't aspirational — it's what happens when every file type has a contract, every change gets automated review, and the framework that enforces these standards is the same one being developed.

## Key Differentiator

Everyone else: "Prevent agents from doing bad things" (guardrails, permissions, filters)
DeepWork: "Make agents reliably do the right things" (structured process, file contracts, automated verification)

Both matter. Only one is being addressed by the market. DeepWork fills the gap.
