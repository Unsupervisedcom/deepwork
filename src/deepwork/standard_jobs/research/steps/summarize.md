# Summarize Research

## Objective

Synthesize the gathered sources and produce a concise research summary in a single step. This combines the synthesis and report stages into one streamlined output for quick research.

## Task

### Process

1. **Read inputs**

   - Read `research/[topic_slug]/scope.md` for the research question, sub-questions, and project context
   - Read `research/[topic_slug]/sources.md` for gathered sources and findings

2. **Synthesize across sources**

   For each sub-question from scope.md:
   - Identify which sources address it
   - Write a brief synthesized answer drawing from the sources
   - Note any contradictions or gaps

3. **Formulate key findings**

   Distill the most important findings into 3-5 clear points. Each should:
   - Directly address some aspect of the research question
   - Be supported by at least one source
   - Be cited with inline markdown links

4. **Write concise takeaways**

   Write 2-3 actionable takeaways. Since this is quick research, acknowledge limitations:
   - What the evidence suggests
   - What gaps remain that might warrant deeper research
   - If project-associated, what this means for the project

5. **Create project symlink (if applicable)**

   If scope.md specifies a project tag:
   ```bash
   mkdir -p projects/[ProjectName]/research
   ln -s ../../../research/[topic_slug] projects/[ProjectName]/research/[topic_slug]
   ```

6. **Write README.md**

## Output Format

### README.md

**Location**: `research/[topic_slug]/README.md`

```markdown
# Research: [Topic Name]

## Overview

**Type**: [science | business | competitive | market | technical]
**Depth**: quick
**Project**: [#ProjectTag or N/A]
**Date**: [YYYY-MM-DD]
**Sources**: [count] sources via local web search

## Research Question

[Clear statement from scope.md]

## Findings

### [Finding Area 1]

[Concise findings with inline citations like [Source Title](url)]

### [Finding Area 2]

[Concise findings with citations]

## Key Takeaways

1. [Actionable takeaway]
2. [Actionable takeaway]
3. [Actionable takeaway]

## Limitations

- Quick depth: [count] sources gathered via local search only
- [Note any sub-questions that lack coverage]
- [Suggest deeper research if warranted]

## Sources

| # | Title | URL |
|---|-------|-----|
| 1 | [Source Title] | [url] |
| 2 | [Source Title] | [url] |
| 3 | [Source Title] | [url] |
```

**Concrete example**:

```markdown
# Research: Nix Remote Builder Performance

## Overview

**Type**: technical
**Depth**: quick
**Project**: #Keystone
**Date**: 2026-03-20
**Sources**: 4 sources via local web search

## Research Question

What is the performance overhead of Nix remote builders compared to local builds?

## Findings

### Build Latency

Remote builders add 5-15% overhead for large derivations due to store path copying, but can reduce wall-clock time significantly for parallel builds ([NixOS Wiki](https://nixos.wiki/wiki/Distributed_build)).

### Configuration Impact

Using `--max-jobs` and `--cores` on remote machines provides near-linear scaling for independent derivations ([Nix Manual](https://nix.dev/manual/nix/latest)).

## Key Takeaways

1. Remote builders are net-positive for builds with 3+ independent derivations
2. Store path copying is the main bottleneck — binary cache helps
3. Worth investigating for Keystone's multi-host build pipeline

## Limitations

- Quick depth: 4 sources via local search only
- No benchmarks with real-world NixOS configurations found
- Deeper research recommended for production deployment decisions

## Sources

| # | Title | URL |
|---|-------|-----|
| 1 | NixOS Wiki: Distributed build | https://nixos.wiki/wiki/Distributed_build |
| 2 | Nix Manual: Remote Builds | https://nix.dev/manual/nix/latest |
| 3 | Blog: Scaling Nix Builds | https://example.com/nix-scaling |
| 4 | Discourse: Remote builder experience | https://discourse.nixos.org/t/... |
```

## Quality Criteria

- Summary is focused and concise, appropriate for quick research depth
- Directly answers the research question from scope.md
- Key claims cite sources with inline markdown links
- Limitations section acknowledges the quick depth and any coverage gaps
- Sources table provides a quick reference of all sources used

## Context

This is the final step of the **quick** workflow. Unlike the **research** workflow which has separate synthesize and report steps, this step combines both into one streamlined output. The result should be useful on its own for quick decisions while clearly noting when deeper research would be warranted.
