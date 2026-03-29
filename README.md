# DeepWork — Make AI Agents Trustworthy at Complex Tasks

AI agents are powerful, but they're unreliable. They go off-script, skip steps, hallucinate details, and don't check their own work. The more complex the task, the worse it gets.

DeepWork fixes this with two systems: **Workflows** that force agents to follow a structured process step by step, and **Reviews** that automatically verify every change against your rules. Together, they make agents trustworthy enough to run autonomously on real work.

## Install

### Claude Code (Terminal)
```
claude plugin marketplace add Unsupervisedcom/deepwork
claude plugin install deepwork@deepwork-plugins
```

Then start a new session and define your first job:
```
/deepwork Make a job for doing competitive research. It will take the URL of the competitor as an input, and should make report including a SWOT analysis for that competitor.
```

### Claude Desktop

1. Enter Cowork mode (toggle at top of screen)
2. Select `Customize with plugins` at the bottom of the page.
3. Select `Personal`, click the `+`, and select `Add marketplace from GitHub'`
4. Set the URL to ```Unsupervisedcom/deepwork``` and press Sync. (adding a marketplace currently fails on Windows)
5. Select the deepwork plugin and click Install.
6. In Cowork mode, select 'Start a deepwork workflow'

> **Note:** DeepWork stores job definitions in `.deepwork/jobs/` and creates work branches in Git. Your project folder should be a Git repository. If it isn't, run `git init` first, or ask Claude to do so.

---

## The Problem

When you ask an agent to do something simple — write a function, answer a question — it works great. But when you ask it to execute a multi-step process — research a topic across multiple sources, audit a codebase, produce a structured report — things fall apart:

- It **skips steps** or invents shortcuts
- It **forgets context** between steps
- It **doesn't check its work** against your standards
- It produces **inconsistent results** every time you run it

You end up babysitting the agent, which defeats the purpose of automation.

## How DeepWork Solves This

DeepWork gives you two complementary systems that work together to make agents trustworthy:

### Workflows: Structured Execution with Quality Gates

Workflows force the agent to follow a strict, step-by-step process. Each step has defined inputs, outputs, and quality checks. The agent can't skip ahead or go off-script — it must complete each step and pass its quality gates before moving on.

You define workflows by describing what you want in plain English. DeepWork asks you questions to refine the process, then generates a hardened multi-step workflow that the agent follows consistently every time.

```
/deepwork write a tutorial for how to use a new feature we just launched
```

DeepWork asks you questions (~10 minutes), then writes the steps. After that, you can run it whenever:

```
/deepwork tutorial_writer
```

The agent follows the workflow step by step, every time, the same way. You build the skill once and reuse it forever.

### Reviews: Automated Verification of Every Change

Reviews are the second layer of trust. You define review policies in `.deepreview` config files — what files to watch, what to check for, how to group them — and they run automatically against every change.

```
/review
```

One command. Every rule you've defined runs in parallel, each review agent scoped to exactly the files and instructions it needs.

Reviews catch what workflows can't: style regressions, documentation falling out of sync, security issues in code the workflow didn't directly touch, requirements that lost their test coverage.

### Together: Trust Through Process + Verification

Workflows ensure the agent follows the right process. Reviews ensure the output meets your standards. The combination is what makes the difference:

| Without DeepWork | With DeepWork |
|-----------------|---------------|
| Agent skips steps or invents shortcuts | Workflow enforces every step in order |
| No quality checks on output | Quality gates block progress until standards are met |
| Inconsistent results every run | Same process, same structure, every time |
| Changes break things silently | Review rules catch regressions automatically |
| You babysit the agent | You review the finished work |

---

## Quick Start

### 1. Install the Plugin

In Claude Code:
```
claude plugin marketplace add Unsupervisedcom/deepwork
claude plugin install deepwork@deepwork-plugins
```

Start a new Claude Code session after installing.

> **Note:** If your folder isn't a Git repo yet, run `git init` first.

### 2. Define Your First Workflow

Start simple — something you do manually in 15-30 minutes:

```
/deepwork write a tutorial for how to use a new feature we just launched
```

DeepWork asks you questions (~10 minutes) then writes the steps. You're creating a **reusable skill** — you only do this once.

### 3. Run It

```
/deepwork tutorial_writer
```

Claude follows the workflow step by step.

### 4. Set Up Reviews

```
/configure_reviews
```

