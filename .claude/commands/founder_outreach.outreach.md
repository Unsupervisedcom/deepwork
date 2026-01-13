---
description: Create personalized email, SMS options, and a custom demo idea tailored to the target company
---

# founder_outreach.outreach

**Step 3 of 3** in the **founder_outreach** workflow

**Summary**: Generate personalized DeepWork outreach for target founders

## Job Overview

A workflow for creating compelling, personalized outreach to convince founders
to try DeepWork. This job researches a target company, analyzes where DeepWork
would fit their workflows, and generates customized email, SMS, and demo ideas.

The workflow produces:
- Comprehensive company research summary
- Analysis of DeepWork fit and relevant workflows
- Personalized email, SMS options, and a custom demo concept

Designed for founder-to-founder outreach where the target is likely a power user
of AI coding tools like Claude Code or OpenCode.


## Prerequisites

This step requires completion of the following step(s):
- `/founder_outreach.research`
- `/founder_outreach.analyze`

Please ensure these steps have been completed before proceeding.

## Instructions

# Generate Outreach Assets

## Objective
Create personalized outreach assets (email, SMS, and demo idea) that will convince the target founder to try DeepWork.

## Prerequisites
This step requires:
- `company_research.md` from the research step
- `deepwork_fit_analysis.md` from the analyze step

Read both files before generating outreach. The analysis file contains the positioning strategy and demo recommendation you should use.

## What is DeepWork? (For Writing Outreach)

**One-sentence**: DeepWork transforms complex multi-step tasks into reusable slash commands for AI coding assistants.

**Slightly longer**: Every time you need your AI assistant to do something complex, you have to re-explain the entire process. DeepWork lets you define workflows once, then execute them with simple slash commands like `/competitive_research.identify_competitors`. All outputs go to Git branches, versioned and reviewable.

**How to explain it casually**: "You know how you have to re-explain multi-step processes to Claude Code every time? This lets you define them once, then just run /workflow_name and it knows exactly what to do."

## Tone Guidelines by Relationship

**For Friends**
- Super casual, skip formalities
- "Hey, built something you'd get..."
- "Dude I need to show you this thing"
- Reference shared context, inside jokes if relevant
- Direct ask, no pitch-speak

**For Warm Intros**
- Friendly but slightly more structured
- Acknowledge the connection briefly
- Still personal, not salesy
- "So-and-so mentioned you're deep into Claude Code..."

**For Cold Outreach**
- Lead with specific insight about their company (show homework)
- Respect their time
- Clear, low-commitment ask
- No "I hope this email finds you well"

## Email Guidelines

**Structure:**
1. **Hook** (1 sentence): Why you thought of them specifically
2. **What it is** (1-2 sentences): DeepWork explanation
3. **Why them** (2-3 sentences): Connect to their situation—team size, what they're building, specific workflows
4. **Social proof** (optional, 1 sentence): What you're using it for
5. **Ask** (1 sentence): Clear, low-commitment (20 min demo)

**Rules:**
- Under 200 words
- No fluff, no "hope this finds you well"
- Sound like a human, not a sales email
- Reference specific things about their company
- Match tone to relationship

**Example email (for a friend):**

> Hey Alex,
>
> Been thinking about you guys since you're basically the perfect test case for something we've been building.
>
> You know how you're building Joy to automate the wholesale journey for your customers? We built something similar but for internal workflows using Claude Code. It's called DeepWork—you define a multi-step process once (competitive research, investor updates, whatever), and it auto-generates slash commands that Claude Code can execute consistently every time.
>
> The thing that made me think of Overjoy: you're 5 people building an AI product. You probably have a ton of repetitive internal processes that you can't afford to hire for but also can't afford to half-ass.
>
> Would you be down for a 20-min demo? I could set up a workflow specific to Overjoy and show you how it works end-to-end.
>
> [Name]

## SMS Guidelines

Provide 3 options with different angles:

1. **Direct**: State what it is + ask (most straightforward)
2. **Hook first**: Question or observation that creates curiosity, then ask
3. **Ultra casual**: Minimum words, maximum intrigue (for close friends)

**Rules:**
- Aim for under 160 characters when possible (SMS length)
- Sound like a text, not a marketing message
- Easy to say "yes" to
- Match casualness to relationship

**Example SMS options:**

> **Direct**: "Hey—built a thing that lets you define workflows once and Claude Code executes them via slash commands. You're 5 ppl building AI, feels like you'd get it. 20 min demo?"

> **Hook first**: "Random q: how much time do you spend re-explaining processes to Claude Code? Built something that fixes that. Would love to show you"

> **Ultra casual**: "Dude I need to show you this thing we built. It's like templates for AI workflows. 20 min this week?"

## Demo Idea Guidelines

Use the demo recommendation from `deepwork_fit_analysis.md` but flesh it out with:

1. **The hook**: One sentence on why this demo specifically
2. **Workflow table**: Steps with commands and outputs
3. **Demo flow**: Minute-by-minute breakdown (20 min total)
4. **Why it works**: Bullet points specific to this founder
5. **Alternatives**: 1-2 backup demo ideas

