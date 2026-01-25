# Teach Claude to Automate *Anything*

Triage email, give feedback to your team, make tutorials/documentation, QA your product every day, do competitive research... *anything*.

## Install
```bash
brew tap unsupervisedcom/deepwork && brew install deepwork
```

Then in your project folder:
```bash
deepwork install
```
See below for additional installation options

DeepWork is an open-source plugin for Claude Code (and other CLI agents). It:
- teaches Claude to follow strict workflows
- makes it easy for you to define them 
- learns and updates automatically

---

## What You Get

This skill took less than 30 minutes to build and uses a browser to deeply explore our product, documents the findings, and produces user-facing documentation about each part of the product. It runs on its own, produces thousands of words of analysis that is turned into user-friendly analysis. It runs for me weekly to capture any updates or changes.

**Example: Competitive research in 45 minutes**

```
/competitive_research
```

Output:

```
deepwork-output/competitive_research/
├── competitors.md           # Who they are, what they do
├── competitor_profiles/     # Deep dive on each
├── primary_research.md      # What they say about themselves
└── strategic_overview.md    # Your positioning recommendations
```

Build the skill once. Run it whenever you need it.

---

## Who This Is For

**If you can use Claude Code and describe a process, you can automate it.**

| You | What You'd Automate |
|-----|---------------------|
| **Solo founder** | Competitive research, meeting prep, investor updates |
| **Indie hacker** | Daily briefs, SEO analysis, git summaries |
| **PM / Ops** | Tutorial writing, quarterly audits, process docs |
| **Power user** | Multi-agent orchestration, overnight coding runs |

We call it **vibe automation**: describe what you want, let it run, iterate on what works.

---

## Quick Start

### 1. Install

```bash
brew tap unsupervisedcom/deepwork
brew install deepwork
```

Then in any project folder:

```bash
deepwork install
```

**After install, exit Claude and restart.** Then verify you see these commands:
- `/deepwork`
- `/deepwork_jobs.define`
- `/deepwork_jobs.implement`

### 2. Define Your First Workflow

Start simple—something you do manually in 15-30 minutes.

```
/deepwork_jobs.define "write a tutorial for how to [your process]"
```

DeepWork asks questions, then writes the steps. You're creating a **reusable skill**—this setup is one-time.

### 3. Run It

```
/tutorial_writer.discover
/tutorial_writer.draft
/tutorial_writer.polish
```

Each step produces an output. Quality checks happen automatically.

---

## What People Are Building

| Workflow | What It Does |
|----------|--------------|
| **Email triage** | Scan inbox, categorize, archive—following YOUR rules |
| **Competitive research** | Track competitors weekly, generate diff reports |
| **Tutorial writer** | Turn your expertise into docs |
| **SaaS user audit** | Quarterly audit of who has access to what |
| **Meeting prep** | Research attendees before calls |

---

## How It Works

**1. Strict workflows** — Claude follows step-by-step instructions with quality checks. No more going off-script.

**2. Easy to define and refine** — Describe what you want in plain English. DeepWork writes the steps.

```
/deepwork_jobs.define "weekly competitive research on my top 5 competitors"
```

**3. Learns automatically** — Run `/deepwork_jobs.learn` after any job to capture what worked and improve for next time.

All work happens on Git branches. Every change is tracked.

---

## Supported Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| **Claude Code** | Full Support | Recommended. Quality hooks, rules, best DX. |
| **Gemini CLI** | Full Support | TOML format, global hooks only |
| OpenCode | Planned | |
| GitHub Copilot CLI | Planned | |

**Tip:** Use the terminal (Claude Code CLI), not the VS Code extension. The terminal has full feature support.

---

## Browser Automation

For workflows that need to interact with websites, DeepWork works with [Claude in Chrome](https://www.anthropic.com/claude-in-chrome).

**⚠️ Safety note:** Browser automation can modify your system. We recommend using a dedicated Chrome profile for automation. See [Browser Automation Safety](docs/browser-automation-safety.md).

---

## Troubleshooting

### Commands don't appear after install

Exit Claude completely and restart. Commands load on startup.

### Python version errors

DeepWork requires Python 3.11+. Check your version:

```bash
python --version
```

### Stop hooks firing unexpectedly

This is a known issue we're fixing. For now, if stop hooks fire when they shouldn't, exit and restart Claude.

### Claude "just does the task" instead of using DeepWork

If Claude bypasses the workflow, explicitly run the step command:

```
/your_job.step_name
```

Don't say "just do it" or "can you do X"—run the slash command directly.

---

## Documentation

- **[Architecture](doc/architecture.md)** — How DeepWork works under the hood
- **[Doc Specs](doc/doc-specs.md)** — Quality criteria for document outputs
- **[Contributing](CONTRIBUTING.md)** — Development setup and guidelines

---

## Example Job Definition

Here's what a job looks like under the hood:

```yaml
name: tutorial_writer
version: "1.0.0"
summary: "Create tutorials from your domain expertise"

steps:
  - id: discover
    name: "Discover & Outline"
    description: "Interview user, create outline"
    inputs:
      - name: topic
        description: "What to document"
    outputs:
      - deepwork-output/tutorial_writer/outline.md

  - id: draft
    name: "Write Tutorial"
    inputs:
      - file: deepwork-output/tutorial_writer/outline.md
        from_step: discover
    outputs:
      - deepwork-output/tutorial_writer/tutorial.md
    dependencies:
      - discover

  - id: polish
    name: "Polish & Export"
    inputs:
      - file: deepwork-output/tutorial_writer/tutorial.md
        from_step: draft
    outputs:
      - deepwork-output/tutorial_writer/final/[topic].md
    dependencies:
      - draft
```

You don't need to write this by hand—`/deepwork_jobs.define` creates it from your description.

---

<details>
<summary><strong>Advanced: Directory Structure</strong></summary>

```
your-project/
├── .deepwork/
│   ├── config.yml          # Platform configuration
│   ├── rules/              # Automated rules
│   └── jobs/               # Job definitions
│       └── job_name/
│           ├── job.yml     # Job metadata
│           └── steps/      # Step instructions
├── .claude/                # Generated Claude skills
│   └── commands/
└── deepwork-output/        # Job outputs (gitignored)
```

</details>

<details>
<summary><strong>Alternative Installation Methods</strong></summary>

Homebrew is recommended, but you can also use:

```bash
# pipx (isolated environment)
pipx install deepwork

# uv
uv tool install deepwork

# pip
pip install deepwork
```

Then in your project:

```bash
deepwork install --platform claude
# or: deepwork install --platform gemini
```

</details>

<details>
<summary><strong>Advanced: Automated Rules</strong></summary>

Rules monitor file changes and prompt Claude to follow guidelines:

```markdown
---
name: Source/Test Pairing
set:
  - src/{path}.py
  - tests/{path}_test.py
---
When source files change, corresponding test files should also change.
```

See [Architecture](doc/architecture.md) for full rules documentation.

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