DeepWork analyzes your project and creates `.deepreview` files with review rules tailored to your codebase. From then on, `/review` checks every change.

---

## Example: Competitive Research Workflow

You can make a DeepWork job that automatically runs deep competitive research:
- Run `/deepwork` in Claude Code
- Explain your process — _e.g. "Go look at my company's website and social channels to capture any new developments, look at our existing list of competitors, do broad web searches to identify any new competitors, and then do deep research on each competitor and produce a comprehensive set of md reports including a summary report for me."_

DeepWork asks you questions to improve the plan and makes a hardened automation workflow (~10 minutes). Then it documents how Claude should execute each step (~2-5 minutes).

After that, you can run the workflow at any time. Output looks something like:

```
# On your work branch (deepwork/competitive_research-acme-2026-02-21):
competitive_research/
├── competitors.md           # Who they are, what they do
├── competitor_profiles/     # Deep dive on each
├── primary_research.md      # What they say about themselves
└── strategic_overview.md    # Your positioning recommendations
```

_All skills are composable. You can call skills inside of other jobs. For example, create a `make_comparison_document` skill and call it at the end of `/competitive_research` — automating the process of going from research to having final briefings for your sales team._

---

## What People Are Building

| Workflow | What It Does | The Trust Problem It Solves |
|----------|--------------|---------------------------|
| **Email triage** | Scan inbox, categorize, archive, draft replies | Agent must follow consistent categorization rules, not just guess |
| **Competitive research** | Track competitors weekly, generate diff reports | Multi-source research needs structured steps to avoid missing sources |
| **Tutorial writer** | Turn expertise into docs | Quality gates ensure docs actually cover what they should |
| **SaaS user audit** | Quarterly audit of service access | Must check every service systematically, not skip ones it finds boring |

One user used DeepWork to automatically research email performance across hundreds of millions of marketing emails. It accessed data from a data warehouse, came up with research questions, queried to answer those questions, and produced a comprehensive report. The process ran autonomously for ~90 minutes and produced a report better than internal dashboards that had been refined for months.

---

## Who This Is For

**If you can describe a process, you can automate it.**

| You | What You'd Automate |
|-----|---------------------|
| **Founders** | Competitive research, bug discovery and ticket creation, investor updates pulling from multiple sources |
| **Ops** | Daily briefs, SEO analysis, git summaries |
| **Product Managers** | Tutorial writing, QA reports, simulated user testing, updating process docs or sales materials |
| **Engineers** | Standup summaries, code review, release notes |
| **Data/Analytics** | Multi-source data pulls, ETL, custom reports and dashboards |

DeepWork is a free, open-source tool — if you're already paying for a Claude Max subscription, each of these automations costs you nothing additional.

Similar to how vibe coding makes it easier for anyone to produce software, this is **vibe automation**: describe what you want, let it run, and then iterate on what works.

---

## DeepWork Reviews — Deep Dive

Reviews are `.deepreview` config files placed anywhere in your project, scoped to the directory they live in (like `.gitignore`). When you run a review, it diffs your branch, matches changed files against your rules, and dispatches parallel AI review agents.

### Why This Is Powerful

**Define rules once, they enforce forever.** A `.deepreview` file is simple YAML — a few lines to describe what files to match, how to group them, and what the reviewer should look for. No more "we forgot to check for X."

**Reviews aren't limited to code.** Documentation tone, prompt quality, config consistency, CI/CD security — anything that can be expressed as "look at these files and check for this."

**Teams own their own rules.** The security team puts a `.deepreview` in `src/auth/`, the platform team in `infrastructure/`, the docs team in `docs/`. Each file is independent and scoped to its directory.

**Smart file grouping.** Three review strategies control what each reviewer sees:
- **`individual`** — one review per file (best for per-file linting and style checks)
- **`matches_together`** — all matched files reviewed as a group (best for cross-file consistency)
- **`all_changed_files`** — a tripwire: if any sensitive file changes, the reviewer sees _every_ changed file in the branch (best for security audits)

**Pass caching.** When a review passes, it's marked as clean. It won't re-run until one of its reviewed files actually changes — so reviews stay fast even as your rule set grows.

### Quick Example

