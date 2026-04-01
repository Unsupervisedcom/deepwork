# Project context for marketing

This is a **library job** -- reusable marketing workflows that any project can adopt.

## Purpose

Marketing workflows for competitive content analysis, content strategy, and campaign
execution. The first workflow (`competitive_content_analysis`) analyzes competitors'
content strategies across channels and produces actionable recommendations.

## Location

This job lives in `library/jobs/marketing/`. It is NOT auto-installed -- users adopt it
via `DEEPWORK_ADDITIONAL_JOBS_FOLDERS`, the `shared_jobs` workflow, or by copying it
into their project's `.deepwork/jobs/` directory.

## Workflows

| Workflow                       | Steps                                                                                    | Purpose                                                  |
|--------------------------------|------------------------------------------------------------------------------------------|----------------------------------------------------------|
| `competitive_content_analysis` | discover_context, research_all_competitors, analyze_patterns, gap_analysis, final_report | Full competitive content analysis with parallel research |
| `research_one_competitor`      | gather_content, analyze_content                                                          | Deep-dive on a single competitor (sub-workflow)          |

## Planned workflows (not yet implemented)

- `campaign_planning` -- strategy through execution
- `content_calendar` -- content calendar across channels
- `seo_audit` -- technical and content SEO audit
- `social_media_strategy` -- platform-specific playbooks
- `email_marketing` -- campaigns and automations
- `launch_comms` -- launch communications coordination
- `analytics_attribution` -- performance and attribution models

## Shared patterns

These steps are designed for reuse across sibling workflows:

- **discover_context**: Project/brand context discovery with output directory inference
- **Competitor identification**: Building and validating competitor lists

## Output conventions

Workflow outputs are durable notes. If the user has a notes directory
(`NOTES_DIR` or `ZK_NOTEBOOK_DIR`), follow its AGENTS.md conventions for note
creation and placement. The final report is a report-type note; supporting
per-competitor research goes as literature notes linked via wikilinks. Fall back
to `.deepwork/tmp/` only if no notes directory exists.

This job does not embed note creation mechanics (zk commands, frontmatter
format, tag conventions) because those vary by user setup. The user's notes
repo AGENTS.md and the agent's platform conventions are the source of truth for
how to create notes. See `process.notes` and `tool.zk-notes` for the canonical
rules if available in the agent's instruction context.

## Quality review learnings

(No learnings recorded yet.)
