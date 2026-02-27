# Teach Claude to Automate *Anything*

Triage email, give feedback to your team, make tutorials/documentation, QA your product every day, do competitive research... *anything*.

## Install

To install in Claude Code, run:
```
/plugin marketplace add https://github.com/Unsupervisedcom/deepwork
/plugin install deepwork@deepwork-plugins
```

Then start a new session and define your first job:
```
/deepwork Make a job for doing competitive research. It will take the URL of the competitor as an input, and should make report including a SWOT analysis for that competitor.
```

To install in Claude Desktop:

In Cowork mode, select 'Customize with plugins' at the bottom of the page.

Select Personal, click the +, and select 'Add marketplace from GitHub' 

Set the URL to ```Unsupervisedcom/deepwork``` and press Sync. (adding a marketplace currently fails on Windows)

Select the deepwork plugin and click Install.

In Cowork mode, select 'Start a deepwork workflow'


> **Note:** DeepWork stores job definitions in `.deepwork/jobs/` and creates work branches in Git. Your project folder should be a Git repository. If it isn't, run `git init` first.

DeepWork is an open-source plugin for Claude Code (and other CLI agents). It:
- teaches Claude to follow strict workflows consistently
- makes it easy for you to define them
- learns and updates automatically

## Example

You can make a DeepWork job that uses Claude Code to automatically run a deep competitive research workflow. To do this you:
- Run `/deepwork` in Claude Code
- Explain your process _e.g. "Go look at my company's website and social channels to capture any new developments, look at our existing list of competitors, do broad web searches to identify any new competitiors, and then do deep research on each competitor and produce a comprehensive set of md reports including a summary report for me._

Deepwork will ask you questions to improve the plan and make a hardened automation workflow. This usually takes ~10 minutes.

When this is done, it will create a .yml file that details the plan and then will document how Claude should execute each individual step in the workflow. This usually takes 2-5 minutes.

After that, you can run the workflow at any time:

Running that `/deepwork competitive_research` command will get you output that looks something like this:
```
# On your work branch (deepwork/competitive_research-acme-2026-02-21):
competitive_research/
├── competitors.md           # Who they are, what they do
├── competitor_profiles/     # Deep dive on each
├── primary_research.md      # What they say about themselves
└── strategic_overview.md    # Your positioning recommendations
```

You only have to build a skill once. Then: run it whenever you need it.

_Note: all of these skills are composable. You can call skills inside of other jobs. As an example, you could create a `make_comparison_document` skill and call it at the end of the `/competitive_research` skill — automating the process of going from research to having final breifings and materials on competitiors for your sales team._

---

## Who This Is For

**If you can use Claude Code and describe a process, you can automate it.**

| You | What You'd Automate |
|-----|---------------------|
| **Founders** | Competitive research, automatically discover bugs/issues and open tickets, reports or investor updates pulling from multiple sources |
| **Ops** | Daily briefs, SEO analysis, git summaries |
| **Product Managers** | Tutorial writing, QA reports, simulated user testing, updating process docs or sales materials |
| **Engineers** | Automate standup summary, git summaries, reports |
| **Data/Analytics** | Pull data from multiple sources, ETL, create custom reports and dashboards |

One user used DeepWork to automatically research email performance across hundreds of millions of marketing emails. It accessed data from a data warehouse, came up with research questions, queried to answer those questions, and then produced a several page, comprehensive report. The process ran autonomously for ~90 minutes and produced a report better than internal dashboards that had been refined for months.

DeepWork is a free, open-source tool — if you're already paying for a Claude Max subscription, each of these automations costs you nothing additional.

Similar to how vibe coding makes easier for anyone to produce software, this is **vibe automation**: describe what you want, let it run, and then iterate on what works.

---

## Quick Start

### 1. Install the Plugin

In Claude Code:
```
/plugin marketplace add https://github.com/Unsupervisedcom/deepwork
/plugin install deepwork@deepwork-plugins
```

Start a new Claude Code session after installing.

> **Note:** If your folder isn't a Git repo yet, run `git init` first.

### 2. Define Your First Workflow

Start simple—something you do manually in 15-30 minutes. Here's an example:

```
/deepwork write a tutorial for how to use a new feature we just launched
```

DeepWork asks you questions (this usually takes about 10 minutes) then writes the steps. You're creating a **reusable skill** — after you do this process you can run that skill any time you want without repeating this process.

### 3. Run It

Once the skill is created, invoke it via `/deepwork`:

```
/deepwork tutorial_writer
```

Claude will follow the workflow step by step.

## Some Examples of What Other People Are Building with DeepWork

| Workflow | What It Does | Why it matters|
|----------|--------------|--------------|
| **Email triage** | Scan inbox, categorize, archive, and draft replies | Save time processing email |
| **Competitive research** | Track competitors weekly, generate diff reports | Fast feedback on how your competition is changing |
| **Tutorial writer** | Turn your expertise into docs | Rapidly build docs, guides, etc. |
| **SaaS user audit** | Quarterly audit of who has access to various services | Save money on forgotten SaaS licenses |

---

## Why It Works Well

**1. Strict workflows** — Claude follows step-by-step instructions with quality checks. No more going off-script.

**2. Easy to define** — Describe what you want in plain English. DeepWork knows how to ask you the right questions to refine your plan.
```
/deepwork
```

**3. Learns automatically** — Run `/deepwork deepwork_jobs learn` after any job to automatically capture what worked and improve for next time.

**4. All work happens on Git branches** — Every change can be version-controlled and tracked. You can roll-back to prior versions of the skill or keep skills in-sync and up-to-date across your team.

**5. Automated change review** — Define `.deepreview` config files to set up review rules (patterns, strategies, instructions). Run `deepwork review --instructions-for claude` to generate parallel review tasks for your changed files. Works wonderfully for code reviews, but can review non-code files as well.

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

### Stop hooks firing unexpectedly

Occasionally, especially after updating a job or running the `deepwork_jobs learn` process after completing a task, Claude will get confused about which workflow it's running checks for. For now, if stop hooks fire when they shouldn't, you can either:
- Ask claude `do we need to address any of these stop hooks or can we ignore them for now?`
- Ignore the stop hooks and keep going until the workflow steps are complete
- Run the `/clear` command to start a new context window (you'll have to re-run the job after this)

### Claude "just does the task" instead of using DeepWork

If Claude attempts to bypass the workflow and do the task on it's own, tell it explicitly to use the skill. You can also manually run the step command:
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
│           ├── job.yml    # Job metadata
│           └── steps/     # Step instructions
```

</details>

<details>
<summary><strong>Alternative Installation Methods</strong></summary>

**Prerequisites** (for non-plugin installs): Python 3.11+, Git

If you prefer to install the `deepwork` CLI directly (for running the MCP server manually):

```bash
# Homebrew
brew tap unsupervisedcom/deepwork && brew install deepwork

# uv
uv tool install deepwork

# pipx
pipx install deepwork

# pip
pip install deepwork
```

Then configure your AI agent CLI to use `deepwork serve` as an MCP server.

</details>

<details>
<summary><strong>Advanced: Nix Flakes</strong></summary>

```bash
# Development environment
nix develop

# Install from flake
nix profile install github:Unsupervisedcom/deepwork

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

*DeepWork is in active development. Expect rough edges—and rapid improvement.*

---

<sub>Inspired by [GitHub's spec-kit](https://github.com/github/spec-kit)</sub>
