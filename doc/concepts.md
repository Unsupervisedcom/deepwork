# Core Concepts

DeepWork automates multi-step workflows by decomposing complex tasks into reviewable steps. Three concepts form the mental model: **Jobs**, **Steps**, and **Workflows**.

```
Job (e.g., "research")
├── Steps: [gather_sources, deep_research, synthesize, check_citations, write_report]
└── Workflows:
    ├── "deep"  → [gather_sources, deep_research, synthesize, check_citations, write_report]
    └── "quick" → [gather_sources, synthesize, write_report]
```

```mermaid
graph LR
    JOB["research"] --> DR["deep workflow"]
    JOB --> Q["quick workflow"]
    DR --> G1["gather_sources"] --> D["deep_research"] --> S1["synthesize"] --> C1["check_citations"] --> W1["write_report"]
    Q --> G2["gather_sources"] --> S2["synthesize"] --> W2["write_report"]
```

Outputs from one step become inputs to the next. This is how data flows through the `deep` workflow:

```mermaid
graph LR
    G["gather_sources"] -- "sources.md" --> D["deep_research"]
    D -- "findings.md" --> S["synthesize"]
    S -- "draft_report.md" --> C["check_citations"]
    C -- "citation_report.md" --> W["write_report"]
```

A **Job** defines a pool of **Steps** and one or more **Workflows** — named paths through those steps. Different workflows reuse the same steps in different combinations. The `deep` workflow runs every step including citation checking; `quick` skips the deep research and citation check to go straight from sources to synthesis.

## Jobs

A job is the top-level container. It lives in `.deepwork/jobs/<name>/job.yml` and defines everything needed to execute a task: the steps, the workflows, and shared context.

```yaml
name: fruits
version: "1.0.0"
summary: "Identify and classify fruits from a mixed list of items"
common_job_info_provided_to_all_steps_at_runtime: |
  A simple, deterministic job for CI testing of the DeepWork framework.
```

Key fields:

- **name** — Unique identifier for the job
- **summary** — What the job does
- **common_job_info_provided_to_all_steps_at_runtime** — Shared context injected into every step so the AI agent understands the broader goal
- **steps** — The atomic units of work (see below)
- **workflows** — Named execution paths through steps (see below)

## Steps

A step is the atomic unit of work. Each step has instructions (a markdown file), defined inputs, defined outputs, and optional quality reviews.

```yaml
steps:
  - id: gather_sources
    name: "Gather Sources"
    description: "Find and collect relevant sources for the research topic"
    instructions_file: steps/gather_sources.md
    inputs:
      - name: research_topic
        description: "The topic to research"
      - name: max_sources
        description: "Maximum number of sources to collect"
    outputs:
      sources.md:
        type: file
        description: "Curated list of sources with URLs and summaries"
        required: true
    dependencies: []
    reviews: []

  - id: deep_research
    name: "Deep Research"
    description: "Analyze gathered sources in depth"
    instructions_file: steps/deep_research.md
    inputs:
      - file: sources.md
        from_step: gather_sources
    outputs:
      findings.md:
        type: file
        description: "Detailed findings from source analysis"
        required: true
    dependencies:
      - gather_sources
    reviews: []
```

### Inputs

Inputs can come from two sources:

- **User-provided** — The user supplies a value when the step runs (`name:` + `description:`)
- **From a prior step** — A file produced by an earlier step (`file:` + `from_step:`)

```yaml
inputs:
  - name: research_topic             # user provides this
    description: "The topic to research"
  - file: sources.md                 # comes from a prior step's output
    from_step: gather_sources
```

### Outputs

Outputs are files that the step produces. They become available as inputs to later steps via `file:` + `from_step:`. This is how data flows through a workflow.

```yaml
outputs:
  findings.md:
    type: file
    description: "Detailed findings from source analysis"
    required: true
```

Output types:
- **`file`** — A single file (e.g., `findings.md`)
- **`files`** — Multiple files (e.g., a directory of individual source analyses)

### Dependencies

