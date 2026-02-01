# PR Relevance Assessment

**PR**: #197 - Merge jobs into experts workflows
**Branch**: total_shift
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
- .claude/skills/review_pr.check_relevance/SKILL.md
- .claude/skills/review_pr.deep_review/SKILL.md
- .claude/skills/review_pr.improve_and_rereview/SKILL.md
- .claude/skills/review_pr/SKILL.md
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
- .deepwork/experts/experts/learnings/expert_prompts_must_emphasize_domain_focus.md
- .deepwork/experts/experts/learnings/keep_experts_focused.md
- .deepwork/experts/experts/learnings/review_pr_efficiency_improvements.md
- .deepwork/experts/experts/topics/discovery_descriptions.md
- .deepwork/experts/experts/topics/expert_design_patterns.md
- .deepwork/jobs/deepwork_jobs/job.yml
- .deepwork/jobs/deepwork_jobs/steps/define.md
- .deepwork/jobs/deepwork_jobs/steps/implement.md
- .deepwork/jobs/deepwork_jobs/steps/learn.md
- .deepwork/jobs/deepwork_jobs/steps/review_job_spec.md
- .deepwork/jobs/deepwork_rules/steps/define.md
- .deepwork/jobs/review_pr/job.yml
- .deepwork/jobs/review_pr/steps/check_relevance.md
- .deepwork/jobs/review_pr/steps/deep_review.md
- .deepwork/jobs/review_pr/steps/improve_and_rereview.md
- .gemini/skills/deepwork_jobs/define.toml
- .gemini/skills/deepwork_jobs/implement.toml
- .gemini/skills/deepwork_jobs/learn.toml
- .gemini/skills/deepwork_jobs/review_job_spec.toml
- .gemini/skills/deepwork_rules/define.toml
- .gemini/skills/review_pr/check_relevance.toml
- .gemini/skills/review_pr/deep_review.toml
- .gemini/skills/review_pr/improve_and_rereview.toml
- .gemini/skills/review_pr/index.toml
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
- src/deepwork/standard/experts/experts/learnings/expert_prompts_must_emphasize_domain_focus.md
- src/deepwork/standard/experts/experts/learnings/keep_experts_focused.md
- src/deepwork/standard/experts/experts/learnings/review_pr_efficiency_improvements.md
- src/deepwork/standard/experts/experts/topics/discovery_descriptions.md
- src/deepwork/standard/experts/experts/topics/expert_design_patterns.md
- src/deepwork/standard_jobs/deepwork_jobs/job.yml
- src/deepwork/standard_jobs/deepwork_jobs/steps/define.md
- src/deepwork/standard_jobs/deepwork_jobs/steps/implement.md
- src/deepwork/standard_jobs/deepwork_jobs/steps/learn.md
- src/deepwork/standard_jobs/deepwork_jobs/steps/review_job_spec.md
- src/deepwork/standard_jobs/deepwork_rules/steps/define.md
- src/deepwork/standard_jobs/review_pr/job.yml
- src/deepwork/standard_jobs/review_pr/steps/check_relevance.md
- src/deepwork/standard_jobs/review_pr/steps/deep_review.md
- src/deepwork/standard_jobs/review_pr/steps/improve_and_rereview.md
- src/deepwork/templates/claude/agent-expert.md.jinja
- src/deepwork/templates/claude/skill-job-meta.md.jinja
- tests/integration/test_experts_sync.py
- tests/unit/test_expert_schema.py
- tests/unit/test_experts_cli.py
- tests/unit/test_experts_generator.py
- tests/unit/test_experts_parser.py
- uv.lock

## Expert Assessments

### deepwork-rules
**Status**: RELEVANT
**Justification**: This PR modifies the `deepwork_rules.define` step instruction file, which directly governs how file-change rules are created. While the change is minor (updating guidance on how to ask questions), it affects the user experience when defining new rules.
**Relevant files**:
- `src/deepwork/standard_jobs/deepwork_rules/steps/define.md`
- `.claude/skills/deepwork_rules.define/SKILL.md`
- `.claude/skills/deepwork_rules/SKILL.md`
- `.deepwork/jobs/deepwork_rules/steps/define.md`

### experts
**Status**: RELEVANT
**Justification**: This PR directly implements the experts system that is core to this domain. It introduces the expert.yml schema, topics and learnings structure, workflow integration, skill generation from experts, and CLI commands for managing experts - all fundamental concepts of the DeepWork experts framework.
**Relevant files**:
- `src/deepwork/standard/experts/experts/expert.yml`
- `src/deepwork/standard/experts/deepwork_jobs/expert.yml`
- `.deepwork/experts/*/expert.yml`
- `src/deepwork/schemas/expert_schema.py`
- `src/deepwork/standard/experts/experts/topics/*.md`
- `src/deepwork/standard/experts/experts/learnings/*.md`
- `src/deepwork/standard/experts/deepwork_jobs/topics/*.md`
- `src/deepwork/standard/experts/deepwork_jobs/learnings/*.md`
- `src/deepwork/core/experts_parser.py`
- `src/deepwork/core/experts_generator.py`
- `src/deepwork/cli/experts.py`
- `src/deepwork/cli/sync.py`
- `src/deepwork/cli/install.py`
- `src/deepwork/templates/claude/agent-expert.md.jinja`
- `.claude/agents/dwe_experts.md`
- `.claude/agents/dwe_deepwork-jobs.md`
- `.claude/skills/*/SKILL.md`
- `tests/unit/test_expert_schema.py`
- `tests/unit/test_experts_cli.py`
- `tests/unit/test_experts_generator.py`
- `tests/unit/test_experts_parser.py`
- `tests/integration/test_experts_sync.py`
- `doc/experts_requirements.md`
- `doc/architecture.md`

## Summary

**Relevant experts**: deepwork-rules, experts
**Next step**: Run `/experts.deep_review` with these experts