**What makes a compelling demo:**
- **Universally relatable**: They definitely do this workflow
- **Immediately useful**: They walk away with real output they can use
- **Shows the "aha"**: Define once → slash commands → Git branches
- **Right length**: 3-5 steps, fits in 20 minutes
- **Specific**: Tied to their business, not generic

**Example demo structure:**

| Step | Command | What it does | Output |
|------|---------|--------------|--------|
| 1 | `/competitive_intel.identify` | Research competitors | `competitors.md` |
| 2 | `/competitive_intel.deep_dive` | Analyze each competitor | `competitor_profiles/` |
| 3 | `/competitive_intel.matrix` | Build comparison | `comparison_matrix.md` |
| 4 | `/competitive_intel.briefing` | Generate exec summary | `briefing.md` |

**Demo flow (20 min):**
- (2 min) Show `job.yml` - "this is how you define a workflow"
- (3 min) Run step 1 live - watch Claude research
- (5 min) Show outputs on Git branch - "everything versioned"
- (5 min) Run step 2 - show it reads previous outputs
- (5 min) Show final output - "this is what you get"

## Output Format

Create `outreach_assets.md` with this structure:

```markdown
# Outreach Assets: [Company Name]

**Target**: [Contact Name], [Title]
**Company**: [Company Name]
**Relationship**: [Friend/Warm/Cold]
**Generated**: [Date]

---

## Email

**Subject**: [Subject line - short, personal, not salesy]

[Email body - under 200 words, follows structure above]

---

## SMS Options

**Option 1 (Direct)**:
[Text - ideally under 160 chars]

**Option 2 (Hook first)**:
[Text]

**Option 3 (Ultra casual)**:
[Text]

---

## Demo Idea: [Workflow Name]

### The Hook
[One sentence on why this demo resonates for this specific company/founder]

### Workflow: `/[command_name]` ([N] steps)

| Step | Command | What it does | Output |
|------|---------|--------------|--------|
| 1 | `/[job].[step]` | [Description] | `[file.md]` |
| 2 | `/[job].[step]` | [Description] | `[file.md]` |
| 3 | `/[job].[step]` | [Description] | `[file.md]` |
| 4 | `/[job].[step]` | [Description] | `[file.md]` |

### Demo Flow (20 min)

1. **(2 min)** [What to show/say]
2. **(3 min)** [What to show/say]
3. **(5 min)** [What to show/say]
4. **(5 min)** [What to show/say]
5. **(5 min)** [What to show/say]

### Why This Demo Works for [Contact Name]
- [Specific reason 1]
- [Specific reason 2]
- [Specific reason 3]

### Alternative Demo Options
1. **[Alternative workflow name]**: [Brief description and why it could work]
2. **[Alternative workflow name]**: [Brief description and why it could work]

---

## Follow-up Notes
[Any context for timing, approach, or things to mention in conversation]
```

## Quality Checklist
- [ ] Email is under 200 words and sounds human (not salesy)
- [ ] Email references specific things about their company
- [ ] Tone matches the relationship (friend vs. warm vs. cold)
- [ ] SMS options are distinct angles, not just rewording
- [ ] Demo workflow is specific to their business
- [ ] Demo has concrete steps with realistic outputs
- [ ] Demo flow fits in 20 minutes
- [ ] "Why this works" bullets are specific to this founder


## Inputs


### Required Files

This step requires the following files from previous steps:
- `company_research.md` (from step `research`)
- `deepwork_fit_analysis.md` (from step `analyze`)

Make sure to read and use these files as context for this step.

## Work Branch Management

All work for this job should be done on a dedicated work branch:

1. **Check current branch**:
   - If already on a work branch for this job (format: `deepwork/founder_outreach-[instance]-[date]`), continue using it
   - If on main/master, create a new work branch

2. **Create work branch** (if needed):
   ```bash
   git checkout -b deepwork/founder_outreach-[instance]-$(date +%Y%m%d)
   ```
   Replace `[instance]` with a descriptive identifier (e.g., `acme`, `q1-launch`, etc.)

## Output Requirements

Create the following output(s):
- `outreach_assets.md`
Ensure all outputs are:
- Well-formatted and complete
- Ready for review or use by subsequent steps

## Completion

After completing this step:

1. **Verify outputs**: Confirm all required files have been created

2. **Inform the user**:
   - Step 3 of 3 is complete
   - Outputs created: outreach_assets.md
   - This is the final step - the job is complete!

## Workflow Complete

This is the final step in the founder_outreach workflow. All outputs should now be complete and ready for review.

Consider:
- Reviewing all work products
- Creating a pull request to merge the work branch
- Documenting any insights or learnings

---

## Context Files

- Job definition: `.deepwork/jobs/founder_outreach/job.yml`
- Step instructions: `.deepwork/jobs/founder_outreach/steps/outreach.md`