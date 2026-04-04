# Project context for marketing

This is a **library job** -- reusable marketing workflows that any project can adopt.

## Purpose

General-purpose marketing workflows for competitive analysis, content strategy,
social media planning, and campaign execution. Steps prefixed `cca_` are specific
to competitive content analysis; prefixed `sm_` are specific to social media.
Unprefixed steps (`discover_context`, `audit_own_content`, `create_campaign`,
`brainstorm_content`) are shared across workflows.

## Location

This job lives in `library/jobs/marketing/`. It is NOT auto-installed -- users adopt it
via `DEEPWORK_ADDITIONAL_JOBS_FOLDERS`, the `shared_jobs` workflow, or by copying it
into their project's `.deepwork/jobs/` directory.

## Workflows

| Workflow                       | Steps                                                                                                      | Purpose                                                  |
|--------------------------------|------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|
| `competitive_content_analysis` | discover_context, cca_research_all_competitors, cca_analyze_patterns, audit_own_content, cca_gap_analysis, cca_final_report, create_campaign, brainstorm_content | Competitive content analysis with own-content audit, campaign tracking, and brainstorm |
| `social_media_setup`           | discover_context, audit_own_content, sm_define_strategy, create_campaign                                   | Content strategy and social media planning for a project |

Per-competitor research is delegated to the shared `research` job (`research/quick` or `research/research`) via nested workflow calls. No marketing-internal research sub-workflow needed.

## Planned workflows (not yet implemented)

- `campaign_planning` -- strategy through execution
- `content_calendar` -- content calendar across channels
- `seo_audit` -- technical and content SEO audit
- `email_marketing` -- campaigns and automations
- `launch_comms` -- launch communications coordination
- `analytics_attribution` -- performance and attribution models

## Shared steps

These steps are reused across sibling workflows:

- **discover_context**: Project/brand context discovery with output directory inference
- **audit_own_content**: Crawl and catalog existing content across all channels
- **create_campaign**: Create milestone + parent issue on the user's project tracker
- **brainstorm_content**: Interactive content ideation posted as issue comment

## Output conventions

Workflow outputs are durable notes. If the user has a notes directory
(`NOTES_DIR` or `ZK_NOTEBOOK_DIR`), follow its AGENTS.md conventions for note
creation and placement. The final report is a report-type note; supporting
per-competitor research goes as literature notes linked via wikilinks. Fall back
to `.deepwork/tmp/` only if no notes directory exists.

This job does not embed note creation mechanics (zk commands, frontmatter
format, tag conventions) because those vary by user setup. The user's notes
repo AGENTS.md and the agent's platform conventions are the source of truth for
how to create notes. Follow the user's notes-directory conventions and any
applicable instructions available in the agent's instruction context.

## Quality review learnings

### 2026-04-01: Plant Caravan competitive content analysis

- The workflow originally ended at `final_report`. Analysis without action tracking
  left the user to manually create issues and milestones. Added `create_campaign`
  and `brainstorm_content` steps to close the loop.
- The user had specific content ideas they wanted to explore but the workflow gave
  no opportunity for interactive brainstorming. The new `brainstorm_content` step
  asks structured questions to capture the user's vision alongside the data-driven
  recommendations.
- Forgejo required `-r` flag on `yq` for token extraction — tea config stores
  tokens as YAML strings that include quotes without raw output mode.
- The gap analysis compared competitor content against a one-line summary of
  the brand's content from context_brief.md rather than an actual audit. Added
  `audit_own_content` step that crawls the brand's website, blog, and social
  channels to produce a real inventory before gap analysis runs.