The `dependencies` list declares which steps must complete before this step can run. This is how DeepWork knows the execution order. A step's dependencies typically match the steps it draws `from_step` inputs from.

## Workflows

A workflow is a named execution path through a job's steps. One job can have multiple workflows — for example, a `full_analysis` workflow that runs everything, and a `quick_check` that runs a subset.

```yaml
workflows:
  - name: full
    summary: "Run the complete fruits identification and classification"
    steps:
      - identify
      - classify
```

Workflows are what you invoke:

```
/deepwork fruits full
```

### Concurrent Steps

Steps can run in parallel by wrapping them in an array within the workflow's step list:

```yaml
workflows:
  - name: full_analysis
    summary: "Complete analysis with parallel research phase"
    steps:
      - setup
      - [research_web, research_docs, research_interviews]  # these run concurrently
      - compile_results
      - final_review
```

In this example, `setup` runs first, then the three research steps run in parallel, then `compile_results` runs after all three finish.

## Quality Gates

Steps can define review criteria. After the AI agent finishes a step, its outputs are evaluated against these criteria. If criteria fail, the agent gets feedback and retries.

```yaml
reviews:
  - run_each: job_yml
    quality_criteria:
      "Job Structure": "Does the job.yml define the expected steps with correct dependencies?"
      "Outputs Defined": "Does the step have the required output files?"
```

Reviews enforce quality without human intervention — the AI agent iterates until the work meets the defined standard.

## Example: Repo Setup Job

A more realistic example showing concurrent steps — a `repo` job that configures a GitHub repository:

```
Job (e.g., "repo")
├── Steps: [audit_repo, create_labels, branch_protection, issue_templates, pr_templates, invite_collaborators]
└── Workflows:
    ├── "setup"          → [audit_repo, [create_labels, branch_protection, issue_templates, pr_templates], invite_collaborators]
    ├── "doctor"         → [audit_repo]
    └── "onboard_user"   → [invite_collaborators]
```

```mermaid
graph TD
    A["audit_repo"] --> L["create_labels"]
    A --> B["branch_protection"]
    A --> I["issue_templates"]
    A --> P["pr_templates"]
    L --> C["invite_collaborators"]
    B --> C
    I --> C
    P --> C

    style L fill:#f0e6d3,stroke:#c2603a
    style B fill:#f0e6d3,stroke:#c2603a
    style I fill:#f0e6d3,stroke:#c2603a
    style P fill:#f0e6d3,stroke:#c2603a
```

The `setup` workflow audits the repo first, then configures labels, branch protection, and templates concurrently (highlighted), then invites collaborators once everything is in place. The `doctor` workflow runs just the audit to check what's missing. The `onboard_user` workflow skips repo config and just sends invites.

## What Happens When You Run a Workflow

```mermaid
flowchart TD
    GW["get_workflows<br/><i>list available workflows</i>"]
    SW["start_workflow<br/><i>initialize & return first step</i>"]
    EX["Execute step<br/><i>read instructions, gather inputs,<br/>produce outputs</i>"]
    FS["finished_step<br/><i>record outputs, run reviews</i>"]
    PASS{"Reviews<br/>pass?"}
    MORE{"More<br/>steps?"}
    DONE["Workflow complete"]

    GW --> SW --> EX --> FS --> PASS
    PASS -->|No — needs_work| EX
    PASS -->|Yes| MORE
    MORE -->|Yes — next_step| EX
    MORE -->|No| DONE
```

1. **get_workflows** — DeepWork lists available workflows for the job
2. **start_workflow** — You pick a workflow; DeepWork initializes it and returns the first step(s)
3. **Execute step** — The AI agent reads the step's instructions, gathers inputs, and produces outputs
4. **finished_step** — DeepWork records the outputs and runs any quality reviews
5. **Next step or retry** — If reviews pass, DeepWork advances to the next step(s). If reviews fail, the agent gets feedback and retries the current step
6. **Complete** — When all steps in the workflow finish, the workflow is complete
