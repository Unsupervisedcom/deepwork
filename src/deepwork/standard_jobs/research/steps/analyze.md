# Analyze Reproducibility

## Objective

Analyze ingested research material to identify reproducible claims, experiments, methodologies, and technical approaches. Assess each for feasibility, resource requirements, and engineering effort.

## Task

### Process

1. **Read the ingested material**

   Read the `ingested_path` reference from the prior step to locate the filed research material. Then read the full content of the filed note, paying particular attention to:
   - Key findings listed in the frontmatter
   - Methodology sections
   - Experimental setups and results
   - Technical claims about performance, behavior, or architecture
   - Code samples, configurations, or parameters mentioned

2. **Identify reproducible items**

   Scan the material for items that can be independently reproduced or validated:

   - **Experiments**: Specific experiments with measurable outcomes
   - **Claims**: Technical claims that can be verified through implementation
   - **Methodologies**: Approaches or techniques that can be applied in a different context
   - **Benchmarks**: Performance measurements that can be re-run
   - **Architectures**: System designs that can be implemented

   For each item, extract:
   - What exactly is being claimed or demonstrated
   - What would constitute successful reproduction
   - What information is available vs. missing

3. **Assess feasibility**

   For each reproducible item, evaluate:

   - **Complexity**: How much engineering effort is needed? (low / medium / high)
   - **Prerequisites**: What tools, data, infrastructure, or knowledge is required?
   - **Data availability**: Is the data publicly available, or would substitutes be needed?
   - **Time estimate**: Rough order of magnitude (hours / days / weeks)
   - **Risk factors**: What could go wrong? What's underspecified?

4. **Prioritize items**

   Rank by a combination of:
   - **Impact**: How valuable is reproducing this? Does it validate a key claim?
   - **Feasibility**: How practical is it given available resources?
   - **Clarity**: How well-specified is the reproduction path?

   Use a simple priority: P0 (do first), P1 (do next), P2 (nice to have).

5. **Write reproducibility_analysis.md**

## Output Format

### reproducibility_analysis.md

**Location**: `research/[topic_slug]/reproducibility_analysis.md`

```markdown
# Reproducibility Analysis: [Topic Name]

**Source**: [title of ingested material]
**Date**: [YYYY-MM-DD]

## Summary

[2-3 sentences: what was analyzed and how many reproducible items were identified]

## Reproducible Items

### 1. [Item Name] — Priority: [P0 | P1 | P2]

**Type**: [experiment | claim | methodology | benchmark | architecture]

**What to reproduce**: [Specific description of what would be reproduced]

**Success criteria**: [What constitutes successful reproduction]

**Feasibility**:
- Complexity: [low | medium | high]
- Prerequisites: [tools, data, infrastructure needed]
- Data availability: [available | partially available | unavailable]
- Time estimate: [hours | days | weeks]
- Risk factors: [what could block or complicate reproduction]

**Missing information**: [What's not specified in the original material]

---

### 2. [Item Name] — Priority: [P0 | P1 | P2]

[Same structure]

---

[Repeat for all identified items]

## Priority Summary

| Priority | Count | Items |
|---|---|---|
| P0 | [n] | [item names] |
| P1 | [n] | [item names] |
| P2 | [n] | [item names] |

## Resource Requirements

**Combined prerequisites for all P0 items**:
- Tools: [list]
- Data: [list]
- Infrastructure: [list]
- Estimated total effort: [range]
```

**Concrete example** (abbreviated):

```markdown
# Reproducibility Analysis: Flash Attention 3

**Source**: Flash Attention 3: Fast and Exact Attention with IO-Awareness
**Date**: 2026-03-20

## Summary

Analyzed the Flash Attention 3 paper identifying 4 reproducible items: the core kernel benchmark, memory usage claims, backward pass optimization, and integration with PyTorch.

## Reproducible Items

### 1. Core Kernel Benchmark — Priority: P0

**Type**: benchmark

**What to reproduce**: Measure attention kernel throughput (TFLOPS) for sequence lengths 512-16384 on H100 GPU, comparing Flash Attention 3 vs. standard attention.

**Success criteria**: Achieve within 10% of reported TFLOPS numbers for each sequence length.

**Feasibility**:
- Complexity: medium
- Prerequisites: H100 GPU, CUDA 12+, PyTorch 2.x
- Data availability: available (synthetic random tensors)
- Time estimate: days
- Risk factors: exact GPU model and driver version may affect numbers
```

## Quality Criteria

- Specific reproducible claims, experiments, or methodologies are clearly listed
- Each item has a feasibility assessment including resource requirements and prerequisites
- Items are prioritized by impact and feasibility
- Success criteria are defined for each item
- Missing information is explicitly noted
- Priority summary table provides a quick overview

## Context

This is the second step of the **reproduce** workflow. The analysis here directly feeds into the **plan** step, which converts these reproducible items into actionable engineering tasks. Be thorough in identifying what's reproducible but realistic about feasibility — the plan step needs honest assessments to create useful work items.
