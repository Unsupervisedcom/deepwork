# PR Relevance Assessment

**PR**: #192 - feat: Add experts system for auto-improving domain knowledge
**Branch**: expert_support
**Date**: 2026-02-01

## Changed Files

- .claude/agents/dwe_deepwork-jobs.md
- .claude/agents/dwe_experts.md
- .claude/settings.json
- .claude/skills/add_platform/SKILL.md
- .claude/skills/commit/SKILL.md
- .claude/skills/deepwork_jobs.define/SKILL.md
- .claude/skills/deepwork_jobs.implement/SKILL.md
- .claude/skills/deepwork_jobs.learn/SKILL.md
- .claude/skills/deepwork_jobs.review_job_spec/SKILL.md
- .claude/skills/deepwork_jobs/SKILL.md
- .claude/skills/deepwork_rules.define/SKILL.md
- .claude/skills/deepwork_rules/SKILL.md
- .claude/skills/manual_tests/SKILL.md
- .claude/skills/update/SKILL.md
- .deepwork/experts/deepwork_jobs/expert.yml
- .deepwork/experts/deepwork_jobs/learnings/.gitkeep
- .deepwork/experts/deepwork_jobs/learnings/prompt_hooks_not_executed.md
- .deepwork/experts/deepwork_jobs/topics/hooks_and_validation.md
- .deepwork/experts/deepwork_jobs/topics/job_yml_schema.md
- .deepwork/experts/deepwork_jobs/topics/skill_generation.md
- .deepwork/experts/deepwork_jobs/topics/step_delegation.md
- .deepwork/experts/deepwork_jobs/topics/step_instructions.md
- .deepwork/experts/experts/expert.yml
- .deepwork/experts/experts/learnings/.gitkeep
- .deepwork/experts/experts/learnings/keep_experts_focused.md
- .deepwork/experts/experts/topics/discovery_descriptions.md
- .deepwork/experts/experts/topics/expert_design_patterns.md
- .deepwork/jobs/deepwork_jobs/job.yml
- .deepwork/jobs/deepwork_jobs/steps/define.md
- .deepwork/jobs/deepwork_jobs/steps/implement.md
- .deepwork/jobs/deepwork_jobs/steps/learn.md
- .deepwork/jobs/deepwork_jobs/steps/review_job_spec.md
- .deepwork/jobs/deepwork_rules/steps/define.md
- .gemini/skills/deepwork_jobs/define.toml
- .gemini/skills/deepwork_jobs/implement.toml
- .gemini/skills/deepwork_jobs/learn.toml
- .gemini/skills/deepwork_jobs/review_job_spec.toml
- .gemini/skills/deepwork_rules/define.toml
- CHANGELOG.md
- README.md
- doc/architecture.md
- doc/experts_requirements.md
- flake.nix
- library/jobs/spec_driven_development/steps/clarify.md
- library/jobs/spec_driven_development/steps/constitution.md
- library/jobs/spec_driven_development/steps/plan.md
- library/jobs/spec_driven_development/steps/specify.md
- pyproject.toml
- src/deepwork/cli/experts.py
- src/deepwork/cli/install.py
- src/deepwork/cli/main.py
- src/deepwork/cli/sync.py
- src/deepwork/core/experts_generator.py
- src/deepwork/core/experts_parser.py
- src/deepwork/schemas/expert_schema.py
- src/deepwork/standard/experts/deepwork_jobs/expert.yml
- src/deepwork/standard/experts/deepwork_jobs/learnings/.gitkeep
- src/deepwork/standard/experts/deepwork_jobs/learnings/prompt_hooks_not_executed.md
- src/deepwork/standard/experts/deepwork_jobs/topics/hooks_and_validation.md
- src/deepwork/standard/experts/deepwork_jobs/topics/job_yml_schema.md
- src/deepwork/standard/experts/deepwork_jobs/topics/skill_generation.md
- src/deepwork/standard/experts/deepwork_jobs/topics/step_delegation.md
- src/deepwork/standard/experts/deepwork_jobs/topics/step_instructions.md
- src/deepwork/standard/experts/experts/expert.yml
- src/deepwork/standard/experts/experts/learnings/.gitkeep
- src/deepwork/standard/experts/experts/learnings/keep_experts_focused.md
- src/deepwork/standard/experts/experts/topics/discovery_descriptions.md
- src/deepwork/standard/experts/experts/topics/expert_design_patterns.md
- src/deepwork/standard_jobs/deepwork_jobs/job.yml
- src/deepwork/standard_jobs/deepwork_jobs/steps/define.md
- src/deepwork/standard_jobs/deepwork_jobs/steps/implement.md
- src/deepwork/standard_jobs/deepwork_jobs/steps/learn.md
- src/deepwork/standard_jobs/deepwork_jobs/steps/review_job_spec.md
- src/deepwork/standard_jobs/deepwork_rules/steps/define.md
- src/deepwork/templates/claude/agent-expert.md.jinja
- src/deepwork/templates/claude/skill-job-meta.md.jinja
- tests/integration/test_experts_sync.py
- tests/unit/test_expert_schema.py
- tests/unit/test_experts_cli.py
- tests/unit/test_experts_generator.py
- tests/unit/test_experts_parser.py
- uv.lock

