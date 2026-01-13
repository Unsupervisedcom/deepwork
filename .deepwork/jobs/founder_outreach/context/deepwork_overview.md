# DeepWork Overview

Use this context when creating outreach materials. This is what DeepWork is and does.

## One-Sentence Description

DeepWork transforms complex multi-step tasks into reusable slash commands for AI coding assistants.

## How It Works

1. **Define a workflow once** - Create a `job.yml` that describes the steps, inputs, and outputs
2. **DeepWork generates slash commands** - Each step becomes a command like `/competitive_research.identify_competitors`
3. **Execute via your AI assistant** - Run commands in Claude Code, Gemini CLI, or other supported platforms
4. **All outputs are Git-native** - Work happens on branches like `deepwork/job-name-instance-date`, everything is versioned and reviewable

## Key Value Propositions

**For Small Teams (< 20 people)**
- "Build lightweight processes without scaling headcount"
- "A 5-person team operating with the process rigor of a 50-person team"
- "Can't afford to hire for process, can't afford to half-ass it either"

**For AI-Native / Technical Founders**
- "You're building AI for customers—are you using AI systematically internally?"
- "Stop re-explaining multi-step workflows to your AI"
- "Define once, execute forever via slash commands"

**For Anyone Doing Repetitive Complex Work**
- "Every time you need your AI to do something complex, you have to re-explain the entire process. DeepWork solves this."
- "Build institutional knowledge into your AI workflows"

## Real Use Cases We're Running

1. **Marketing materials with built-in accuracy checks** - Generate content, then automated validation step checks for accuracy
2. **DevOps process automation** - Deployment workflows, monitoring setup, incident response
3. **Bug discovery → code agent pipeline** - Find bugs, automatically kick off agent to fix them
4. **Founder outreach** (this job!) - Research company → analyze fit → generate personalized email/SMS/demo

## High-Potential Workflows for Startups

| Category | Examples | Frequency |
|----------|----------|-----------|
| **Research** | Competitive intel, market research, customer research | Quarterly |
| **Reporting** | Investor updates, board decks, metrics dashboards | Weekly/Monthly |
| **Content** | Marketing materials, sales collateral, case studies | Ongoing |
| **Ops** | New hire onboarding, compliance evidence gathering | Per event |
| **DevOps** | Deployment, monitoring, cloud cost management | Daily/Weekly |
| **Sales** | Lead research, proposal generation, pipeline reporting | Daily |
| **Ad Ops** | Get reports → suggest changes → execute | Daily |

## What Makes a Workflow "DeepWork-able"

Good fit:
- **Multi-step** (3-7 steps is ideal)
- **Repeatable** (done more than once)
- **Has clear inputs/outputs** (files, reports, decisions)
- **Benefits from consistency** (same quality every time)
- **Currently manual or inconsistent** (no one owns it, or founder does it ad-hoc)

Bad fit:
- One-off tasks
- Highly creative work with no structure
- Tasks requiring real-time human judgment at every step
- Simple tasks that don't need a workflow

## Example Workflow Structure

Here's what a good DeepWork workflow looks like:

**`/competitive_intel` (4 steps)**

| Step | Command | What it does | Output |
|------|---------|--------------|--------|
| 1 | `/competitive_intel.identify` | Research competitors in the space | `competitors.md` |
| 2 | `/competitive_intel.deep_dive` | Analyze each competitor's features, pricing, positioning | `competitor_profiles/` |
| 3 | `/competitive_intel.matrix` | Build comparison matrix | `comparison_matrix.md` |
| 4 | `/competitive_intel.briefing` | Generate exec summary + talking points | `competitive_briefing.md` |

**What makes this demo work:**
- Universally relatable (every founder does competitive research)
- Immediately useful (they walk away with real output)
- Shows the "aha" moment (define once → slash commands → Git-native)
- Appropriate length (20 min demo, 4 steps)

## Target Audience

Primary: **Founders who are power users of Claude Code or OpenCode**
- Technical enough to appreciate the architecture
- Already using AI for complex work
- Feel the pain of re-explaining workflows
- Small team, wearing many hats

Secondary: **Technical teams at startups**
- Engineers who want to systematize processes
- Ops people looking for automation without complexity
