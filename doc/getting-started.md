# Getting Started with DeepWork

DeepWork turns multi-step tasks into reusable commands that AI assistants can run autonomously.

Here's why it's worth the 15 minutes to learn: someone on our team built a 6-step data analysis job — it connects to a production database, runs dozens of SQL queries, validates findings, generates charts, and produces a full report. That job took about 20 minutes to define. Now it runs in ~90 minutes, hands-off, whenever they need it. The kind of analysis that used to take half a day of focused work is now a single command.

That's the value prop. Let's get you there.

---

## Before You Start

**AI assistant:** This guide uses Claude Code (recommended). DeepWork also supports Gemini CLI — swap `--platform claude` for `--platform gemini` in the commands below.

<details>
<summary>Need to install Claude Code?</summary>

```bash
npm install -g @anthropic-ai/claude-code
claude  # starts it, prompts for auth
```

</details>

**Also needed:** Python 3.11+ and a Git repository.

---

## Install DeepWork

```bash
pipx install deepwork
deepwork install --platform claude
```

Or ask Claude to do it: "Install the deepwork package from PyPI and run `deepwork install --platform claude`"

---

## Build Your First Workflow

Let's build a simple job that summarizes meeting notes into action items.

**Step 1: Define the job**

```
/deepwork_jobs.define
```

Claude interviews you. Here's roughly what it looks like:

```
Claude: What task do you want to automate? What's the goal?

You:    Turn my meeting notes into a summary with action items

Claude: What's the input — a file, a link, text you'll paste in?

You:    A markdown file with raw notes

Claude: What should the output be?

You:    A markdown file with a summary and bulleted action items
        with owners

Claude: Are there multiple steps, or is this a single transformation?

You:    Just one step for now

Claude: [Generates the job definition...]
```

This takes about 10 minutes. Answer naturally — Claude helps you refine as you go.

**Step 2: Implement the job**

```
/deepwork_jobs.implement
```

Claude generates instruction files and syncs commands. Then restart Claude (exit and run `claude` again) — Claude only discovers new slash commands on startup.

**Step 3: Run it**

```
/meeting_notes.summarize
```

Claude creates a work branch, executes your workflow, and produces output. When it finishes, you'll have your summary file on the branch.

---

## What You Just Built

After those steps, your project has:

```
.deepwork/jobs/meeting_notes/
├── job.yml              ← your workflow definition
└── steps/
    └── summarize.md     ← instructions for this step

.claude/commands/
└── meeting_notes.summarize.md   ← the slash command Claude discovered
```

The job is now reusable. Each run creates a new Git branch (like `deepwork/meeting_notes-2024-01-15`), keeping your main branch clean. When a job finishes, review the output on the branch and merge if you're happy with it.

---

## What Else Can You Build?

Now that you've built one, here are ideas — from practical to weird:

- **Research a job applicant** — scan their portfolio, find their Twitter/GitHub/writing, summarize their work
- **Prep for a sales call** — research the company, find recent news, identify talking points, draft an agenda
- **Weekly product audit** — run your test suite, summarize failures, draft bug reports, update your status doc
- **Track competitor pricing** — check their pricing pages weekly, update your comparison spreadsheet, flag changes
- **Process customer feedback** — ingest a CSV of NPS comments, categorize by theme, identify top issues, draft response templates
- **Turn meetings into action** — take a transcript, extract action items, assign owners, draft the follow-up email
- **Content pipeline** — research a topic → outline → draft → edit → format for publishing

The pattern: something you do repeatedly, where AI can do the heavy lifting.

**A job takes 10-15 minutes to prototype.** If it doesn't work, throw it away. If it half-works, refine it. The cost of experimentation is low — try weird stuff and see what sticks.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `deepwork: command not found` | `pipx ensurepath`, restart terminal |
| `Must be in a Git repository` | `git init` |
| Commands not showing | Exit and restart Claude |
| Nested repository warning | Move up or out of the nested repo |
| Step taking a long time | Complex jobs take 15-20 min. Kick it off, grab coffee. |

---

## Keep Going

- **Refine it:** `/deepwork_jobs.refine` — tweak steps after running once
- **Add validation:** Define stop hooks to check outputs before a step finishes
- **Create policies:** Auto-trigger instructions when files change — `/deepwork_policy.define`
- **Go deeper:** [doc/architecture.md](architecture.md)
