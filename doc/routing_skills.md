# Routing skills

A routing skill is a single slash command that dispatches to DeepWork workflows
across one or more jobs. It sits between the user and the MCP server, parsing
intent and calling `start_workflow` with the right `job_name` and
`workflow_name`.

Without a routing skill, users invoke workflows verbosely:

```
/deepwork engineer/implement
/deepwork platform_engineer/investigate_incident
```

A routing skill like `/engineering` lets them say:

```
/engineering fix the login bug from issue #42
/engineering set up dashboards for the API
/engineering check repo health
```

## When to create a routing skill

Create one when:

- Multiple jobs share a domain and the user shouldn't need to know which job
  holds the workflow they want.
- A single job has many workflows and intent parsing improves the UX over
  listing them all.
- You want a memorable command (`/business`) rather than the generic
  `/deepwork job/workflow` path.

Do NOT create one when:

- The job has a single workflow — `/deepwork job/workflow` is fine.
- The workflow is only invoked programmatically (nested workflows, sub-agents).

## How to build a routing skill

A routing skill is a standard `SKILL.md` with three responsibilities:

1. **Discover** — call `get_workflows` and filter to the relevant job names.
2. **Match** — parse the user's intent against the filtered workflows.
3. **Dispatch** — call `start_workflow` with the matched `job_name` and
   `workflow_name`.

### Structure

```markdown
---
name: <skill-name>
description: "<one-line description>"
---

# <Title>

<One paragraph explaining what domains this skill covers.>

## Routing table

| Intent pattern | Job | Workflow | When to use |
|----------------|-----|----------|-------------|
| ... | ... | ... | ... |

## How to use

1. Call `get_workflows` to discover available workflows
2. Filter results to jobs: `job_a`, `job_b`, ...
3. Parse the user's intent against the routing table
4. Call `start_workflow` with the matched job_name and workflow_name
5. Follow the standard workflow lifecycle (finished_step, etc.)

## Intent parsing

When the user invokes `/<skill-name>`, parse their intent:
1. **Explicit workflow**: `/<skill-name> <workflow>` — match directly
2. **General request**: `/<skill-name> <request>` — infer best match from
   the routing table and available workflows
3. **No context**: `/<skill-name>` alone — present the routing table and ask
   the user to choose
```

### Key points

- The routing table is guidance for intent matching, not a hard-coded
  dispatch map. The skill should always call `get_workflows` to confirm
  which workflows are actually available — jobs may not be installed.
- A routing skill can span any number of jobs. Group by user mental model
  (what feels like one domain), not by job boundaries.
- Keep the routing table concise. If a job has 14 workflows, group them by
  sub-domain and list the groups, not all 14 rows.
- The skill body should NOT duplicate workflow instructions — those come from
  the MCP server via `start_workflow`.

## Proactive invocation

A routing skill doesn't have to wait for an explicit `/command`. The skill
description in the frontmatter tells the agent when to activate. If the
description says "TRIGGER when: user asks to build a feature, fix a bug, or
add functionality," the agent invokes the skill automatically when it
recognizes that intent — the same way a Claude Code skill with a TRIGGER
clause works.

This is the key difference between a routing skill and a plain workflow
shortcut. The routing skill encodes domain knowledge about *when* to start
a workflow, not just *which* workflow to start.

### Example: spec-driven feature request

The user says:

> Add a WebSocket notification system so users get real-time updates when
> their reports finish processing.

The agent recognizes this is new functionality that needs a spec before
implementation. The `/engineering` skill activates proactively:

1. The skill calls `get_workflows` and finds both `engineer/implement` and
   `spec_driven_development/full` are available.
2. The user's request describes net-new functionality with no existing spec
   or issue — this matches `spec_driven_development/full` (constitution →
   specification → planning → task generation → implementation).
3. The skill calls `start_workflow` with
   `job_name: "spec_driven_development"`, `workflow_name: "full"`.
4. Once the spec workflow completes and produces an implementation plan, the
   agent can start `engineer/implement` to execute the plan with TDD
   discipline.

If instead the user said "fix the login bug from issue #42," the skill would
route to `engineer/implement` directly — the issue already exists and no spec
phase is needed.

## Example: `/engineering`

Routes to the `engineer` and `spec_driven_development` library jobs. The
skill decides whether the user's request needs a spec phase first or can go
straight to implementation.

