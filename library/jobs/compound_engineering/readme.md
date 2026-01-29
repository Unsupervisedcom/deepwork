# Compound Engineering

A DeepWork implementation of [Every's Compound Engineering methodology](https://github.com/EveryInc/compound-engineering-plugin) - making each unit of engineering work easier than the last.

## Overview

This job implements the core Compound Engineering workflow cycle:

```
Plan -> Work -> Review -> Compound -> Repeat
```

**Philosophy**: 80% of effort goes into planning and review, 20% into execution. Each cycle compounds knowledge - plans inform future plans, reviews catch more issues, and patterns get documented for reuse.

## Quick Start

1. Copy this job to your project:
   ```bash
   cp -r library/jobs/compound_engineering .deepwork/jobs/
   ```

2. Sync to generate slash commands:
   ```bash
   deepwork sync
   ```

3. Start using the workflow:
   - `/compound_engineering.brainstorm` - Explore a feature idea
   - `/compound_engineering.plan` - Create implementation plan
   - `/compound_engineering.work` - Execute the plan
   - `/compound_engineering.review` - Review changes
   - `/compound_engineering.compound` - Document learnings

## Workflow Steps

| Step | Purpose | When to Use |
|------|---------|-------------|
| **Brainstorm** | Explore requirements through dialogue | Feature is unclear or needs design exploration |
| **Plan** | Create detailed implementation plan | Starting any new feature or bug fix |
| **Work** | Execute plan with task tracking | Ready to implement |
| **Review** | Multi-perspective code review | Before merging PR |
| **Compound** | Document learnings for reuse | After solving a non-trivial problem |

### Full Workflow

Use the `full_cycle` workflow for comprehensive feature development:
```
/compound_engineering.full_cycle
```

### Shortcuts

- `plan_and_work` - Skip brainstorming for clear requirements
- `review_cycle` - Review and document existing changes

## Artifacts Produced

- `docs/brainstorms/` - Design exploration documents
- `docs/plans/` - Implementation plans with acceptance criteria
- `docs/solutions/` - Documented problem resolutions (compounded knowledge)
- `docs/reviews/` - Code review findings

## Credit

This job is a DeepWork adaptation of the [Compound Engineering Plugin](https://github.com/EveryInc/compound-engineering-plugin) by [Every](https://every.to/). For the full philosophy, read:
- [Compound engineering: how Every codes with agents](https://every.to/chain-of-thought/compound-engineering-how-every-codes-with-agents)
- [The story behind compounding engineering](https://every.to/source-code/my-ai-had-already-fixed-the-code-before-i-saw-it)

---

## Comparison: DeepWork vs. Claude Code Plugin

This section documents what DeepWork handles automatically, what the original plugin supports that this version doesn't, and suggestions for improving DeepWork.

### Things DeepWork Does Automatically

The following features are handled by DeepWork's core framework, requiring no re-implementation:

| Feature | DeepWork Approach | Original Plugin Approach |
|---------|-------------------|-------------------------|
| **Slash command generation** | Automatic via `deepwork sync` - converts job.yml steps to `/job.step` commands | Manual command files in `commands/` folder |
| **Multi-platform support** | Built-in sync to Claude Code, Gemini, Codex formats | Separate CLI tool (`bunx @every-env/compound-plugin install --to opencode`) |
| **Step dependencies** | Declarative in job.yml with `dependencies:` field | Implicit in command instructions |
| **Input/output tracking** | Explicit in job.yml with `inputs:` and `outputs:` fields | Ad-hoc file references in markdown |
| **Quality criteria** | Structured in job.yml with `quality_criteria:` field | Embedded in command prose |
| **Workflow composition** | Named workflows combining steps in job.yml | Manual command chaining by user |
| **Version tracking** | Built-in `version:` and `changelog:` fields | Separate CHANGELOG.md file |
| **Step visibility** | `hidden: true` for internal steps | No equivalent |

**Key Insight**: DeepWork's structured job.yml format captures metadata that the plugin expresses through prose, making it easier to validate, compose, and extend workflows programmatically.

### Features the Original Plugin Supports That This Version Does Not

The Compound Engineering Plugin has 28 agents, 24 commands, and 15 skills. This DeepWork version implements the 5 core workflow steps. Here's what's missing:

#### 1. Specialized Review Agents

The plugin has 13+ specialized review agents that run in parallel:

| Agent | Purpose |
|-------|---------|
| `kieran-rails-reviewer` | Rails-specific best practices |
| `dhh-rails-reviewer` | DHH's Rails style conventions |
| `code-simplicity-reviewer` | YAGNI and minimalism review |
| `security-sentinel` | Security vulnerability scanning |
| `performance-oracle` | Performance issue detection |
| `architecture-strategist` | Architectural pattern review |
| `data-integrity-guardian` | Database and data safety |
| `data-migration-expert` | Migration safety validation |
| `agent-native-reviewer` | Verifies agent accessibility |
| `pattern-recognition-specialist` | Anti-pattern detection |

**DeepWork Gap**: No built-in concept of "agents" as parallel sub-tasks with specialized prompts.

#### 2. Research Agents

| Agent | Purpose |
|-------|---------|
| `best-practices-researcher` | External best practices research |
| `framework-docs-researcher` | Official documentation lookup |
| `learnings-researcher` | Search docs/solutions/ for prior learnings |
| `repo-research-analyst` | Codebase pattern analysis |
| `git-history-analyzer` | Git history insights |

**DeepWork Gap**: No built-in research phase or external knowledge integration.

#### 3. MCP Server Integration

The plugin integrates Context7 MCP server for documentation access:
```json
"mcpServers": {
  "context7": {
    "type": "http",
    "url": "https://mcp.context7.com/mcp"
  }
}
```

**DeepWork Gap**: No MCP server integration in job definitions.

#### 4. Interactive User Questioning

The plugin uses `AskUserQuestion` tool for structured dialogue:
- Multiple choice questions
- Decision gates that wait for user input
- Post-action option menus

**DeepWork Gap**: No declarative way to define interactive decision points in job.yml.

#### 5. Auto-Invoke Triggers

The plugin auto-invokes `/compound` on phrases like:
- "that worked"
- "it's fixed"
- "working now"

**DeepWork Gap**: No hook system for auto-triggering steps based on conversation content.

#### 6. Skills with Scripts and Templates

Plugin skills include executable scripts:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/git-worktree/scripts/worktree-manager.sh create feature-name
```

And templates for generating content:
```
.claude/skills/compound-docs/assets/resolution-template.md
```

**DeepWork Gap**: Skills have references and workflows, but no standardized script/template system.

#### 7. Browser and Design Integration

| Feature | Plugin Support |
|---------|---------------|
| `agent-browser` skill | Playwright-based browser automation |
| `figma-design-sync` agent | Compare implementation to Figma designs |
| `imgup` skill | Screenshot upload to image hosts |
| `test-browser` command | End-to-end browser testing |
| `xcode-test` command | iOS simulator testing |

**DeepWork Gap**: No browser automation or design tool integration.

#### 8. Git Worktree Management

The `git-worktree` skill provides isolated parallel development:
- Create worktrees from main
- Automatic .env file copying
- Interactive cleanup

**DeepWork Gap**: No git workflow primitives in job definitions.

#### 9. Language/Framework-Specific Skills

| Skill | Purpose |
|-------|---------|
| `dhh-rails-style` | Rails conventions |
| `dspy-ruby` | DSPy patterns for Ruby |
| `andrew-kane-gem-writer` | Gem writing patterns |
| `frontend-design` | Frontend best practices |

**DeepWork Gap**: No curated library of framework-specific knowledge.

---

### Suggestions for Improving DeepWork

Based on the gaps identified above, here are concrete suggestions for DeepWork improvements:

#### High Priority

1. **Add Agent/Sub-task Support**

   Allow steps to spawn parallel sub-agents with specialized prompts:
   ```yaml
   steps:
     - id: review
       agents:
         - name: simplicity-reviewer
           prompt_file: agents/simplicity.md
           run: parallel
         - name: security-reviewer
           prompt_file: agents/security.md
           run: parallel
   ```

2. **Add Decision Gates**

   Support interactive decision points in workflows:
   ```yaml
   steps:
     - id: plan
       post_actions:
         - type: ask_user
           question: "Plan ready. What next?"
           options:
             - label: "Start work"
               next_step: work
             - label: "Create issue"
               action: gh_issue_create
   ```

3. **Add MCP Server Integration**

   Allow jobs to declare MCP dependencies:
   ```yaml
   mcp_servers:
     - name: context7
       url: https://mcp.context7.com/mcp
       tools:
         - search_docs
         - get_library_info
   ```

#### Medium Priority

4. **Add Auto-Invoke Triggers**

   Support conversation-based step triggering:
   ```yaml
   steps:
     - id: compound
       auto_invoke:
         phrases:
           - "that worked"
           - "it's fixed"
         condition: non_trivial_problem_solved
   ```

5. **Add Script/Template Support**

   Standardize executable scripts and templates in skills:
   ```yaml
   skills:
     git-worktree:
       scripts:
         - name: create
           file: scripts/worktree-manager.sh
           args: ["create", "$branch_name"]
       templates:
         - name: worktree-readme
           file: templates/README.md
   ```

6. **Add Research Phase Support**

   Built-in research capabilities before execution:
   ```yaml
   steps:
     - id: plan
       research:
         - type: codebase
           patterns: ["similar_implementations"]
         - type: external
           condition: "high_risk_topic"
           sources: ["official_docs", "best_practices"]
   ```

#### Lower Priority

7. **Add Framework-Specific Skill Library**

   Curated skills for common frameworks:
   - `library/skills/rails/` - Rails conventions
   - `library/skills/react/` - React patterns
   - `library/skills/python/` - Python best practices

8. **Add Browser/Testing Integration**

   Browser automation primitives:
   ```yaml
   steps:
     - id: e2e_test
       browser:
         - action: navigate
           url: http://localhost:3000
         - action: screenshot
           output: test-results/
   ```

9. **Add Git Workflow Primitives**

   Declarative git operations:
   ```yaml
   steps:
     - id: work
       git:
         - action: create_branch
           from: main
           pattern: "feat/{feature_name}"
         - action: worktree
           condition: parallel_development
   ```

---

### Summary

| Category | Plugin Features | DeepWork Status | Priority |
|----------|----------------|-----------------|----------|
| Core workflow | 4 commands | Implemented | Done |
| Specialized agents | 28 agents | Not supported | High |
| MCP integration | Context7 | Not supported | High |
| Interactive decisions | AskUserQuestion | Not supported | High |
| Auto-invoke | Phrase triggers | Not supported | Medium |
| Scripts/templates | Skill scripts | Partial | Medium |
| Research phase | 5 research agents | Not supported | Medium |
| Browser testing | agent-browser, Playwright | Not supported | Low |
| Framework skills | 15 skills | Not in library | Low |
| Git workflows | Worktree skill | Not supported | Low |

The most impactful improvements would be **agent support** (enabling parallel specialized reviews), **MCP integration** (external knowledge access), and **decision gates** (interactive workflows). These would close the gap for the most commonly used plugin features.

---

## Customization

### Adapting for Your Project

1. **Change documentation paths**: Update `docs/plans/`, `docs/solutions/`, etc. to match your project structure

2. **Add framework-specific guidance**: Extend step instructions with your tech stack conventions

3. **Integrate with issue trackers**: Add `gh issue create` or Linear integration in the plan step

4. **Add custom review perspectives**: Extend the review step with your team's specific concerns

### Required Configuration

Before using, ensure:
- Git repository initialized
- `gh` CLI installed and authenticated (for PR creation)
- `docs/` directory structure created (will be auto-created by steps)