```yaml
# .deepreview
python_best_practices:
  description: "Review Python files for code quality."
  match:
    include: ["**/*.py"]
    exclude: ["tests/**"]
  review:
    strategy: individual
    instructions: |
      Check for proper error handling, consistent naming,
      and no hardcoded secrets.

prompt_best_practices:
  description: "Review prompt and instruction files for quality."
  match:
    include:
      - "**/CLAUDE.md"
      - "**/AGENTS.md"
      - ".claude/**/*.md"
  review:
    strategy: individual
    instructions: |
      Review this prompt/instruction file for clarity, specificity,
      and adherence to prompt engineering best practices. Flag vague
      instructions, missing examples, and conflicting directives.

requirements_traceability:
  description: "Verify requirements have automated tests."
  match:
    include: ["**/*"]
  review:
    strategy: all_changed_files
    instructions: |
      This project keeps formal requirements in specs/.
      Verify that every requirement has a corresponding
      automated test or review rule that enforces it.
      Flag any requirement missing traceability.

security_audit:
  description: "Full security review when auth code changes."
  match:
    include: ["src/auth/**/*.py"]
  review:
    strategy: all_changed_files
    agent:
      claude: "security-expert"
    instructions: |
      Auth code changed. Review ALL changed files for
      security regressions and leaked credentials.
```

### What People Use Reviews For

| Review Rule | What It Catches |
|-------------|-----------------|
| **Language-specific code review** | Style violations, anti-patterns, bugs — per your project's conventions |
| **Documentation freshness** | Docs that fall out of sync when the code they describe changes |
| **Prompt & instruction review** | Prompt files that don't follow best practices |
| **Migration safety** | Conflicting database migrations, destructive operations |
| **Version sync** | Version numbers that drift across `pyproject.toml`, `CHANGELOG.md`, lock files |
| **CI/CD audit** | Unpinned GitHub Actions, leaked secrets, missing approval gates |
| **Cross-file consistency** | API schema changes without matching client updates |
| **Requirements traceability** | Requirements without corresponding automated tests or enforcement |

See [README_REVIEWS.md](README_REVIEWS.md) for the full reference — strategies, additional context flags, glob patterns, agent personas, and more examples.

---

## Supported Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| **Claude Code** | Full Support | Recommended. Plugin-based delivery with quality hooks. |
| **Gemini CLI** | Partial Support | TOML format skill, manual setup |
| OpenCode | Planned | |
| GitHub Copilot CLI | Planned | |
| Others | Planned | We are nailing Claude and Gemini first, then adding others according to demand |

**Tip:** Use the terminal (Claude Code CLI), not the VS Code extension. The terminal has full feature support.

---

## Browser Automation

For workflows that need to interact with websites, you can use any browser automation tool that works in Claude Code. We generally recommend [Claude in Chrome](https://www.anthropic.com/claude-in-chrome).

**Warning:** Browser automation is still something models can be hit-or-miss on. We recommend using a dedicated Chrome profile for automation.

---

## Troubleshooting

Here are some known issues that affect some early users — we're working on improving normal performance on these, but here are some known workarounds.

### Claude "just does the task" instead of using DeepWork

If Claude attempts to bypass the workflow and do the task on its own, tell it explicitly to use the skill. You can also manually run the step command:
```
/deepwork your_job
```

Tip: Don't say things like "can you do X" while **defining** a new job — Claude has a bias towards action and workarounds and may abandon the skill creation workflow and attempt to do your task as a one off. Instead, say something like "create a workflow that..."

### If you can't solve your issues using the above and need help

Send [@tylerwillis](https://x.com/tylerwillis) a message on X.

---

<details>
<summary><strong>Advanced: Directory Structure</strong></summary>

```
your-project/
├── .deepwork/
│   ├── tmp/               # Session state (created lazily)
│   └── jobs/              # Job definitions
│       └── job_name/
│           └── job.yml    # Job definition (self-contained with inline instructions)
```

</details>

<details>
<summary><strong>Advanced: Nix Flakes (for contributors)</strong></summary>

```bash
# Development environment
nix develop

# Run without installing
nix run github:Unsupervisedcom/deepwork -- --help
```

</details>

---

## License

Business Source License 1.1 (BSL 1.1). Free for non-competing use. Converts to Apache 2.0 on January 14, 2030.

See [LICENSE.md](LICENSE.md) for details.

---

## Feedback

We're iterating fast. [Open an issue](https://github.com/Unsupervisedcom/deepwork/issues) or reach out on Twitter [@tylerwillis](https://twitter.com/tylerwillis).

---

*DeepWork is in active development. Expect rough edges — and rapid improvement.*

---

<sub>Inspired by [GitHub's spec-kit](https://github.com/github/spec-kit)</sub>