```markdown
---
name: engineering
description: >-
  Engineering execution: spec-driven development, TDD implementation,
  repo health. TRIGGER when: user asks to build a feature, fix a bug,
  add functionality, or check repo health.
---

# Engineering

Domain-agnostic engineering execution — from spec through PR merge — with
TDD discipline and repo health checks.

## Routing table

| Intent pattern | Job | Workflow | When to use |
|----------------|-----|----------|-------------|
| new feature, new system, design, spec, plan | spec_driven_development | full | Net-new functionality that needs a spec before code |
| implement, build, fix, issue, bug, from issue | engineer | implement | Execute from an existing issue or spec through PR merge |
| doctor, check, health, validate, setup | engineer | doctor | Validate agent.md and domain context files |

## How to use

1. Call `get_workflows` to discover available workflows
2. Filter results to jobs: `engineer`, `spec_driven_development`
3. Parse the user's intent against the routing table
4. Call `start_workflow` with the matched job_name and workflow_name
5. Follow the standard workflow lifecycle

## Intent parsing

When the user invokes `/engineering` (or the skill activates proactively):
1. **Explicit workflow**: `/engineering implement` or `/engineering doctor`
2. **New functionality**: "add a caching layer to the API" → no existing
   issue or spec → route to `spec_driven_development/full`
3. **Existing issue**: "fix the login bug from issue #42" → issue exists
   → route to `engineer/implement`
4. **Repo health**: "check if the repo is ready for engineering workflows"
   → route to `engineer/doctor`
5. **No context**: `/engineering` alone → present the three workflows and ask
```

## Example: `/business`

Routes across three jobs spanning marketing, strategy, and competitive
intelligence. Demonstrates a routing skill that groups many workflows under
sub-domains.

```markdown
---
name: business
description: "Marketing, strategy, and competitive intelligence workflows"
---

# Business

Marketing campaigns, strategic planning, and competitive intelligence —
all from one command.

## Routing table

### Marketing

| Intent pattern | Job | Workflow | When to use |
|----------------|-----|----------|-------------|
| campaign, ads, advertising | marketing | campaign_planning | Strategy through execution |
| content, calendar, editorial | marketing | content_calendar | Content calendar across channels |
| seo, search ranking, organic | marketing | seo_audit | Technical and content SEO audit |
| social, twitter, linkedin, instagram | marketing | social_media_strategy | Platform-specific playbooks |
| email, newsletter, drip | marketing | email_marketing | Campaigns and automations |
| launch, announcement, comms | marketing | launch_comms | Launch communications coordination |
| attribution, analytics, performance | marketing | analytics_attribution | Performance and attribution models |

### Strategy

| Intent pattern | Job | Workflow | When to use |
|----------------|-----|----------|-------------|
| lean canvas, mvp | strategy | lean_canvas | Generate and validate a Lean Canvas |
| working backwards, press release | strategy | working_backwards | Amazon-style press release and FAQ |
| validate, assumptions, evidence | strategy | business_model_validation | Validate assumptions through evidence |
| charter, mission | strategy | charter_mission | Draft charter and mission statement |
| okr, kpi, metrics | strategy | okr_kpi_framework | Define OKRs and KPIs |
| stakeholder, influence, interest | strategy | stakeholder_map | Map stakeholders by influence and interest |
| strategic plan, annual plan, quarterly | strategy | strategic_planning | Quarterly or annual strategic planning |
| board deck, investor update | strategy | board_deck | Board deck or investor update |
| partnership, partner evaluation | strategy | partnership_evaluation | Evaluate partnership opportunities |
| pricing, price model | strategy | pricing_strategy | Analyze and recommend pricing models |

### Competitive intelligence

| Intent pattern | Job | Workflow | When to use |
|----------------|-----|----------|-------------|
| competitive landscape, competitors | competitive_intel | competitive_landscape | Map the competitive landscape |
| swot | competitive_intel | swot_analysis | SWOT analysis |
| market size, tam, sam, som | competitive_intel | market_sizing | TAM, SAM, SOM estimation |
| customer segments, personas | competitive_intel | customer_segmentation | Identify and profile customer segments |
| win loss, deals | competitive_intel | win_loss_analysis | Analyze won and lost deals |
| trends, forecast | competitive_intel | trend_forecast | Identify and project trends |
| brand, positioning | competitive_intel | brand_positioning_audit | Assess brand positioning |

## How to use

1. Call `get_workflows` to discover available workflows
2. Filter results to jobs: `marketing`, `strategy`, `competitive_intel`
3. Parse the user's intent against the routing table sub-domains
4. Call `start_workflow` with the matched job_name and workflow_name
5. Follow the standard workflow lifecycle

## Intent parsing

When the user invokes `/business`, parse their intent:
1. **Explicit workflow**: `/business swot_analysis` → `competitive_intel/swot_analysis`
2. **General request**: `/business I need to plan our Q3 content strategy`
   → infer `marketing/content_calendar`
3. **Ambiguous**: `/business analyze our market position` → could be
   `competitive_intel/competitive_landscape` or
   `competitive_intel/brand_positioning_audit` — ask the user to clarify
4. **No context**: `/business` alone → show the three sub-domains and ask
```
