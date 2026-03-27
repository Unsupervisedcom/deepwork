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

Here is an example response from deepwork research reproduce.

```
● Reproduce workflow complete. Here's what was produced in research/dsn-et-tai-algorithms/:

  Reproducibility Analysis — 5 items identified:
  - P0: Dual-frequency ionosphere-free combination (hours), full iterative ET−TAI algorithm (weeks)
  - P1: GPS receiver phase-center offsets (hours), TOPEX phase-center vector (days)
  - P2: GPS transmission-time algorithm (days)

  Reproduction Plan — 8 tasks, 2–4 weeks estimated:
  - Critical path: Ingest Sections 2/3/5 → SPICE setup → approximate ET−TAI → station position → full iterative algorithm
  - Key blocker: Sections 2, 3, and 5 of the monograph contain the core equations referenced by all four algorithms

  Open questions for you:
  1. Which language — Python (fast prototyping with astropy/spiceypy) or Rust?
  2. Validate against existing tools (Astropy/SOFA) or clean-room implementation?
  3. Just Section 7, or working toward the full ODP formulation?
```

## Quick Start

If you haven't already, enable shared library jobs in your project:

```
/deepwork shared_jobs
```

Natural language is matched to the `research` job's `research` workflow. Scopes the question, gathers from multiple platforms, synthesizes findings, and produces a report with bibliography.

```
/deepwork do a deep research run on growing plants in lunar regolith
```

Or create a Claude skill for quick access, then use it:

```
/deepwork create a /research.deep skill that runs the research job's research workflow
```

```
/research.deep growing plants in lunar regolith
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
