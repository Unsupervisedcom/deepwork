# Teach Claude to Automate *Anything*

Triage email, give feedback to your team, make tutorials/documentation, QA your product every day, do competitive research... *anything*.

## Install
```bash
brew tap unsupervisedcom/deepwork && brew install deepwork
```

Then in your project folder (must be a Git repository):
```bash
deepwork install
claude
```

> **Note:** DeepWork requires a Git repository. If your folder isn't already a repo, run `git init` first.

Now inside claude, define your first job using the `/deepwork_jobs` command. Ex.
```
/deepwork_jobs Make a job for doing competitive research. It will take the URL of the competitor as an input, and should make report including a SWOT analysis for that competitor.
```

See below for additional installation options

DeepWork is an open-source plugin for Claude Code (and other CLI agents). It:
- teaches Claude to follow strict workflows consistently
- makes it easy for you to define them 
- learns and updates automatically

## Example

You can make a DeepWork job that uses Claude Code to automatically run a deep competitive research workflow. To do this you:
- Run `/deepwork_jobs` in Claude Code and select `define`
- Explain your process _e.g. "Go look at my company's website and social channels to capture any new developments, look at our existing list of competitors, do broad web searches to identify any new competitiors, and then do deep research on each competitor and produce a comprehensive set of md reports including a summary report for me._

Deepwork will ask you questions to improve the plan and make a hardened automation workflow. This usually takes ~10 minutes. 

When this is done, it will create a .yml file that details the plan and then will use templates to document how Claude should execute each individual step in the workflow. This usually takes 2-5 minutes.

After that, it will create a new skill for you in Claude, something like `/competitive_research` that you can run at any time (or automate). 

Running that `/competitive_research` command will get you output that looks something like this:
```
deepwork-output/competitive_research/
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

### 1. Install

```bash
brew tap unsupervisedcom/deepwork
brew install deepwork
```

Then in any project folder (must be a Git repository):

```bash
deepwork install
```

> **Note:** If your folder isn't a Git repo yet, run `git init` first.

**After install, load Claude.** Then verify you see this command: `/deepwork_jobs`

### 2. Define Your First Workflow

Start simple—something you do manually in 15-30 minutes. Here's an example:

```
/deepwork_jobs write a tutorial for how to use a new feature we just launched
```

DeepWork asks you questions (this usually takes about 10 minutes) then writes the steps. You're creating a **reusable skill** — after you do this process you can run that skill any time you want without repeating this process.

### 3. Run It

Once the skill is created, type the name of your job (e.g. `/tutorial`) in Claude and you'll see the skill show up in your suggestions (e.g. `/tutorial_writer`).

Hit enter to run the skill. Claude will follow the workflow step by step. 

## Some Examples of What Other People Are Building with DeepWork
=======
To start the process, just run:

```
/deepwork_jobs
```

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
/deepwork_jobs
```

**3. Learns automatically** — Run `/deepwork_jobs.learn` (or ask claude to `run the deepwork learn job`) after any job to automatically capture what worked and improve for next time.

**4. All work happens on Git branches** — Every change can be version-controlled and tracked. You can roll-back to prior versions of the skill or keep skills in-sync and up-to-date across your team.

---

## Supported Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| **Claude Code** | Full Support | Recommended. Quality hooks, best DX. |
| **Gemini CLI** | Partial Support | TOML format, global hooks only |
| OpenCode | Planned | |
| GitHub Copilot CLI | Planned | |
| Others | Planned | We are nailing Claude and Gemini first, then adding others according ot demand |

**Tip:** Use the terminal (Claude Code CLI), not the VS Code extension. The terminal has full feature support.

---

## Browser Automation

For workflows that need to interact with websites, you can use any browser automation tool that works in Claude Code. We generally recommend [Claude in Chrome](https://www.anthropic.com/claude-in-chrome).

**⚠️ Safety note:** Browser automation is still something models can be hit-or-miss on. We recommend using a dedicated Chrome profile for automation.

---

## Troubleshooting

Here are some known issues that affect some early users — we're working on improving normal performance on these, but here are some known workarounds.

### Slash Commands don't appear after install

Exit Claude completely and restart.

### Stop hooks firing unexpectedly

Occasionally, especially after updating a job or running the `deepwork_jobs learn` process after completing a task, Claude will get confused about which workflow it's running checks for. For now, if stop hooks fire when they shouldn't, you can either:
- Ask claude `do we need to address any of these stop hooks or can we ignore them for now?` 
- Ignore the stop hooks and keep going until the workflow steps are complete
- Run the `/clear` command to start a new context window (you'll have to re-run the job after this)

### Claude "just does the task" instead of using DeepWork

If Claude attempts to bypass the workflow and do the task on it's own, tell it explicitly to use the skill. You can also manually run the step command:
```
/your_job
```

Tip: Don't say things like "can you do X" while in **defining** a new `/deepwork_jobs` — Claude has a bias towards action and workarounds and may abandon the skill creation workflow and attempt to do your task as a one off. Instead, say something like "create a workflow that..."

### If you can't solve your issues using the above and need help

Send [@tylerwillis](https://x.com/tylerwillis) a message on X.

---

<details>
<summary><strong>Advanced: Directory Structure</strong></summary>

```
your-project/
├── .deepwork/
│   ├── config.yml          # Platform configuration
│   └── jobs/               # Job definitions
│       └── job_name/
│           ├── job.yml     # Job metadata
│           └── steps/      # Step instructions
├── .claude/                # Generated Claude skills
│   └── skills/
└── deepwork-output/        # Job outputs (gitignored)
```

</details>

<details>
<summary><strong>Alternative Installation Methods</strong></summary>

**Prerequisites** (for non-Homebrew installs): Python 3.11+, Git

Homebrew is recommended, but you can also use:

```bash
# uv (Recommended)
uv tool install deepwork

# pipx
pipx install deepwork

# pip
pip install deepwork
```

Then in your project folder (in terminal, not in Claude Code):

```bash
deepwork install
```

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

**Code Coverage**: 78.99% (as of 2026-02-09)