## Expert Assessments

### deepwork-jobs
**Status**: RELEVANT
**Justification**: This PR directly implements the experts system that integrates with the jobs framework. The changes include the core expert.yml schema, CLI commands, agent generation templates, and standard experts - all of which interact with and extend the existing jobs system.
**Relevant files**:
- `.deepwork/experts/*/expert.yml` - Expert definition files
- `.deepwork/experts/*/topics/*.md` - Topic files
- `.deepwork/experts/*/learnings/*.md` - Learning files
- `src/deepwork/standard/experts/*/` - Standard expert source files
- `src/deepwork/schemas/expert_schema.py` - Expert schema definition
- `src/deepwork/core/experts_parser.py` - Expert parsing logic
- `src/deepwork/core/experts_generator.py` - Agent generation from experts
- `src/deepwork/cli/experts.py` - CLI commands (topics, learnings)
- `src/deepwork/templates/claude/agent-expert.md.jinja` - Agent template
- `doc/experts_requirements.md` - Requirements documentation
- Tests: `tests/unit/test_expert_schema.py`, `tests/unit/test_experts_*.py`, `tests/integration/test_experts_sync.py`

### experts
**Status**: RELEVANT
**Justification**: This PR directly implements the experts system that this expert is documented to be an expert on. The changes add the core experts framework including expert.yml schema, CLI commands, agent generation, and the standard experts - all of which fall squarely within this domain of expertise.
**Relevant files**:
- `src/deepwork/schemas/expert_schema.py` - Expert schema definition
- `src/deepwork/core/experts_parser.py` - Expert parsing logic
- `src/deepwork/core/experts_generator.py` - Agent generation from experts
- `src/deepwork/standard/experts/experts/expert.yml` - Experts expert definition
- `src/deepwork/standard/experts/experts/topics/*.md` - Topic files
- `src/deepwork/standard/experts/experts/learnings/*.md` - Learning files
- `src/deepwork/standard/experts/deepwork_jobs/expert.yml` - DeepWork Jobs expert
- `src/deepwork/standard/experts/deepwork_jobs/topics/*.md` - Topic files
- `src/deepwork/standard/experts/deepwork_jobs/learnings/*.md` - Learning files
- `src/deepwork/cli/experts.py` - CLI commands
- `src/deepwork/cli/main.py` - experts-related changes
- `src/deepwork/cli/install.py` - experts handling
- `src/deepwork/cli/sync.py` - experts sync
- `src/deepwork/templates/claude/agent-expert.md.jinja` - Agent template
- `doc/experts_requirements.md` - Requirements documentation
- `doc/architecture.md` - experts-related sections
- Tests: `tests/unit/test_expert_schema.py`, `tests/unit/test_experts_cli.py`, `tests/unit/test_experts_generator.py`, `tests/unit/test_experts_parser.py`, `tests/integration/test_experts_sync.py`

## Summary

**Relevant experts**: deepwork-jobs, experts
**Next step**: Run `/review_pr.deep_review` with these experts
