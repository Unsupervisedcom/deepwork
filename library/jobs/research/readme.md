# Research

A multi-workflow research suite for deep investigation, quick summaries, material ingestion, and reproduction planning.

## Overview

This job provides four workflows covering the full research lifecycle — from scoping a question to producing a polished report, importing external material into your notes, or creating an engineering reproduction plan.

## Workflows

### research (Deep Investigation)

Full multi-platform research with 8+ sources, cross-platform validation, and comprehensive report with bibliography.

```
scope → choose_platforms → gather → synthesize → report
```

**Platform support**: Local (WebSearch/WebFetch), Gemini Deep Research, ChatGPT, Grok, Perplexity

### quick (Fast Summary)

Local-only research producing a concise summary from 3+ sources.

```
scope → gather_quick → summarize
```

### ingest (Material Import)

Import external research material (markdown, papers, URLs) into your notes system with frontmatter metadata and tags.

```
parse → file
```

Requires `NOTES_DIR` or `NOTES_RESEARCH_DIR` environment variables.

### reproduce (Reproducibility Planning)

Ingest research material, analyze for reproducible claims, and create an engineering plan with optional issue creation.

```
ingest_material → analyze → plan
```

## Quick Start

Natural language is matched to the `research` job's `research` workflow. Scopes the question, gathers from multiple platforms, synthesizes findings, and produces a report with bibliography.

```
/deepwork do a deep research run on growing plants in lunar regolith
```

Or create Claude skills for quick access:

```
/deepwork create a /research.deep skill that runs the research job's research workflow
```

## Prerequisites

- For **research** workflow: Browser tool access if using external platforms (Gemini, ChatGPT, etc.)
- For **ingest/reproduce** workflows: `NOTES_DIR` environment variable set to your notes root directory

## Research Types

science, business, competitive, market, technical

## Output Locations

- **research/quick**: `research/[topic_slug]/` in the working directory
- **ingest**: `$NOTES_RESEARCH_DIR/[topic_slug]/` with frontmatter tags
- **reproduce**: reproduction plan in working directory + optional issue creation
