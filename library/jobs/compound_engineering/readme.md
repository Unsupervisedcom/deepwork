# Compound Engineering Job

A DeepWork implementation inspired by [Every Inc's Compound Engineering Plugin](https://github.com/EveryInc/compound-engineering-plugin).

## Overview

This job implements the core Compound Engineering methodology: **"Each unit of engineering work should make subsequent units easier—not harder."**

The workflow inverts traditional development ratios:
- **80% planning and review** (frontloading quality)
- **20% execution** (following the plan)

By systematically capturing learnings and maintaining quality gates, technical debt decreases over time instead of accumulating.

## The Four Steps

| Step | Purpose | Time Investment |
|------|---------|-----------------|
| **Plan** | Transform ideas into detailed implementation plans with research | 40% |
| **Work** | Execute plans with task tracking and incremental commits | 20% |
| **Review** | Multi-perspective code review before merging | 30% |
| **Compound** | Document solutions and learnings for future reuse | 10% |

## Installation

1. Copy this job to your project:
   ```bash
   cp -r library/jobs/compound_engineering .deepwork/jobs/
   ```

2. Sync to generate slash commands:
   ```bash
   deepwork sync
   ```

3. Reload Claude Code to see the new commands.

## Usage

### Full Cycle
```
/compound_engineering
```
Select the `full_cycle` workflow to run all steps in sequence.

### Individual Steps
```
/compound_engineering.plan    # Create an implementation plan
/compound_engineering.work    # Execute a plan
/compound_engineering.review  # Review code changes
/compound_engineering.compound # Document learnings
```

## Customization

Before using, you may want to customize:

| Placeholder | Location | Purpose |
|-------------|----------|---------|
| `[test_command]` | steps/work.md | Your test runner command |
| `[lint_command]` | steps/work.md | Your linting command |
| `[code_review_standards_path]` | job.yml | Path to your review standards |

---

## What DeepWork Does Automatically

The following features from the original Compound Engineering plugin **did not need to be re-implemented** because DeepWork provides them automatically:

### 1. Slash Command Generation
- **Original**: Plugin manually defines `/workflows:plan`, `/workflows:work`, etc.
- **DeepWork**: Automatically generates slash commands from job.yml steps

### 2. Step-by-Step Workflow Execution
- **Original**: Plugin implements workflow orchestration logic
- **DeepWork**: Handles step sequencing, dependencies, and execution automatically

### 3. Quality Hooks and Validation
- **Original**: Plugin implements pre/post hooks for quality checks
- **DeepWork**: Provides hook system via `deepwork hook` command

### 4. Platform Integration (Claude Code)
- **Original**: Plugin packages commands for Claude Code marketplace
- **DeepWork**: Syncs jobs to `.claude/commands/` automatically

### 5. Multi-Platform Support
- **Original**: Plugin has separate converters for OpenCode, Codex
- **DeepWork**: Supports Claude Code and Gemini CLI natively

### 6. Workflow State Management
- **Original**: Plugin tracks workflow progress
- **DeepWork**: Maintains state through step dependencies and outputs

### 7. Rules System
- **Original**: Plugin has rules for file monitoring
- **DeepWork**: Provides `.deepwork/rules/` for file-based rules

### 8. Sub-agent Coordination
- **Original**: Plugin spawns specialized agents
- **DeepWork**: Agents can use Task tool with guidance from step instructions

---

## What This Version Does NOT Support

The following features from the original Compound Engineering plugin are **not implemented** in this DeepWork version:

### 1. Specialized Review Agents (28 agents in original)
**Original**: 14+ specialized review agents including:
- `kieran-rails-reviewer`, `dhh-rails-reviewer` (framework-specific)
- `security-sentinel`, `performance-oracle` (domain-specific)
- `code-simplicity-reviewer`, `pattern-recognition-specialist`

**This Version**: Uses general-purpose sub-agents with prompts that guide review perspective. Less specialized but more flexible.

**Impact**: Reviews may miss framework-specific nuances that dedicated agents would catch.

### 2. Git Worktree Integration
**Original**: `/workflows:work` and `/workflows:review` offer to create git worktrees for isolated development/review environments.

**This Version**: Does not manage git worktrees. Users work on regular branches.

**Impact**: Can't do parallel development in isolated environments as easily.

### 3. File-Based Todo Tracking (`todos/` directory)
**Original**: Creates markdown todo files in `todos/` directory with YAML frontmatter, status tracking (pending/ready/complete), and priority levels.

**This Version**: Uses TodoWrite tool for in-session tracking. No persistent todo files.

**Impact**: Task state doesn't persist between sessions. Can't triage todos across team.

### 4. Screenshot Capture and Upload
**Original**: `/workflows:work` captures screenshots for UI changes and uploads to image hosts for PR documentation.

**This Version**: Does not automate screenshot capture or upload.

**Impact**: Visual documentation must be done manually.

### 5. MCP Server Integration (context7)
**Original**: Integrates with context7 MCP server for framework documentation lookup (100+ frameworks).

**This Version**: Uses WebSearch for external research. No MCP integration.

**Impact**: Framework-specific documentation lookup is less reliable.

### 6. Figma Design Sync
**Original**: `figma-design-sync` agent synchronizes web implementations with Figma designs.

**This Version**: No Figma integration.

**Impact**: Design-to-code verification is manual.

### 7. Browser Automation (`agent-browser`)
**Original**: Provides CLI-based browser automation for testing and screenshots.

**This Version**: No browser automation.

**Impact**: Can't automate browser-based testing or capture.

### 8. Image Generation (`gemini-imagegen`)
**Original**: Generates and edits images using Google's Gemini API.

**This Version**: No image generation capability.

**Impact**: Can't generate documentation images or diagrams.

### 9. PR Comment Resolution
**Original**: `/resolve_pr_parallel` resolves GitHub PR comments in parallel.

**This Version**: No dedicated PR comment resolution.

**Impact**: PR feedback must be addressed manually.

### 10. Automatic Trigger Phrases
**Original**: `/workflows:compound` auto-triggers on phrases like "that worked!", "it's fixed".

**This Version**: Must be invoked explicitly.

**Impact**: Users may forget to document learnings.

### 11. Language/Framework-Specific Skills
**Original**: 15 skills including `dhh-rails-style`, `andrew-kane-gem-writer`, `dspy-ruby`, `frontend-design`.

**This Version**: No framework-specific skills included.

**Impact**: Must prompt for framework conventions manually.

### 12. Changelogs and Release Management
**Original**: `/changelog` generates changelogs, `/release-docs` manages documentation.

**This Version**: No changelog or release automation.

**Impact**: Release documentation is manual.

---

## Suggestions for Improving DeepWork

Based on the gaps above and analysis of how Compound Engineering works, here are suggestions for DeepWork:

### High Priority

#### 1. Persistent Todo Files
**Gap**: TodoWrite is session-scoped; Compound Engineering persists todos to files.

**Suggestion**: Add a `todo_persistence` option to jobs that writes TodoWrite state to markdown files in a `todos/` directory. This enables:
- Task state persistence between sessions
- Team-wide task visibility
- Triage workflows across multiple contributors

#### 2. Agent Persona System
**Gap**: Can't define specialized agent personas that bring domain expertise.

**Suggestion**: Add an `agents/` directory to jobs where users can define personas:
```yaml
# .deepwork/jobs/my_job/agents/security-reviewer.yml
name: security-reviewer
persona: |
  You are a security-focused code reviewer. You look for:
  - Input validation gaps
  - Authentication/authorization issues
  - Data exposure risks
  ...
```

These could be referenced in steps: `use_agent: security-reviewer`

#### 3. Parallel Sub-agent Execution
**Gap**: Review step must spawn sub-agents sequentially or rely on Task tool parallelism.

**Suggestion**: Add explicit parallel execution syntax in steps:
```yaml
parallel_agents:
  - security-reviewer
  - performance-reviewer
  - pattern-reviewer
aggregate_results: true
```

### Medium Priority

#### 4. External Tool Integration (MCP)
**Gap**: No way to integrate with MCP servers like context7.

**Suggestion**: Add `mcp_servers` configuration to job.yml or project config:
```yaml
mcp_servers:
  - name: context7
    url: https://context7.com/mcp
```

#### 5. Trigger Phrases / Auto-invocation
**Gap**: Jobs must be explicitly invoked.

**Suggestion**: Add `triggers` to job.yml:
```yaml
triggers:
  phrases:
    - "that worked"
    - "finally fixed"
    - "problem solved"
  action: suggest  # or auto-run
```

#### 6. Git Worktree Support
**Gap**: No built-in worktree management.

**Suggestion**: Add worktree helpers:
```bash
deepwork worktree create feature-x
deepwork worktree list
deepwork worktree cleanup
```

Or document a pattern for managing worktrees in jobs.

#### 7. Screenshot/Image Capture
**Gap**: No visual documentation automation.

**Suggestion**: Add image capture to the tool set or document integration with existing screenshot tools. Could be a skill in the library.

### Lower Priority

#### 8. Framework Detection and Adaptation
**Gap**: Jobs don't adapt based on detected frameworks.

**Suggestion**: Add framework detection:
```yaml
framework_adaptations:
  rails:
    review_agents: [rails-reviewer]
    test_command: bundle exec rspec
  nextjs:
    review_agents: [react-reviewer]
    test_command: npm test
```

#### 9. PR Integration
**Gap**: No direct GitHub/GitLab PR integration.

**Suggestion**: Add PR utilities:
```bash
deepwork pr create --from-plan docs/plans/feature-plan.md
deepwork pr review 123
```

#### 10. Learning Aggregation
**Gap**: Solutions accumulate but aren't automatically aggregated into patterns.

**Suggestion**: Add a `deepwork learn analyze` command that:
- Scans `docs/solutions/`
- Identifies recurring themes
- Suggests pattern documentation
- Detects critical issues that should be in required reading

---

## The Compound Engineering Philosophy

This job embodies a specific philosophy about engineering work:

1. **Planning Pays Dividends**: Time invested in planning reduces time spent on rework, debugging, and reviews. The 80/20 split (planning/execution) may seem extreme but yields higher quality.

2. **Quality is a Multiplier**: Every quality check now prevents multiple issues later. Technical debt compounds negatively; quality compounds positively.

3. **Knowledge Should Accumulate**: Solutions captured today accelerate work tomorrow. The `docs/solutions/` directory becomes an ever-growing knowledge base.

4. **Multiple Perspectives Catch More**: A single reviewer misses things. Multiple specialized perspectives (security, performance, patterns) catch a broader range of issues.

5. **Small Commits, Continuous Testing**: Large batched commits are harder to review and debug. Small incremental commits with continuous testing maintain quality.

## Credits

This job is inspired by and based on [Every Inc's Compound Engineering Plugin](https://github.com/EveryInc/compound-engineering-plugin) (MIT License).

The original plugin provides:
- 28 specialized agents
- 24 slash commands
- 15 skills
- MCP server integration
- Multi-platform support

This DeepWork version captures the core methodology in a simpler, more portable format while identifying gaps that could improve DeepWork's capabilities.

---

*This example demonstrates how DeepWork can replicate sophisticated AI engineering workflows while highlighting areas for platform improvement.*
